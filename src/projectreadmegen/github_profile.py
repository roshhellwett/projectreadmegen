import os
import re
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path

import requests

from projectreadmegen import usagetracker

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN_INFO = """
================================================================
               GitHub Profile README Generator
================================================================

To create the best possible README for your GitHub profile,
we can fetch detailed information about your profile using
the GitHub API.

[bold cyan]What we fetch:[/bold cyan]
- Your profile information (name, bio, company, etc.)
- Your public repositories
- Programming languages you use
- Repository statistics (stars, forks)

[bold yellow]This is optional:[/bold yellow]
If you don't provide a token, we'll use publicly available
information from your GitHub profile URL instead.

[dim]Note: A GitHub token is stored locally and never shared.[/dim]

================================================================
"""


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    pass


class GitHubValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_github_username(username: str) -> Tuple[bool, str]:
    """
    Validate GitHub username format.

    GitHub usernames can only contain:
    - Alphanumeric characters
    - Hyphens (-)
    - Cannot start/end with hyphen
    - Must be between 1-39 characters

    Args:
        username: The username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"

    if len(username) > 39:
        return False, "Username must be 39 characters or less"

    if username.startswith("-") or username.endswith("-"):
        return False, "Username cannot start or end with a hyphen"

    if "--" in username:
        return False, "Username cannot contain consecutive hyphens"

    pattern = r"^[a-zA-Z0-9-]+$"
    if not re.match(pattern, username):
        return False, "Username can only contain letters, numbers, and hyphens"

    return True, ""


def validate_github_url(url: str) -> Tuple[bool, str]:
    """
    Validate GitHub profile URL format.

    Args:
        url: The GitHub profile URL to validate

    Returns:
        Tuple of (is_valid, extracted_username)
    """
    if not url:
        return False, ""

    url = url.strip().rstrip("/")

    if url.startswith("https://github.com/"):
        username = url.replace("https://github.com/", "")
    elif url.startswith("http://github.com/"):
        username = url.replace("http://github.com/", "")
    elif url.startswith("github.com/"):
        username = url.replace("github.com/", "")
    else:
        return False, ""

    username = username.split("/")[0].split("?")[0].split("#")[0]

    if username:
        is_valid, error = validate_github_username(username)
        if is_valid:
            return True, username

    return False, ""


def extract_username_from_url(url: str) -> Optional[str]:
    """
    Extract username from a GitHub profile URL.

    Args:
        url: The GitHub profile URL

    Returns:
        Extracted username or None if invalid
    """
    is_valid, username = validate_github_url(url)
    if is_valid:
        return username
    return None


def fetch_github_user(username: str, token: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch GitHub user profile data.

    Args:
        username: GitHub username
        token: Optional GitHub API token

    Returns:
        Dictionary with user data or None if not found

    Raises:
        GitHubAPIError: If API request fails
    """
    url = f"{GITHUB_API_BASE}/users/{username}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "projectreadmegen",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 404:
            return None
        elif response.status_code == 403:
            raise GitHubAPIError(
                "GitHub API rate limit exceeded. Please try again later "
                "or add a GitHub token for higher rate limits."
            )
        elif not response.ok:
            raise GitHubAPIError(
                f"GitHub API error: {response.status_code} - {response.text}"
            )

        return response.json()

    except requests.exceptions.Timeout:
        raise GitHubAPIError(
            "Request timed out. Please check your internet connection."
        )
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Network error: {str(e)}")


def fetch_user_repos(
    username: str, token: Optional[str] = None, max_repos: int = 30
) -> List[Dict]:
    """
    Fetch user's public repositories.

    Args:
        username: GitHub username
        token: Optional GitHub API token
        max_repos: Maximum number of repositories to fetch

    Returns:
        List of repository dictionaries
    """
    url = f"{GITHUB_API_BASE}/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "projectreadmegen",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    repos = []
    page = 1
    per_page = 100

    try:
        while len(repos) < max_repos:
            params = {
                "sort": "updated",
                "direction": "desc",
                "per_page": min(per_page, max_repos - len(repos)),
                "page": page,
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if not response.ok:
                if response.status_code == 403:
                    logger.warning("Rate limit reached while fetching repos")
                break

            page_repos = response.json()
            if not page_repos:
                break

            for repo in page_repos:
                repos.append(
                    {
                        "name": repo.get("name", ""),
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "stargazers_count": repo.get("stargazers_count", 0),
                        "forks_count": repo.get("forks_count", 0),
                        "topics": repo.get("topics", []),
                        "html_url": repo.get("html_url", ""),
                        "homepage": repo.get("homepage"),
                        "fork": repo.get("fork", False),
                        "archived": repo.get("archived", False),
                        "updated_at": repo.get("updated_at"),
                    }
                )

            page += 1

            if len(page_repos) < per_page:
                break

        repos = [r for r in repos if not r.get("fork") and not r.get("archived")]
        return sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)

    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching repos: {e}")
        return []


def calculate_language_stats(repos: List[Dict]) -> Dict[str, int]:
    """
    Calculate programming language statistics from repositories.

    Args:
        repos: List of repository dictionaries

    Returns:
        Dictionary mapping languages to percentage usage
    """
    language_counts = {}
    total_repos_with_lang = 0

    for repo in repos:
        lang = repo.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1
            total_repos_with_lang += 1

    if total_repos_with_lang == 0:
        return {}

    language_percentages = {}
    for lang, count in sorted(
        language_counts.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = int((count / total_repos_with_lang) * 100)
        language_percentages[lang] = percentage

    return language_percentages


def build_profile_context(
    username: str,
    profile_url: str,
    user_data: Optional[Dict] = None,
    repos: Optional[List[Dict]] = None,
    languages: Optional[Dict[str, int]] = None,
    style: str = "basic",
) -> str:
    """
    Build comprehensive context for AI to generate README.

    Args:
        username: GitHub username
        profile_url: GitHub profile URL
        user_data: User profile data from GitHub API
        repos: List of user repositories
        languages: Language statistics
        style: README style (basic, professional, stylish, unique)

    Returns:
        Formatted context string for AI
    """
    context_parts = []

    context_parts.append(f"# GitHub Profile README Generation")
    context_parts.append(f"Username: {username}")
    context_parts.append(f"Profile URL: {profile_url}")
    context_parts.append(f"Style: {style}")
    context_parts.append("")

    if user_data:
        context_parts.append("## User Profile Information")
        if user_data.get("name"):
            context_parts.append(f"Name: {user_data['name']}")
        if user_data.get("bio"):
            context_parts.append(f"Bio: {user_data['bio']}")
        if user_data.get("company"):
            context_parts.append(f"Company: {user_data['company']}")
        if user_data.get("location"):
            context_parts.append(f"Location: {user_data['location']}")
        if user_data.get("blog"):
            context_parts.append(f"Website: {user_data['blog']}")
        if user_data.get("twitter_username"):
            context_parts.append(f"Twitter: @{user_data['twitter_username']}")
        context_parts.append("")

        context_parts.append("## GitHub Statistics")
        context_parts.append(
            f"- Public Repositories: {user_data.get('public_repos', 'N/A')}"
        )
        context_parts.append(f"- Followers: {user_data.get('followers', 0)}")
        context_parts.append(f"- Following: {user_data.get('following', 0)}")
        if user_data.get("public_gists"):
            context_parts.append(f"- Public Gists: {user_data['public_gists']}")
        if user_data.get("created_at"):
            join_date = user_data["created_at"][:10]
            context_parts.append(f"- Member Since: {join_date}")
        context_parts.append("")
    else:
        context_parts.append("## User Information")
        context_parts.append(f"GitHub Profile: {profile_url}")
        context_parts.append("")

    if languages:
        context_parts.append("## Programming Languages")
        for lang, percentage in list(languages.items())[:10]:
            context_parts.append(f"- {lang}: {percentage}%")
        context_parts.append("")

    if repos:
        context_parts.append("## Notable Repositories")
        top_repos = repos[:10]

        for i, repo in enumerate(top_repos, 1):
            context_parts.append(f"{i}. **{repo['name']}**")
            if repo.get("description"):
                context_parts.append(f"   Description: {repo['description']}")
            stats = []
            if repo.get("stargazers_count", 0) > 0:
                stats.append(f"{repo['stargazers_count']} stars")
            if repo.get("forks_count", 0) > 0:
                stats.append(f"{repo['forks_count']} forks")
            if repo.get("language"):
                stats.append(f"Language: {repo['language']}")
            if stats:
                context_parts.append(f"   Stats: {' | '.join(stats)}")
            if repo.get("topics"):
                context_parts.append(f"   Topics: {', '.join(repo['topics'][:5])}")
            context_parts.append("")

    context_parts.append(f"## README Style Required")
    context_parts.append(
        f"Generate a {style} GitHub profile README based on the information above."
    )
    context_parts.append("")
    context_parts.append(
        "Create a professional, engaging README that highlights the user's personality,"
    )
    context_parts.append("skills, and contributions. Make it unique and memorable.")

    return "\n".join(context_parts)


def get_style_prompt(style: str) -> str:
    """
    Get the system prompt for a specific README style.

    Args:
        style: README style (basic, professional, stylish, unique)

    Returns:
        System prompt for AI
    """
    prompts = {
        "basic": """You are an expert at creating clean, professional GitHub profile READMEs.

Create a basic but polished GitHub profile README that includes:
1. A brief, friendly introduction
2. GitHub stats section (using shields.io badges)
3. Top skills/languages as a simple list
4. Featured repositories section
5. Social links (GitHub, LinkedIn, Twitter, etc.)
6. A simple contact section

Keep it clean, minimal, and easy to maintain. Focus on clarity and professionalism.
Use proper Markdown formatting throughout.

Include these badges at the top:
- GitHub profile badge
- Stats badges (repos, followers, following)

DO NOT include animated elements or complex graphics. Keep it lightweight.
Make sure all links and badges are properly formatted for GitHub Markdown.""",
        "professional": """You are an expert at creating professional GitHub profile READMEs for career-focused developers.

Create a professional GitHub profile README that includes:
1. Professional header with name and title/tagline
2. About Me section with career focus
3. GitHub stats with shields.io badges (repos, stars, followers, following)
4. Top programming languages section
5. Featured/representative repositories (3-5) with descriptions
6. Skills section organized by category
7. Work experience or open source contributions section
8. Education/certifications if relevant
9. Contact information and social links

Make it suitable for job applications and professional networking.
Use a clean, organized layout with clear sections.
Use proper Markdown formatting.

Include shields.io badges for:
- Profile views
- GitHub stats
- Top languages
- Streak (if impressive)

DO NOT include animated elements. Keep it professional and career-focused.""",
        "stylish": """You are an expert at creating visually stunning GitHub profile READMEs with creative elements.

Create a stylish, visually impressive GitHub profile README with:
1. Eye-catching header with animated typing effect (use readme-typing-svg.demolab.com)
2. GitHub Readme Stats cards (github-readme-stats.vercel.app)
3. Top languages visualization card
4. Contribution streak stats
5. Featured projects with cards
6. WakaTime activity section (placeholder if not available)
7. Social media links with icons
8. A fun "visitor counter" or "spotify playing" section

Use these dynamic stats cards:
```
![GitHub Stats](https://github-readme-stats.vercel.app/api?username=USERNAME&theme=dark)
![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=USERNAME&layout=compact)
![Streak](https://github-readme-stats.vercel.app/api/streak/?username=USERNAME&theme=dark)
```

Use typing effect:
```
![Typing SVG](https://readme-typing-svg.demolab.com/?lines=YOUR+TAGLINE+HERE&center=true&width=500)
```

Make it visually impressive but still readable. Balance creativity with functionality.
Use a dark theme option where possible for better visual impact.""",
        "unique": """You are an expert at creating unique, creative GitHub profile READMEs that stand out.

Create a unique, memorable GitHub profile README that showcases personality and creativity:

1. Creative header/banner section
2. Personalized intro that reflects personality
3. Bento grid or creative layout concept
4. All GitHub stats cards (stats, languages, streak, top repos)
5. Detailed skills section with levels or progress indicators
6. Featured projects with rich descriptions
7. Open source contributions highlight
8. Current learning/focus section
9. Fun facts or personal interests
10. Quote or inspiration section
11. All social and contact links
12. Contribution graph reference

Use creative Markdown techniques:
- Emojis strategically (not excessive)
- Custom separators and dividers
- Interesting section headers
- Visual hierarchy with spacing

Include dynamic cards:
```
![Stats](https://github-readme-stats.vercel.app/api?username=USERNAME&theme=radical)
![Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=USERNAME&theme=radical)
![Streak](https://github-readme-stats.vercel.app/api/streak/?username=USERNAME&theme=radical)
```

Make it THE most impressive README viewers have seen. Show creativity!
But ensure it's still maintainable and not overwhelming.""",
    }

    return prompts.get(style, prompts["basic"])


def create_output_folder(username: str, output_path: str) -> Tuple[bool, str]:
    """
    Create output folder for GitHub profile README.

    Args:
        username: GitHub username (will be folder name)
        output_path: Base output directory

    Returns:
        Tuple of (success, folder_path or error_message)
    """
    try:
        base_path = Path(output_path).resolve()
        profile_folder = base_path / username

        if profile_folder.exists() and profile_folder.is_file():
            return False, f"Cannot create folder: {profile_folder} is a file"

        profile_folder.mkdir(parents=True, exist_ok=True)

        return True, str(profile_folder)

    except PermissionError:
        return False, "Permission denied. Check write access to the output directory."
    except Exception as e:
        return False, f"Error creating folder: {str(e)}"


def generate_readme_content(
    username: str,
    profile_url: str,
    style: str,
    user_data: Optional[Dict] = None,
    repos: Optional[List[Dict]] = None,
    languages: Optional[Dict[str, int]] = None,
) -> str:
    """
    Generate GitHub profile README using Grok AI.

    Args:
        username: GitHub username
        profile_url: GitHub profile URL
        style: README style
        user_data: User profile data
        repos: User repositories
        languages: Language statistics

    Returns:
        Generated README content
    """
    from projectreadmegen.grok import GrokClient

    api_key = usagetracker.get_api_key()
    if not api_key:
        raise GitHubValidationError("Groq API key not configured")

    client = GrokClient(api_key=api_key)

    context = build_profile_context(
        username=username,
        profile_url=profile_url,
        user_data=user_data,
        repos=repos,
        languages=languages,
        style=style,
    )

    system_prompt = get_style_prompt(style)

    try:
        readme = client.generate_readme(
            project_context=context,
            system_prompt=system_prompt,
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
        )

        readme = readme.strip()

        if username in readme and "USERNAME" in readme:
            readme = readme.replace("USERNAME", username)

        return readme

    except Exception as e:
        logger.error(f"Error generating README: {e}")
        raise GitHubAPIError(f"Failed to generate README: {str(e)}")


def save_github_readme(
    content: str, folder_path: str, username: str
) -> Tuple[bool, str]:
    """
    Save generated README to file.

    Args:
        content: README content
        folder_path: Folder to save in
        username: Username for filename

    Returns:
        Tuple of (success, file_path or error_message)
    """
    try:
        readme_path = Path(folder_path) / "README.md"

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, str(readme_path)

    except PermissionError:
        return False, "Permission denied. Cannot write to the folder."
    except Exception as e:
        return False, f"Error saving README: {str(e)}"


def check_readme_exists(folder_path: str) -> Tuple[bool, str]:
    """
    Check if README.md already exists in folder.

    Args:
        folder_path: Path to check

    Returns:
        Tuple of (exists, file_path)
    """
    readme_path = Path(folder_path) / "README.md"
    exists = readme_path.exists()
    return exists, str(readme_path)


def read_existing_readme(folder_path: str) -> Optional[str]:
    """
    Read existing README content.

    Args:
        folder_path: Path to folder with README

    Returns:
        README content or None
    """
    readme_path = Path(folder_path) / "README.md"

    if readme_path.exists():
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass

    return None

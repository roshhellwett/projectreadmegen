import os
import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

USAGE_FILE = "+projectreadmegen_usage.json"
DEFAULT_API_KEY = None

GROQ_KEY_INFO = """
================================================================
                    Groq API Key Setup
================================================================

A Groq API key is required to use AI-powered features.

Steps to get your free API key:
1. Visit: https://console.groq.com/keys
2. Click "Create Key" button
3. Copy the generated key
4. Paste it below

Your key will be securely stored on your device.

================================================================
"""

GITHUB_TOKEN_INFO = """
================================================================
               GitHub API Token (Optional)
================================================================

A GitHub API token allows us to fetch more detailed information
about your GitHub profile, including:
- All your repositories
- Programming languages used
- More accurate statistics

To create a token:
1. Visit: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: "read:user" and "public_repo"
4. Copy and paste the token below

This is optional but recommended for best results.

================================================================
"""

CACHE_FILE = "+projectreadmegen_cache.json"


def get_usage_file_path():
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "projectreadmegen" / USAGE_FILE
    return Path.home() / USAGE_FILE


def get_cache_file_path():
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "projectreadmegen" / CACHE_FILE
    return Path.home() / CACHE_FILE


def load_usage_data():
    path = get_usage_file_path()
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {"user_key_set": False, "github_token_set": False}
    return {"user_key_set": False, "github_token_set": False}


def save_usage_data(data):
    path = get_usage_file_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Could not save usage data: {e}")


def load_project_cache(project_path):
    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())

    if path.exists():
        try:
            with open(path, "r") as f:
                cache = json.load(f)
                return cache.get(cache_key, {})
        except Exception:
            return {}
    return {}


def save_project_cache(project_path, data):
    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())

    try:
        cache = {}
        if path.exists():
            with open(path, "r") as f:
                cache = json.load(f)

        cache[cache_key] = {
            "last_template": data.get("template", "standard"),
            "last_used": str(date.today()),
            "path": cache_key,
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Could not save cache: {e}")


def check_api_key():
    """Check if Groq API key is configured."""
    api_key = get_api_key()
    if api_key:
        return True
    return False


def check_free_limit():
    """Check if API is available. Now requires user's own API key."""
    api_key = get_api_key()
    if api_key:
        return True, "Using your own API key"
    return False, "API key required"


def require_api_key():
    """Prompt user to set up API key when none is configured."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print(
        Panel(
            """
[bold red]API Key Required![/bold red]

To use AI-powered features, you need to set up your own Groq API key.

[bold yellow]How to get your free API key:[/bold yellow]

1. Visit: [link]https://console.groq.com/keys[/link]
2. Click "Create Key" button
3. Copy the generated key
4. Return here and paste it

[dim]This is a one-time setup. Your key will be stored securely.[/dim]
        """,
            title="Setup Required",
            border_style="red",
        )
    )

    key = input("\nPaste your Groq API key here: ").strip()

    if key and key.startswith("gsk_"):
        os.environ["GROQ_API_KEY"] = key
        data = load_usage_data()
        data["user_key_set"] = True
        save_usage_data(data)
        console.print("\n[green]API key saved successfully![/green]")
        console.print("[dim]You can now use AI-powered features unlimited times.[/dim]")
        input("\nPress Enter to continue...")
        return True
    elif key:
        console.print("\n[red]Invalid key format![/red]")
        console.print("[yellow]Key should start with 'gsk_'[/yellow]")
        input("\nPress Enter to continue...")

    return False


def handle_exhausted():
    """Redirect to API key setup (kept for backward compatibility)."""
    return require_api_key()


def show_key_setup():
    """Show key setup prompt if API key is not configured."""
    if check_api_key():
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print(
        Panel(
            """
[bold yellow]Setup Your Groq API Key[/bold yellow]

To use AI-powered features, you need your own Groq API key.

[bold]Get your free key:[/bold]
1. Visit: https://console.groq.com/keys
2. Create a new key
3. Copy and paste below

[dim]This is a one-time setup.[/dim]
        """,
            title="API Key Required",
            border_style="yellow",
        )
    )

    key = input("\nPaste your Groq API key (or press Enter to skip): ").strip()

    if key and key.startswith("gsk_"):
        os.environ["GROQ_API_KEY"] = key
        data = load_usage_data()
        data["user_key_set"] = True
        save_usage_data(data)
        console.print("\n[green]API key configured![/green]")
    else:
        console.print("\n[dim]Skipped. You can add your key later from the menu.[/dim]")


def get_api_key():
    """Get Groq API key from environment or return None."""
    user_key = os.environ.get("GROQ_API_KEY") or os.environ.get("groq_api_key")
    if user_key:
        return user_key
    if DEFAULT_API_KEY:
        return DEFAULT_API_KEY
    return None


def save_github_token(token: str):
    """Save GitHub token to usage data file."""
    data = load_usage_data()
    data["github_token"] = token
    data["github_token_set"] = True
    save_usage_data(data)
    logger.info("GitHub token saved successfully")


def get_github_token():
    """Get stored GitHub token from usage data file."""
    data = load_usage_data()
    return data.get("github_token", "")


def has_github_token():
    """Check if GitHub token is stored."""
    data = load_usage_data()
    return bool(data.get("github_token", ""))


def clear_github_token():
    """Remove stored GitHub token."""
    data = load_usage_data()
    if "github_token" in data:
        del data["github_token"]
    data["github_token_set"] = False
    save_usage_data(data)


def prompt_github_token():
    """Prompt user for GitHub token if not already set."""
    from rich.console import Console
    from rich.panel import Panel

    if has_github_token():
        return get_github_token()

    console = Console()

    console.print(
        Panel(
            """
[bold cyan]GitHub API Token (Optional)[/bold cyan]

Adding a GitHub token helps us fetch more detailed information
about your profile for better README generation.

[bold green]Benefits:[/bold green]
- Access all your repositories
- See your programming language stats
- Get accurate follower/following counts
- Fetch repository descriptions and topics

[bold yellow]How to create a token:[/bold yellow]
1. Visit: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select: [green]read:user[/green] and [green]public_repo[/green]
4. Copy and paste below

[dim]Press Enter to skip (basic info will be used instead)[/dim]
        """,
            title="GitHub Token",
            border_style="cyan",
        )
    )

    token = input("\nPaste GitHub token (or press Enter to skip): ").strip()

    if token:
        save_github_token(token)
        console.print("\n[green]GitHub token saved![/green]")
        return token

    console.print("\n[dim]Skipped. Using basic profile information.[/dim]")
    return ""


def get_remaining_credits():
    """Get status message for remaining credits/API key status."""
    api_key = get_api_key()

    if api_key:
        return "[dim]Using your own API key | Powered by Zenith Open Source Projects | Developer - roshhellwett[/dim]"

    return "[red]API Key Required[/red] | Powered by Zenith Open Source Projects"


def get_project_last_template(project_path):
    """Get last used template for a project from cache."""
    cache = load_project_cache(project_path)
    return cache.get("last_template", "standard")


def get_project_readme_info(project_path):
    """Get README modification time from project cache."""
    cache = load_project_cache(project_path)
    project_data = cache.get(str(Path(project_path).resolve()), {})
    return {
        "last_readme_mtime": project_data.get("last_readme_mtime"),
        "last_readme_hash": project_data.get("last_readme_hash"),
        "last_generate_time": project_data.get("last_generate_time"),
    }


def save_project_readme_info(project_path, readme_path):
    """Save README info for smart update detection."""
    import time

    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())

    try:
        cache = {}
        if path.exists():
            with open(path, "r") as f:
                cache = json.load(f)

        readme_mtime = 0
        readme_hash = ""
        if Path(readme_path).exists():
            stat = Path(readme_path).stat()
            readme_mtime = stat.st_mtime
            with open(readme_path, "rb") as f:
                import hashlib

                readme_hash = hashlib.md5(f.read()).hexdigest()[:16]

        if cache_key not in cache:
            cache[cache_key] = {}

        cache[cache_key].update(
            {
                "last_readme_mtime": readme_mtime,
                "last_readme_hash": readme_hash,
                "last_generate_time": time.time(),
                "path": cache_key,
            }
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Could not save README info: {e}")

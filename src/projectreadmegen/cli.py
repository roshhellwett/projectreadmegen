# cli.py

import os
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from projectreadmegen.scanner import scan_directory, load_config
from projectreadmegen.detector import detect_stack
from projectreadmegen.generator import generate_readme, save_readme
from projectreadmegen import __version__
from projectreadmegen import grok
from projectreadmegen import usagetracker
from projectreadmegen import github_profile

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="projectreadmegen — Auto-generate README files from folder structure.",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()


def print_version():
    console.print(f"""
[bold cyan]projectreadmegen[/bold cyan] version {__version__}

[dim]Auto-generate README files with AI power[/dim]

[green]Powered by Zenith Open Source Projects | Developer - roshhellwett[/green]
    """)
    raise typer.Exit(code=0)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
):
    if version:
        print_version()
    if ctx.invoked_subcommand is None:
        main_menu_loop()


def show_main_menu():
    console.clear()
    console.print(
        Panel(
            """
[bold cyan]Welcome to projectreadmegen[/bold cyan]
[dim]Auto-generate README files with AI power[/dim]

[bold yellow]Select an option:[/bold yellow]

  [green]1[/green]  Create README with AI
  [green]2[/green]  Create Normal README (template-based)
  [green]3[/green]  Manage API Key
  [green]4[/green]  View Credits Status
  [green]5[/green]  Update projectreadmegen
  [green]6[/green]  Help & Commands
  [green]7[/green]  Create GitHub Profile README  [NEW]
  [green]8[/green]  Exit
        """,
            title="projectreadmegen Menu",
            border_style="cyan",
        )
    )
    choice = input("\nEnter your choice (1-8): ").strip()
    return choice


def handle_create_ai():
    console.print("\n[bold]Select mode:[/bold]")
    console.print("  [green]1[/green]  Generate (quick mode)")
    console.print("  [green]2[/green]  Interactive (answer questions)")

    mode = input("\nEnter mode (1/2): ").strip()

    path = input("\nEnter project path (default: .): ").strip() or "."

    if mode == "2":
        handle_interactive_mode(ai=True, path=path)
    else:
        handle_generate_mode(ai=True, path=path)


def handle_create_normal():
    console.print("\n[bold]Select mode:[/bold]")
    console.print("  [green]1[/green]  Generate (quick mode)")
    console.print("  [green]2[/green]  Interactive (answer questions)")

    mode = input("\nEnter mode (1/2): ").strip()

    path = input("\nEnter project path (default: .): ").strip() or "."

    if mode == "2":
        handle_interactive_mode(ai=False, path=path)
    else:
        handle_generate_mode(ai=False, path=path)


def handle_manage_api():
    user_key = os.environ.get("GROQ_API_KEY")
    has_key = bool(user_key)

    if has_key:
        console.print("""
[bold yellow]Current Status:[/bold yellow]
  You have your own API key configured.

[bold]Options:[/bold]
  [green]1[/green]  Update API Key (replace current)
  [green]2[/green]  Remove API Key
  [green]3[/green]  Manage GitHub Token (for GitHub Profile README)
  [green]4[/green]  Go Back
        """)
    else:
        console.print("""
[bold yellow]Current Status:[/bold yellow]
  No API key configured. AI features require an API key.

[bold]Options:[/bold]
  [green]1[/green]  Add Your Own API Key
  [green]2[/green]  Manage GitHub Token (for GitHub Profile README)
  [green]3[/green]  Go Back
        """)

    choice = input("\nEnter choice: ").strip()

    if has_key and choice == "1":
        key = input("\nEnter your new Groq API key: ").strip()
        if not key:
            console.print("[yellow]No key provided. Cancelled.[/yellow]")
        elif key.startswith("gsk_") and len(key) > 10:
            os.environ["GROQ_API_KEY"] = key
            data = usagetracker.load_usage_data()
            data["user_key_set"] = True
            usagetracker.save_usage_data(data)
            console.print("[green]✓ API key updated successfully![/green]")
        else:
            console.print("[red]✗ Invalid key format. Key should start with 'gsk_' and be longer.[/red]")
            console.print("[dim]Get your key at: https://console.groq.com/keys[/dim]")
        input("\nPress Enter to continue...")
    elif has_key and choice == "2":
        del os.environ["GROQ_API_KEY"]
        data = usagetracker.load_usage_data()
        data["user_key_set"] = False
        usagetracker.save_usage_data(data)
        console.print("[green]API key removed.[/green]")
        input("\nPress Enter to continue...")
    elif has_key and choice == "3":
        handle_github_token_settings()
    elif not has_key and choice == "1":
        console.print("""
[bold]Get your free API key:[/bold]
1. Visit: https://console.groq.com/keys
2. Click "Create Key"
3. Copy the key and paste below
        """)
        key = input("\nEnter your Groq API key: ").strip()
        if not key:
            console.print("[yellow]No key provided. Cancelled.[/yellow]")
        elif key.startswith("gsk_") and len(key) > 10:
            os.environ["GROQ_API_KEY"] = key
            data = usagetracker.load_usage_data()
            data["user_key_set"] = True
            usagetracker.save_usage_data(data)
            console.print("[green]✓ API key added successfully![/green]")
        else:
            console.print("[red]✗ Invalid key format. Key should start with 'gsk_' and be longer.[/red]")
        input("\nPress Enter to continue...")
    elif not has_key and choice == "2":
        handle_github_token_settings()
    elif (has_key and choice == "4") or (not has_key and choice == "3"):
        return


def handle_credits_status():
    msg = usagetracker.get_remaining_credits()
    data = usagetracker.load_usage_data()

    user_key = os.environ.get("GROQ_API_KEY")
    has_key = bool(user_key) or data.get("user_key_set")
    has_github_token = usagetracker.has_github_token()

    console.print(f"""
[bold yellow]Credits Status:[/bold yellow]

  Groq API Key: {"[green]Configured[/green]" if has_key else "[red]Not configured[/red]"}
  GitHub Token: {"[green]Configured[/green]" if has_github_token else "[dim]Not configured[/dim]"}

  {msg}

[bold]Details:[/bold]
  - Groq API key required for AI features
  - GitHub token optional for better GitHub Profile README
    """)
    input("\nPress Enter to continue...")


def handle_help():
    console.print("""
[bold cyan]Help & Commands[/bold cyan]

[bold yellow]Quick Commands:[/bold yellow]
  python -m projectreadmegen generate .         Normal README
  python -m projectreadmegen generate . --ai   AI-powered README
  python -m projectreadmegen generate . -a     Short flag for --ai
  python -m projectreadmegen interactive .     Interactive mode
  python -m projectreadmegen interactive . --ai Interactive + AI
  python -m projectreadmegen --help            Show all options

[bold yellow]Options:[/bold yellow]
  --ai, -a, --grok     Use Grok AI for enhanced README
  --force, -f          Overwrite existing README
  --dry-run            Preview without saving
  --template, -t        Choose template (minimal/standard/full/academic)
  --depth, -d          Folder tree depth (default: 3)
  --no-badges          Disable badge generation

[bold yellow]API Key:[/bold yellow]
  Get free key at: https://console.groq.com/keys
  Set via: $env:GROQ_API_KEY="your_key"

[dim]Press Ctrl+C to exit anytime[/dim]
    """)
    input("\nPress Enter to continue...")


def handle_github_token_settings():
    """Manage GitHub API token settings."""
    has_token = usagetracker.has_github_token()
    current_token = usagetracker.get_github_token()

    if has_token and current_token:
        masked_token = (
            current_token[:8] + "..." + current_token[-4:]
            if len(current_token) > 12
            else "***"
        )
    else:
        masked_token = None

    console.print(f"""
[bold cyan]GitHub Token Settings[/bold cyan]

[bold yellow]Current Status:[/bold yellow]
  {"[green]Configured[/green]" if has_token else "[dim]Not configured[/dim]"}
  {"Token: " + masked_token if masked_token else ""}

[bold yellow]What is a GitHub Token?[/bold yellow]
  A GitHub token helps us fetch more detailed information
  about your profile for creating better GitHub Profile READMEs.

  Benefits:
  - Access all your repositories
  - See programming language statistics
  - Get accurate follower counts
  - Fetch repository descriptions

[bold yellow]Options:[/bold yellow]
  [green]1[/green]  {"Update" if has_token else "Add"} GitHub Token
  [green]2[/green]  Remove Token {"(already not set)" if not has_token else ""}
  [green]3[/green]  Go Back
    """)

    choice = input("\nEnter choice: ").strip()

    if choice == "1":
        console.print("""
[bold]Create a GitHub Token:[/bold]
1. Visit: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: [green]read:user[/green] and [green]public_repo[/green]
4. Click "Generate token"
5. Copy and paste below
        """)
        token = input("\nPaste GitHub token (or press Enter to cancel): ").strip()
        if token:
            usagetracker.save_github_token(token)
            console.print("[green]GitHub token saved![/green]")
        else:
            console.print("[dim]Cancelled.[/dim]")
        input("\nPress Enter to continue...")
    elif choice == "2" and has_token:
        usagetracker.clear_github_token()
        console.print("[green]GitHub token removed.[/green]")
        input("\nPress Enter to continue...")
    elif choice == "3":
        return


def handle_github_profile():
    """Handle GitHub Profile README generation."""
    if not usagetracker.check_api_key():
        console.print(
            Panel(
                """
[bold red]API Key Required[/bold red]

To create a GitHub Profile README, you need to set up your Groq API key first.

[bold yellow]Get your free API key:[/bold yellow]
1. Visit: https://console.groq.com/keys
2. Create a new key
3. Copy and paste below
            """,
                title="Setup Required",
                border_style="red",
            )
        )

        key = input("\nPaste your Groq API key: ").strip()
        if key and key.startswith("gsk_"):
            os.environ["GROQ_API_KEY"] = key
            data = usagetracker.load_usage_data()
            data["user_key_set"] = True
            usagetracker.save_usage_data(data)
            console.print("[green]API key saved![/green]\n")
        else:
            console.print("[red]Invalid key format. Cancelling.[/red]")
            input("\nPress Enter to continue...")
            return

    console.print(
        Panel(
            """
[bold cyan]GitHub Profile README Generator[/bold cyan]

Create a professional README for your GitHub profile!

[bold yellow]Features:[/bold yellow]
- AI-powered personalized content
- Multiple style options (Basic, Professional, Stylish, Unique)
- Automatic repository and language detection
- Beautiful badges and stats cards

[bold]Let's get started...[/bold]
        """,
            title="GitHub Profile README",
            border_style="cyan",
        )
    )

    username = input("\nEnter your GitHub username: ").strip()
    if not username:
        console.print("[red]Username cannot be empty.[/red]")
        input("\nPress Enter to continue...")
        return

    is_valid, error = github_profile.validate_github_username(username)
    if not is_valid:
        console.print(f"[red]Invalid username: {error}[/red]")
        input("\nPress Enter to continue...")
        return

    profile_url = input(
        "Enter your GitHub profile URL (e.g., https://github.com/" + username + "): "
    ).strip()
    if not profile_url:
        profile_url = f"https://github.com/{username}"

    console.print("""
[bold cyan]Select Style:[/bold yellow]

  [green]1[/green]  Basic README
      Clean, simple, and professional

  [green]2[/green]  Professional README
      Career-focused with detailed sections

  [green]3[/green]  Stylish with Badges
      Visually impressive with stats cards

  [green]4[/green]  Unique & Creative
      Most detailed and eye-catching
    """)

    style_choice = input("\nEnter style (1-4, default: 2): ").strip() or "2"

    style_map = {"1": "basic", "2": "professional", "3": "stylish", "4": "unique"}
    style = style_map.get(style_choice, "professional")

    output_path = (
        input("\nEnter output path (default: current directory): ").strip() or "."
    )

    success, folder_path = github_profile.create_output_folder(username, output_path)
    if not success:
        console.print(f"[red]Error: {folder_path}[/red]")
        input("\nPress Enter to continue...")
        return

    exists, readme_path = github_profile.check_readme_exists(folder_path)
    if exists:
        console.print(
            f"\n[yellow]Warning: README.md already exists in {folder_path}[/yellow]"
        )
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            console.print("[dim]Cancelled.[/dim]")
            input("\nPress Enter to continue...")
            return

    github_token = (
        usagetracker.get_github_token() if usagetracker.has_github_token() else None
    )

    if not github_token:
        console.print("""
[bold cyan]GitHub Token (Optional)[/bold cyan]

A GitHub token allows us to fetch detailed information about your profile
for a more personalized README. This is recommended but optional.

[bold]Benefits:[/bold]
- Access all your repositories
- See your programming languages
- Get accurate stats

[bold]Press Enter to skip[/bold] or type [green]y[/green] to add a token now:""")
        add_token = input().strip().lower()
        if add_token == "y":
            console.print("""
1. Visit: https://github.com/settings/tokens
2. Create token with [green]read:user[/green] scope
3. Paste below
            """)
            token = input("GitHub token: ").strip()
            if token:
                github_token = token
                usagetracker.save_github_token(token)
                console.print("[green]Token saved![/green]\n")

    console.print("\n[bold cyan]Fetching GitHub profile data...[/bold cyan]")

    user_data = None
    repos = []
    languages = {}

    try:
        user_data = github_profile.fetch_github_user(username, github_token)
        if not user_data:
            console.print(
                f"[yellow]Could not fetch profile data for @{username}[/yellow]"
            )
            console.print("[dim]Will proceed with profile URL only.[/dim]\n")
    except Exception as e:
        console.print(f"[yellow]Could not fetch profile: {str(e)}[/yellow]")
        console.print("[dim]Proceeding with limited information...[/dim]\n")

    if user_data:
        try:
            repos = github_profile.fetch_user_repos(username, github_token)
            languages = github_profile.calculate_language_stats(repos)
        except Exception as e:
            console.print(f"[yellow]Could not fetch repositories: {str(e)}[/yellow]")

    console.print(f"[green]Found {len(repos)} repositories[/green]")
    if languages:
        top_langs = list(languages.items())[:5]
        console.print(
            f"[green]Top languages: {', '.join([lang[0] for lang in top_langs])}[/green]\n"
        )

    console.print(f"[bold cyan]Generating {style} README...[/bold cyan]\n")

    try:
        readme_content = github_profile.generate_readme_content(
            username=username,
            profile_url=profile_url,
            style=style,
            user_data=user_data,
            repos=repos,
            languages=languages,
        )

        success, result = github_profile.save_github_readme(
            readme_content, folder_path, username
        )

        if success:
            console.print(
                Panel(
                    f"""
[bold green]GitHub Profile README Created Successfully![/bold green]

  Username  : @{username}
  Style     : {style.capitalize()}
  Location  : {result}

[bold yellow]Next Steps:[/bold yellow]
1. Copy the README.md to your GitHub profile repository
2. The repository should be named: {username}
3. Push to GitHub and see your new profile!

[dim]Find your profile at: {profile_url}[/dim]
                """,
                    title="Success!",
                    border_style="green",
                )
            )
        else:
            console.print(f"[red]Error saving README: {result}[/red]")

    except Exception as e:
        console.print(f"[red]Error generating README: {str(e)}[/red]")
        console.print("[yellow]Please try again or check your API key.[/yellow]")

    input("\nPress Enter to continue...")


def handle_update():
    import subprocess

    console.print("\n[bold cyan]Checking for updates...[/bold cyan]\n")

    try:
        # Get current installed version
        current_result = subprocess.run(
            ["pip", "show", "projectreadmegen"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        current_version = "Unknown"
        for line in current_result.stdout.split("\n"):
            if line.startswith("Version:"):
                current_version = line.replace("Version:", "").strip()
                break

        # Get latest version from pip index (returns versions newest-first)
        result = subprocess.run(
            ["pip", "index", "versions", "projectreadmegen"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        latest_version = "Unknown"
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "Available versions:" in line:
                    # First version in the list is the latest
                    versions = (
                        line.replace("Available versions:", "").strip().split(", ")
                    )
                    if versions and versions[0]:
                        latest_version = versions[0].strip()
                    break
        else:
            # Fallback: try pip install --upgrade --dry-run
            console.print(f"  Current installed: [yellow]{current_version}[/yellow]")
            console.print("[dim]Checking PyPI for latest version...[/dim]")
            dry_result = subprocess.run(
                ["pip", "install", "--upgrade", "--dry-run", "projectreadmegen"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if (
                dry_result.returncode == 0
                and "would be upgraded" in dry_result.stdout.lower()
            ):
                console.print("[bold yellow]A new version is available![/bold yellow]")
                console.print("  Updating now...\n")

                update_result = subprocess.run(
                    ["pip", "install", "--upgrade", "projectreadmegen"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if update_result.returncode == 0:
                    console.print("[green]Update successful![/green]\n")

                    new_result = subprocess.run(
                        ["pip", "show", "projectreadmegen"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    for line in new_result.stdout.split("\n"):
                        if line.startswith("Version:"):
                            new_version = line.replace("Version:", "").strip()
                            console.print(
                                f"  Updated to: [green]{new_version}[/green]\n"
                            )
                            break
                else:
                    console.print(f"[red]Update failed: {update_result.stderr}[/red]\n")
            else:
                console.print("[green]You are on the latest version![/green]\n")

            input("Press Enter to continue...")
            return

        console.print(f"  Current installed: [yellow]{current_version}[/yellow]")
        console.print(f"  Latest on PyPI:  [green]{latest_version}[/green]\n")

        if current_version != latest_version and latest_version != "Unknown":
            console.print("[bold yellow]A new version is available![/bold yellow]")
            console.print("  Updating now...\n")

            update_result = subprocess.run(
                ["pip", "install", "--upgrade", "projectreadmegen"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if update_result.returncode == 0:
                console.print("[green]Update successful![/green]\n")

                new_result = subprocess.run(
                    ["pip", "show", "projectreadmegen"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                for line in new_result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        new_version = line.replace("Version:", "").strip()
                        console.print(f"  Updated to: [green]{new_version}[/green]\n")
                        break
            else:
                console.print(f"[red]Update failed: {update_result.stderr}[/red]\n")
        else:
            console.print("[green]You are on the latest version![/green]\n")

    except Exception as e:
        console.print(f"[red]Error checking for updates: {e}[/red]\n")

    input("Press Enter to continue...")


def handle_generate_mode(ai=False, path="."):
    try:
        root = Path(path).resolve()

        # Validate path
        if not root.exists():
            console.print(f"[red]✗ Error: Path '{path}' does not exist.[/red]")
            console.print("[dim]  Please check the path and try again.[/dim]")
            input("\nPress Enter to continue...")
            return

        if not root.is_dir():
            console.print(f"[red]✗ Error: '{path}' is not a directory.[/red]")
            console.print("[dim]  Please provide a directory path, not a file.[/dim]")
            input("\nPress Enter to continue...")
            return

        # Try to read directory
        try:
            list(root.iterdir())
        except PermissionError:
            console.print(f"[red]✗ Error: No permission to access '{path}'.[/red]")
            console.print("[dim]  Please check folder permissions.[/dim]")
            input("\nPress Enter to continue...")
            return

        # Load configuration
        try:
            config = load_config(str(root))
        except Exception as e:
            from projectreadmegen.exceptions import ProjectReadmeGenException
            if isinstance(e, ProjectReadmeGenException):
                console.print("[red]✗ Configuration Error:[/red]")
                console.print(f"[yellow]  {e.user_message}[/yellow]")
            else:
                console.print(f"[red]✗ Configuration Error: {e}[/red]")
            input("\nPress Enter to continue...")
            return

        # Check API key if needed
        if ai:
            if not usagetracker.check_api_key():
                can_continue = usagetracker.require_api_key()
                if not can_continue:
                    return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            try:
                # Scan project
                task = progress.add_task("Scanning project...", total=None)
                try:
                    scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                except Exception as e:
                    from projectreadmegen.exceptions import ProjectReadmeGenException
                    if isinstance(e, ProjectReadmeGenException):
                        console.print(f"[red]✗ Scan Error: {e.user_message}[/red]")
                    else:
                        console.print(f"[red]✗ Failed to scan directory: {e}[/red]")
                    input("\nPress Enter to continue...")
                    return

                # Detect stack
                progress.update(task, description="Detecting stack...")
                detection = detect_stack(scan)

                # Generate README
                if ai:
                    progress.update(task, description="Generating README with AI...")
                    try:
                        readme = grok.generate_ai_readme(scan, detection, config)
                        console.print("[green]✓ AI generation successful![/green]")
                    except Exception as ai_error:
                        from projectreadmegen.exceptions import APIError as CustomAPIError
                        if isinstance(ai_error, CustomAPIError):
                            progress.stop()
                            console.print(f"[yellow]⚠ {ai_error.user_message}[/yellow]")
                            console.print("[dim]Falling back to template-based generation...[/dim]")
                        else:
                            logger.error(f"AI generation error: {ai_error}")
                            progress.stop()
                            console.print(
                                "[yellow]⚠ AI generation unavailable. Falling back to template-based generation.[/yellow]"
                            )
                        readme = generate_readme(scan, detection, config)
                        progress = Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            transient=True,
                            console=console,
                        )
                        progress.start()
                        task = progress.add_task("Finishing...", total=None)
                else:
                    progress.update(task, description="Generating README...")
                    readme = generate_readme(scan, detection, config)

                # Save README
                progress.update(task, description="Saving README...")
                try:
                    output_path = root / config["output_file"]
                    save_readme(readme, str(output_path))
                except Exception as save_error:
                    from projectreadmegen.exceptions import ProjectReadmeGenException
                    progress.stop()
                    if isinstance(save_error, ProjectReadmeGenException):
                        console.print(f"[red]✗ Save Error: {save_error.user_message}[/red]")
                    else:
                        console.print(f"[red]✗ Failed to save README: {save_error}[/red]")
                    input("\nPress Enter to continue...")
                    return

                progress.stop()

            except Exception as e:
                console.print(f"[red]✗ Unexpected error: {e}[/red]")
                logger.error(f"Unexpected error in generate mode: {e}", exc_info=True)
                input("\nPress Enter to continue...")
                return

        credits_msg = usagetracker.get_remaining_credits()

        console.print(
            Panel(
                f"[green]✓ README generated successfully![/green]\n\n"
                f"  Project  : [bold]{scan['name']}[/bold]\n"
                f"  Language : [bold]{detection['primary_lang']}[/bold]\n"
                f"  Type     : [bold]{detection['project_type']}[/bold]\n"
                f"  Mode     : [bold]{'AI' if ai else 'Template'}[/bold]\n"
                f"  Saved to : [bold]{output_path}[/bold]\n\n"
                f"{credits_msg}",
                title="projectreadmegen",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
    except Exception as e:
        logger.error(f"Unexpected error in handle_generate_mode: {e}", exc_info=True)
        console.print(f"[red]✗ Error: {e}[/red]")

    input("\nPress Enter to continue...")



def handle_interactive_mode(ai=False, path="."):
    try:
        root = Path(path).resolve()

        # Validate path
        if not root.exists():
            console.print(f"[red]✗ Error: Path '{path}' does not exist.[/red]")
            console.print("[dim]  Please check the path and try again.[/dim]")
            input("\nPress Enter to continue...")
            return

        if not root.is_dir():
            console.print(f"[red]✗ Error: '{path}' is not a directory.[/red]")
            input("\nPress Enter to continue...")
            return

        # Load configuration
        try:
            config = load_config(str(root))
        except Exception as e:
            from projectreadmegen.exceptions import ProjectReadmeGenException
            if isinstance(e, ProjectReadmeGenException):
                console.print("[red]✗ Configuration Error:[/red]")
                console.print(f"[yellow]  {e.user_message}[/yellow]")
            else:
                console.print(f"[red]✗ Configuration Error: {e}[/red]")
            input("\nPress Enter to continue...")
            return

        if ai:
            if not usagetracker.check_api_key():
                can_continue = usagetracker.require_api_key()
                if not can_continue:
                    return

            console.print("\n[yellow]Generating AI-powered README...[/yellow]")
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = grok.generate_ai_readme(scan, detection, config)
            except Exception as ai_error:
                from projectreadmegen.exceptions import ProjectReadmeGenException
                if isinstance(ai_error, ProjectReadmeGenException):
                    console.print(f"[yellow]⚠ {ai_error.user_message}[/yellow]")
                else:
                    logger.error(f"AI generation error: {ai_error}")
                    console.print(f"[yellow]⚠ AI generation unavailable. {str(ai_error)[:100]}[/yellow]")
                console.print("[dim]Falling back to template-based generation...[/dim]")
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
        else:
            console.print("\n[bold cyan]Interactive Mode[/bold cyan]\n")

            # Collect user input with validation
            author = input("Your name (optional): ").strip()
            if author:
                config["author"] = author

            github_user = input("Your GitHub username (optional): ").strip()
            if github_user:
                if len(github_user) < 1 or len(github_user) > 39:
                    console.print("[yellow]⚠ GitHub username should be 1-39 characters. Skipping.[/yellow]")
                else:
                    config["github_username"] = github_user

            template = (
                input(
                    "Template [minimal/standard/full/academic] (default: standard): "
                ).strip()
                or "standard"
            ).lower()

            # Validate template
            valid_templates = ["minimal", "standard", "full", "academic"]
            if template not in valid_templates:
                console.print(f"[yellow]⚠ Unknown template '{template}'. Using 'standard'.[/yellow]")
                template = "standard"
            config["template"] = template

            include_tree = input("Include folder tree? [Y/n]: ").strip().lower()
            config["include_tree"] = include_tree != "n"

            # Scan and generate
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
            except Exception as gen_error:
                from projectreadmegen.exceptions import ProjectReadmeGenException
                if isinstance(gen_error, ProjectReadmeGenException):
                    console.print(f"[red]✗ Generation Error: {gen_error.user_message}[/red]")
                else:
                    console.print(f"[red]✗ Failed to generate README: {gen_error}[/red]")
                    logger.error(f"Generation error: {gen_error}", exc_info=True)
                input("\nPress Enter to continue...")
                return

        # Save the README
        try:
            output_path = root / config["output_file"]
            save_readme(readme, str(output_path))
        except Exception as save_error:
            from projectreadmegen.exceptions import ProjectReadmeGenException
            if isinstance(save_error, ProjectReadmeGenException):
                console.print(f"[red]✗ Save Error: {save_error.user_message}[/red]")
            else:
                console.print(f"[red]✗ Failed to save README: {save_error}[/red]")
            input("\nPress Enter to continue...")
            return

        credits_msg = usagetracker.get_remaining_credits()

        console.print(
            Panel(
                f"[green]✓ README generated successfully![/green]\n\n"
                f"  Project  : [bold]{scan['name']}[/bold]\n"
                f"  Mode     : [bold]Interactive {'(AI)' if ai else '(Template)'}[/bold]\n"
                f"  Saved to : [bold]{output_path}[/bold]\n\n"
                f"{credits_msg}",
                title="projectreadmegen",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
    except Exception as e:
        logger.error(f"Unexpected error in interactive mode: {e}", exc_info=True)
        console.print(f"[red]✗ Error: {e}[/red]")

    input("\nPress Enter to continue...")


def main_menu_loop():
    while True:
        try:
            choice = show_main_menu()

            if choice == "1":
                handle_create_ai()
            elif choice == "2":
                handle_create_normal()
            elif choice == "3":
                handle_manage_api()
            elif choice == "4":
                handle_credits_status()
            elif choice == "5":
                handle_update()
            elif choice == "6":
                handle_help()
            elif choice == "7":
                handle_github_profile()
            elif choice == "8":
                console.print("\n[cyan]Thank you for using projectreadmegen![/cyan]\n")
                break
            else:
                console.print("\n[red]Invalid choice. Please try again.[/red]")
                input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            console.print(
                "\n\n[cyan]Goodbye! Thank you for using projectreadmegen![/cyan]\n"
            )
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")


@app.command()
def start():
    """Start interactive menu mode."""
    main_menu_loop()


@app.command()
def version():
    """Show version information."""
    from projectreadmegen import __version__

    console = Console()
    console.print(f"""
[bold cyan]projectreadmegen[/bold cyan] version {__version__}

[dim]Auto-generate README files with AI power[/dim]

[green]Powered by Zenith Open Source Projects | Developer - roshhellwett[/green]
    """)


@app.command()
def update():
    """Check for updates and upgrade projectreadmegen."""
    handle_update()


@app.command()
def generate(
    path: str = typer.Argument(".", help="Path to the project directory"),
    template: str | None = typer.Option(
        None,
        "--template",
        "-t",
        help="Template to use: minimal | standard | full | academic",
    ),
    output: str = typer.Option(
        "README.md", "--output", "-o", help="Output filename (default: README.md)"
    ),
    no_badges: bool = typer.Option(
        False, "--no-badges", help="Disable badge generation"
    ),
    depth: int = typer.Option(
        3, "--depth", "-d", help="Max folder tree depth (default: 3)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print README to terminal without saving to file"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing README.md without confirmation"
    ),
    ai: bool = typer.Option(
        False, "--ai", "-a", "--grok", help="Use Grok AI to generate enhanced README"
    ),
    auto_ai: bool = typer.Option(
        False, "--auto-ai", help="Auto-detect and use AI when API key is available"
    ),
):
    from projectreadmegen.exceptions import ProjectReadmeGenException

    console = Console()
    root = Path(path).resolve()

    # Validate path
    if not root.exists():
        console.print(f"[red]✗ Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)

    if not root.is_dir():
        console.print(f"[red]✗ Error: '{path}' is not a directory.[/red]")
        raise typer.Exit(code=1)

    # Load config
    try:
        config = load_config(str(root))
    except ProjectReadmeGenException as e:
        console.print("[red]✗ Configuration Error:[/red]")
        console.print(f"[yellow]{e.user_message}[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Failed to load configuration: {e}[/red]")
        raise typer.Exit(code=1)

    if not template:
        template = usagetracker.get_project_last_template(str(root))

    if template:
        # Validate template
        valid_templates = ["minimal", "standard", "full", "academic"]
        if template.lower() in valid_templates:
            config["template"] = template.lower()
        else:
            console.print(f"[yellow]⚠ Unknown template '{template}'. Using 'standard'.[/yellow]")
            config["template"] = "standard"

    if no_badges:
        config["include_badges"] = False

    # Validate depth
    if depth < 1 or depth > 10:
        console.print("[yellow]⚠ Tree depth must be 1-10. Using default of 3.[/yellow]")
        depth = 3
    config["max_tree_depth"] = depth

    if ai:
        config["ai_enabled"] = True
    if auto_ai:
        config["ai_enabled"] = True

    use_ai = config.get("ai_enabled", False) or auto_ai

    if use_ai and not usagetracker.check_api_key():
        usagetracker.require_api_key()

    output_path = root / output
    if output_path.exists() and not dry_run and not force:
        readme_info = usagetracker.get_project_readme_info(str(root))

        if readme_info.get("last_readme_mtime"):
            current_mtime = output_path.stat().st_mtime
            last_gen_time = readme_info.get("last_generate_time", 0)

            if current_mtime > last_gen_time:
                console.print(
                    "[yellow]Warning: README.md has been modified since last generation.[/yellow]"
                )
                console.print(
                    "[dim]Use --force to overwrite or regenerate manually.[/dim]"
                )

        overwrite = typer.confirm(
            f"'{output}' already exists. Overwrite?", default=False
        )
        if not overwrite:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            task = progress.add_task("Scanning project...", total=None)
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            except ProjectReadmeGenException as e:
                console.print(f"[red]✗ Scan Error: {e.user_message}[/red]")
                raise typer.Exit(code=1)
            except Exception as e:
                console.print(f"[red]✗ Failed to scan project: {e}[/red]")
                logger.error(f"Scan error: {e}", exc_info=True)
                raise typer.Exit(code=1)

            progress.update(task, description="Detecting stack...")
            detection = detect_stack(scan)

            if use_ai:
                allowed, message = usagetracker.check_free_limit()

                if not allowed:
                    can_continue = usagetracker.handle_exhausted()
                    if not can_continue:
                        raise typer.Exit(code=1)

                if "Free use" in message:
                    console.print(f"[yellow]{message}[/yellow]")

                progress.update(task, description="Generating README with Grok AI...")
                try:
                    readme = grok.generate_ai_readme(scan, detection, config)
                except ProjectReadmeGenException as ai_e:
                    progress.stop()
                    console.print(f"[yellow]⚠ {ai_e.user_message}[/yellow]")
                    console.print("[dim]Falling back to template-based generation...[/dim]")
                    readme = generate_readme(scan, detection, config)
                    progress = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    )
                    progress.start()
                    task = progress.add_task("Finishing...", total=None)
                except Exception as ai_e:
                    logger.error(f"AI generation error: {ai_e}", exc_info=True)
                    progress.stop()
                    console.print("[yellow]⚠ AI generation failed, falling back to template[/yellow]")
                    readme = generate_readme(scan, detection, config)
                    progress = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    )
                    progress.start()
                    task = progress.add_task("Finishing...", total=None)
            else:
                progress.update(task, description="Generating README...")
                readme = generate_readme(scan, detection, config)

        except typer.Exit:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}", exc_info=True)
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            raise typer.Exit(code=1)

    if dry_run:
        console.print(Panel(readme, title="[cyan]README Preview[/cyan]", expand=False))
    else:
        try:
            save_readme(readme, str(output_path))
        except ProjectReadmeGenException as e:
            console.print(f"[red]✗ Save Error: {e.user_message}[/red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]✗ Failed to save README: {e}[/red]")
            logger.error(f"Save error: {e}", exc_info=True)
            raise typer.Exit(code=1)

        usagetracker.save_project_cache(
            str(root), {"template": config.get("template", "standard")}
        )
        usagetracker.save_project_readme_info(str(root), str(output_path))

        credits_msg = usagetracker.get_remaining_credits()

        console.print(
            Panel(
                f"[green]✓ README generated successfully![/green]\n\n"
                f"  Project  : [bold]{scan['name']}[/bold]\n"
                f"  Language : [bold]{detection['primary_lang']}[/bold]\n"
                f"  Type     : [bold]{detection['project_type']}[/bold]\n"
                f"  Template : [bold]{config['template']}[/bold]\n"
                f"  Saved to : [bold]{output_path}[/bold]\n\n"
                f"{credits_msg}",
                title="projectreadmegen",
                border_style="green",
            )
        )


@app.command()
def interactive(
    path: str = typer.Argument(".", help="Path to the project directory"),
    ai: bool = typer.Option(
        False, "--ai", "-a", "--grok", help="Use Grok AI to generate enhanced README"
    ),
):
    """Interactive mode — answer questions to customize your README."""
    from projectreadmegen.exceptions import ProjectReadmeGenException

    console = Console()
    console.print("[bold cyan]projectreadmegen — Interactive Mode[/bold cyan]\n")

    root = Path(path).resolve()

    # Validate path
    if not root.exists():
        console.print(f"[red]✗ Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)

    if not root.is_dir():
        console.print(f"[red]✗ Error: '{path}' is not a directory.[/red]")
        raise typer.Exit(code=1)

    # Load configuration
    try:
        config = load_config(str(root))
    except ProjectReadmeGenException as e:
        console.print(f"[red]✗ Configuration Error: {e.user_message}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Failed to load configuration: {e}[/red]")
        raise typer.Exit(code=1)

    if ai:
        if not usagetracker.check_api_key():
            console.print("[yellow]API key required for AI features.[/yellow]")
            usagetracker.require_api_key()

        try:
            console.print("[yellow]Using AI to generate README...[/yellow]")
            scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            detection = detect_stack(scan)
            readme = grok.generate_ai_readme(scan, detection, config)
        except ProjectReadmeGenException as e:
            console.print(f"[yellow]⚠ {e.user_message}[/yellow]")
            console.print("[dim]Falling back to template-based generation...[/dim]")
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
            except Exception as fallback_e:
                console.print(f"[red]✗ Failed to generate README: {fallback_e}[/red]")
                logger.error(f"Fallback generation error: {fallback_e}", exc_info=True)
                raise typer.Exit(code=1)
        except Exception as ai_e:
            logger.error(f"AI generation error: {ai_e}", exc_info=True)
            console.print("[yellow]⚠ AI generation unavailable. Falling back to template.[/yellow]")
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
            except Exception as fallback_e:
                console.print(f"[red]✗ Failed to generate README: {fallback_e}[/red]")
                logger.error(f"Fallback generation error: {fallback_e}", exc_info=True)
                raise typer.Exit(code=1)
    else:
        try:
            config["author"] = typer.prompt("Your name (optional)", default="")
            config["github_username"] = typer.prompt("Your GitHub username (optional)", default="")

            template = typer.prompt(
                "Template [minimal/standard/full/academic]", default="standard"
            ).lower()

            # Validate template
            valid_templates = ["minimal", "standard", "full", "academic"]
            if template not in valid_templates:
                console.print(f"[yellow]⚠ Unknown template '{template}'. Using 'standard'.[/yellow]")
                template = "standard"
            config["template"] = template

            include_tree = typer.confirm("Include folder tree in README?", default=True)
            config["include_tree"] = include_tree

            scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            detection = detect_stack(scan)
            readme = generate_readme(scan, detection, config)
        except ProjectReadmeGenException as e:
            console.print(f"[red]✗ Generation Error: {e.user_message}[/red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]✗ Failed to generate README: {e}[/red]")
            logger.error(f"Generation error: {e}", exc_info=True)
            raise typer.Exit(code=1)

    # Save README
    try:
        output_path = root / config["output_file"]
        save_readme(readme, str(output_path))
    except ProjectReadmeGenException as e:
        console.print(f"[red]✗ Save Error: {e.user_message}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Failed to save README: {e}[/red]")
        logger.error(f"Save error: {e}", exc_info=True)
        raise typer.Exit(code=1)

    credits_msg = usagetracker.get_remaining_credits()

    console.print(
        Panel(
            f"[green]✓ README generated successfully![/green]\n\n"
            f"  Project  : [bold]{scan['name']}[/bold]\n"
            f"  Mode     : [bold]Interactive {'(AI)' if ai else '(Template)'}[/bold]\n"
            f"  Saved to : [bold]{output_path}[/bold]\n\n"
            f"{credits_msg}",
            title="projectreadmegen",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()

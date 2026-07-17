# cli.py

import os
import logging
from pathlib import Path
from typing import Optional

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

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="projectreadmegen — Auto-generate README files from folder structure.",
    add_completion=False,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "-help", "--help"]},
    no_args_is_help=False,
    rich_markup_mode="rich",
)
console = Console()


def print_version():
    console.print(f"""
[bold white]projectreadmegen[/bold white] [dim]v{__version__}[/dim]
[dim]Architectural Documentation Suite & Web Studio[/dim]

[dim]Powered by Zenith Open Source Projects | Developer: roshhellwett[/dim]
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
            f"""
[bold white]PROJECT README GEN STUDIO v{__version__}[/bold white]
[dim]Architectural Documentation & Web Suite[/dim]

[dim]Select an execution mode:[/dim]

  [bold white]1.[/bold white]  Create README with AI Architecture
  [bold white]2.[/bold white]  Create Normal README (Deterministic Engine)
  [bold white]3.[/bold white]  Manage API Key & Credentials
  [bold white]4.[/bold white]  View Quota & System Diagnostics
  [bold white]5.[/bold white]  Update Package Version
  [bold white]6.[/bold white]  Help & Command Reference
  [bold white]7.[/bold white]  Create GitHub Profile README
  [bold white]8.[/bold white]  Launch Web UI Studio
  [bold white]9.[/bold white]  Exit Suite
        """,
            border_style="dim",
        )
    )
    choice = input("\n> Enter selection (1-9): ").strip()
    return choice


def handle_launch_web(port: int = 8000, host: str = "127.0.0.1"):
    import uvicorn
    from projectreadmegen.server import app as web_app

    console.print(
        f"\n[bold white]Launching Project README Gen Web UI Studio...[/bold white]"
    )
    console.print(
        f"[dim]Studio accessible at:[/dim] [bold blue]http://{host}:{port}[/bold blue]"
    )
    console.print("[dim]Press Ctrl+C to stop the server and return to menu[/dim]\n")
    try:
        uvicorn.run(web_app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        console.print("\n[dim]Web Studio server stopped. Returning to menu...[/dim]\n")
    except OSError as e:
        if (
            "address is already in use" in str(e).lower()
            or "only one usage of each socket address" in str(e).lower()
            or getattr(e, "errno", None) in (48, 98, 10048)
        ):
            console.print(
                f"\n[bold yellow][!] Port {port} is currently busy or already in use.[/bold yellow]"
            )
            console.print(
                f"[dim]Fallback Solution:[/dim] Try running on another port from terminal using: [bold white]python -m projectreadmegen web --port {port + 1}[/bold white]\n"
            )
        else:
            console.print(f"\n[red][-] Server Error: {e}[/red]\n")
        input("Press Enter to return to menu...")
    except Exception as e:
        console.print(f"\n[red][-] Server Error: {e}[/red]\n")
        input("Press Enter to return to menu...")


def handle_create_ai():
    if not usagetracker.check_api_key():
        if not usagetracker.require_api_key():
            return

    console.print("\n[bold white]Select generation mode:[/bold white]")
    console.print("  [bold white]1.[/bold white]  Quick Mode (Automated)")
    console.print("  [bold white]2.[/bold white]  Interactive Mode (Custom questions)")

    mode = input("\n> Enter mode (1/2): ").strip()

    path = input("\n> Enter project path (default: .): ").strip() or "."

    if mode == "2":
        handle_interactive_mode(ai=True, path=path)
    else:
        handle_generate_mode(ai=True, path=path)


def handle_create_normal():
    console.print("\n[bold white]Select generation mode:[/bold white]")
    console.print("  [bold white]1.[/bold white]  Quick Mode (Automated)")
    console.print("  [bold white]2.[/bold white]  Interactive Mode (Custom questions)")

    mode = input("\n> Enter mode (1/2): ").strip()

    path = input("\n> Enter project path (default: .): ").strip() or "."

    if mode == "2":
        handle_interactive_mode(ai=False, path=path)
    else:
        handle_generate_mode(ai=False, path=path)


def handle_manage_api():
    user_key = usagetracker.get_api_key()
    has_key = bool(user_key)

    if has_key:
        console.print("""
[bold white]API Key Management[/bold white]
[dim]Status: Active Groq API Key Configured[/dim]

  [bold white]1.[/bold white]  Update API Key (replace current)
  [bold white]2.[/bold white]  Remove API Key
  [bold white]3.[/bold white]  Manage GitHub Token
  [bold white]4.[/bold white]  Return to Main Menu
        """)
    else:
        console.print("""
[bold white]API Key Management[/bold white]
[dim]Status: No Groq API Key Configured (Required for AI generation)[/dim]

  [bold white]1.[/bold white]  Configure Groq API Key
  [bold white]2.[/bold white]  Manage GitHub Token
  [bold white]3.[/bold white]  Return to Main Menu
        """)

    choice = input("\n> Enter selection: ").strip()

    if has_key and choice == "1":
        key = input("\n> Enter new Groq API key: ").strip()
        if not key:
            console.print("[dim]No key provided. Operation cancelled.[/dim]")
        elif key.startswith("gsk_") and len(key) > 10:
            usagetracker.save_api_key(key)
            console.print(
                "[bold white][+] API key updated and synced atomically across CLI & Web Studio.[/bold white]"
            )
        else:
            console.print(
                "[red][-] Invalid key format. Key should start with 'gsk_' and exceed 10 characters.[/red]"
            )
            console.print(
                "[dim]Obtain your API key at: https://console.groq.com/keys[/dim]"
            )
        input("\nPress Enter to continue...")
    elif has_key and choice == "2":
        usagetracker.clear_api_key()
        console.print("[bold white][+] API key removed.[/bold white]")
        input("\nPress Enter to continue...")
    elif has_key and choice == "3":
        handle_github_token_settings()
    elif not has_key and choice == "1":
        console.print("""
[bold white]API Key Setup Instructions:[/bold white]
[dim]1. Visit: https://console.groq.com/keys[/dim]
[dim]2. Click "Create Key"[/dim]
[dim]3. Paste the key below:[/dim]
        """)
        key = input("\n> Enter Groq API key: ").strip()
        if not key:
            console.print("[dim]No key provided. Operation cancelled.[/dim]")
        elif key.startswith("gsk_") and len(key) > 10:
            usagetracker.save_api_key(key)
            console.print(
                "[bold white][+] API key configured and synced atomically across CLI & Web Studio.[/bold white]"
            )
        else:
            console.print(
                "[red][-] Invalid key format. Key should start with 'gsk_' and exceed 10 characters.[/red]"
            )
        input("\nPress Enter to continue...")
    elif not has_key and choice == "2":
        handle_github_token_settings()
    elif (has_key and choice == "4") or (not has_key and choice == "3"):
        return


def handle_credits_status():
    unified = usagetracker.get_unified_status_dict()
    has_key = unified["api_key_configured"]
    has_github_token = unified["github_token_configured"]
    msg = unified["credits_message"]
    storage_path = unified["storage_path"]

    console.print(
        Panel(
            f"""
[bold white]System Diagnostics & API Quota Dashboard[/bold white]

  [bold white]Groq API Key:[/bold white] {"[bold white]Active (" + (unified['api_key_masked'] or 'Configured') + ")[/bold white]" if has_key else "[red]Not configured[/red]"}
  [bold white]GitHub Token:[/bold white] {"[bold white]Active (" + (unified['github_token_masked'] or 'Configured') + ")[/bold white]" if has_github_token else "[dim]Not configured[/dim]"}
  [bold white]Storage Path:[/bold white] [dim]{storage_path}[/dim]

  {msg}

[bold white]Architectural Notes:[/bold white]
  - Groq API Key required for LPU inference engine (`generate --ai` & `profile`)
  - GitHub Token optional for higher REST rate limits (5,000 req/hr)
  - Credentials stored atomically and shared instantly with Web Studio
            """,
            border_style="dim",
        )
    )
    input("\nPress Enter to continue...")


def handle_help():
    console.print("""
[bold white]Command Reference & Execution Cheat Sheet[/bold white]

[bold white]Terminal Execution:[/bold white]
  python -m projectreadmegen generate .         Deterministic README engine
  python -m projectreadmegen generate . --ai    Groq LPU AI-synthesized README
  python -m projectreadmegen generate . -a      Short flag for --ai
  python -m projectreadmegen interactive .      Interactive custom questions
  python -m projectreadmegen web --port 8000    Launch Web Studio SPA
  python -m projectreadmegen --help             Inspect complete flags table

[bold white]CLI Flags & Parameters:[/bold white]
  --ai, -a, --grok     Enable Groq LPU™ AI synthesis
  --force, -f          Overwrite existing target file without prompt
  --dry-run            Render directly to stdout without writing to disk
  --template, -t        Preset target (`minimal` | `standard` | `full` | `academic`)
  --depth, -d          Max folder tree traversal depth (default: 3)
  --no-badges          Suppress badge generation

[bold white]Environment & Credentials:[/bold white]
  Obtain free LPU key: https://console.groq.com/keys
  Set via environment: $env:GROQ_API_KEY="your_key"

[dim]Press Ctrl+C to terminate execution anytime[/dim]
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
[bold white]GitHub API Token Management[/bold white]
[dim]Status: {"Active (" + masked_token + ")" if (has_token and masked_token) else "Not configured"}[/dim]

[dim]Benefits of configuring a GitHub Token:[/dim]
  - Expand API rate limits from 60 req/hr to 5,000 req/hr
  - Access private/public repository language breakdown accurately
  - Fetch detailed description and follower statistics

[bold white]Options:[/bold white]
  [bold white]1.[/bold white]  {"Update" if has_token else "Configure"} GitHub Token
  [bold white]2.[/bold white]  Remove Token {"(already not set)" if not has_token else ""}
  [bold white]3.[/bold white]  Return to Main Menu
    """)

    choice = input("\n> Enter selection: ").strip()

    if choice == "1":
        console.print("""
[bold white]Token Generation Instructions:[/bold white]
[dim]1. Visit: https://github.com/settings/tokens[/dim]
[dim]2. Generate new token (classic) with scopes: read:user, public_repo[/dim]
[dim]3. Paste the token below:[/dim]
        """)
        token = input("\n> Paste GitHub token (Enter to cancel): ").strip()
        if token:
            usagetracker.save_github_token(token)
            console.print(
                "[bold white][+] GitHub token configured and persisted.[/bold white]"
            )
        else:
            console.print("[dim]Operation cancelled.[/dim]")
        input("\nPress Enter to continue...")
    elif choice == "2" and has_token:
        usagetracker.clear_github_token()
        console.print("[bold white][+] GitHub token removed.[/bold white]")
        input("\nPress Enter to continue...")
    elif choice == "3":
        return


def handle_github_profile():
    """Handle GitHub Profile README generation."""
    if not usagetracker.check_api_key():
        console.print(
            Panel(
                """
[bold white]Authentication Required[/bold white]

To generate an AI-synthesized GitHub Profile README, an active Groq API key is required.

[dim]Instructions:[/dim]
1. Visit: https://console.groq.com/keys
2. Create key and paste below
            """,
                border_style="dim",
            )
        )

        key = input("\n> Paste Groq API key: ").strip()
        if key and key.startswith("gsk_"):
            usagetracker.save_api_key(key)
            console.print(
                "[bold white][+] API key saved and shared across CLI & Web Studio.[/bold white]\n"
            )
        else:
            console.print("[red][-] Invalid key format. Operation cancelled.[/red]")
            input("\nPress Enter to continue...")
            return

    console.print(
        Panel(
            """
[bold white]GitHub Profile Architecture Studio[/bold white]
[dim]Synthesizing dynamic Bento & Profile README documentation[/dim]

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

    username = input("\n> Enter GitHub username: ").strip()
    if not username:
        console.print("[red][-] Username cannot be empty.[/red]")
        input("\nPress Enter to continue...")
        return

    is_valid, error = github_profile.validate_github_username(username)
    if not is_valid:
        console.print(f"[red][-] Invalid username: {error}[/red]")
        input("\nPress Enter to continue...")
        return

    profile_url = input(
        f"> Enter GitHub profile URL (default: https://github.com/{username}): "
    ).strip()
    if not profile_url:
        profile_url = f"https://github.com/{username}"

    console.print("""
[bold white]Select Profile Architecture:[/bold white]

  [bold white]1.[/bold white]  Basic Architecture (`basic`)
      Clean, minimal, high-contrast overview

  [bold white]2.[/bold white]  Professional Corporate (`professional`)
      Career-focused layout with structured sections & metrics

  [bold white]3.[/bold white]  Dynamic Stats Studio (`stylish`)
      Bento-inspired with live dynamic shields & stat cards

  [bold white]4.[/bold white]  Unique Bento (`unique`)
      Eye-catching, comprehensive architectural profile
    """)

    style_choice = input("\n> Enter style (1-4, default: 2): ").strip() or "2"

    style_map = {"1": "basic", "2": "professional", "3": "stylish", "4": "unique"}
    style = style_map.get(style_choice, "professional")

    output_path = (
        input("\n> Enter output path (default: current directory): ").strip() or "."
    )

    success, folder_path = github_profile.create_output_folder(username, output_path)
    if not success:
        console.print(f"[red][-] Error creating directory: {folder_path}[/red]")
        input("\nPress Enter to continue...")
        return

    exists, readme_path = github_profile.check_readme_exists(folder_path)
    if exists:
        console.print(
            f"\n[yellow][!] Warning: Target file {readme_path} already exists[/yellow]"
        )
        overwrite = input("> Overwrite target? (y/N): ").strip().lower()
        if overwrite != "y":
            console.print("[dim]Operation cancelled.[/dim]")
            input("\nPress Enter to continue...")
            return

    github_token = (
        usagetracker.get_github_token() if usagetracker.has_github_token() else None
    )

    if not github_token:
        console.print(
            """
[bold white]GitHub API Token (Optional Enhancement)[/bold white]
[dim]Configuring a token expands rate limits and enables precise language usage calculations.[/dim]

[bold white]Press Enter to proceed without token[/bold white], or type 'y' to configure now:"""
        )
        add_token = input().strip().lower()
        if add_token == "y":
            console.print("""
[dim]1. Visit: https://github.com/settings/tokens[/dim]
[dim]2. Generate token with read:user scope[/dim]
[dim]3. Paste below:[/dim]
            """)
            token = input("> GitHub token: ").strip()
            if token:
                github_token = token
                usagetracker.save_github_token(token)
                console.print(
                    "[bold white][+] Token persisted and active.[/bold white]\n"
                )

    console.print(
        "\n[bold white][*] Fetching REST metrics from GitHub API...[/bold white]"
    )

    user_data = None
    repos = []
    languages = {}

    try:
        user_data = github_profile.fetch_github_user(username, github_token)
        if not user_data:
            console.print(
                f"[yellow][!] Could not query profile metadata for @{username}[/yellow]"
            )
            console.print(
                "[dim]Proceeding with deterministic profile structure.[/dim]\n"
            )
    except Exception as e:
        console.print(f"[yellow][!] GitHub query fallback triggered: {str(e)}[/yellow]")
        console.print("[dim]Proceeding with structural fallback engine...[/dim]\n")

    if user_data:
        try:
            repos = github_profile.fetch_user_repos(username, github_token)
            languages = github_profile.calculate_language_stats(repos)
        except Exception as e:
            console.print(
                f"[yellow][!] Repository inspection fallback: {str(e)}[/yellow]"
            )

    console.print(
        f"[bold white][+] Indexed {len(repos)} public repositories[/bold white]"
    )
    if languages:
        top_langs = list(languages.items())[:5]
        console.print(
            f"[dim]Top detected languages: {', '.join([lang[0] for lang in top_langs])}[/dim]\n"
        )

    console.print(
        f"[bold white][*] Synthesizing {style} profile architecture...[/bold white]\n"
    )

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
[bold white]GitHub Profile Architecture Completed[/bold white]

  [bold white]Target Username :[/bold white] @{username}
  [bold white]Architecture    :[/bold white] {style.capitalize()}
  [bold white]Target File     :[/bold white] {result}

[bold white]Deployment Checklist:[/bold white]
  1. Commit `{result}` into your public profile repository (`{username}/{username}`)
  2. Push to GitHub (`git push origin main`)
  3. Verify live dynamic shields at `{profile_url}`
                """,
                    border_style="dim",
                )
            )
        else:
            console.print(f"[red][-] Error writing artifact: {result}[/red]")

    except Exception as e:
        console.print(f"[red][-] Synthesis exception encountered: {str(e)}[/red]")
        console.print("[dim]Check rate quotas or inspect network state.[/dim]")

    input("\nPress Enter to continue...")


def handle_update():
    import subprocess
    import sys
    import shutil
    import os
    from pathlib import Path

    def _safe_pip_upgrade():
        temp_old_exe = None
        if sys.platform == "win32":
            try:
                exe_path_str = shutil.which("projectreadmegen")
                if exe_path_str:
                    exe_path = Path(exe_path_str)
                    if exe_path.exists() and exe_path.suffix.lower() == ".exe":
                        temp_old_exe = exe_path.with_name(
                            f"projectreadmegen_old_{os.getpid()}.exe"
                        )
                        if temp_old_exe.exists():
                            try:
                                temp_old_exe.unlink()
                            except Exception:
                                pass
                        exe_path.rename(temp_old_exe)
            except Exception as unlock_err:
                console.print(
                    f"[dim]Note: Could not rename active executable before upgrade: {unlock_err}[/dim]"
                )

        update_result = subprocess.run(
            ["pip", "install", "--upgrade", "projectreadmegen"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if update_result.returncode == 0:
            console.print(
                "[bold white][+] Upgrade completed successfully![/bold white]\n"
            )
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
                        f"  Active version: [bold white]{new_version}[/bold white]\n"
                    )
                    break
            if temp_old_exe and temp_old_exe.exists():
                try:
                    temp_old_exe.unlink()
                except Exception:
                    pass
        else:
            if temp_old_exe and temp_old_exe.exists():
                try:
                    exe_path = Path(
                        shutil.which("projectreadmegen")
                        or str(temp_old_exe.with_name("projectreadmegen.exe"))
                    )
                    if not exe_path.exists():
                        temp_old_exe.rename(exe_path)
                except Exception:
                    pass
            console.print(
                f"[red][-] Upgrade encountered an issue:\n{update_result.stderr or update_result.stdout}[/red]"
            )
            if "WinError 32" in (update_result.stderr or "") or "access the file" in (
                update_result.stderr or ""
            ):
                console.print(
                    "\n[bold yellow]Windows Process Lock Detected[/bold yellow]"
                )
                console.print(
                    "[white]Because projectreadmegen.exe is currently active, Windows prevented pip from overwriting it.[/white]"
                )
                console.print(
                    "[bold cyan]To upgrade cleanly, close this terminal window and run:[/bold cyan]"
                )
                console.print(
                    "  [bold white]pip install --upgrade projectreadmegen[/bold white]\n"
                )

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
            console.print(
                f"  Current installed : [bold white]{current_version}[/bold white]"
            )
            console.print("[dim]Checking PyPI index for upgrades...[/dim]")
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
                console.print(
                    "[bold white][!] Newer package release detected on PyPI[/bold white]"
                )
                console.print("  Executing pip upgrade package...\n")
                _safe_pip_upgrade()
            else:
                console.print(
                    "[bold white][+] Current installation matches latest PyPI release[/bold white]\n"
                )

            input("Press Enter to continue...")
            return

        console.print(
            f"  Current installed : [bold white]{current_version}[/bold white]"
        )
        console.print(
            f"  Latest on PyPI    : [bold white]{latest_version}[/bold white]\n"
        )

        if current_version != latest_version and latest_version != "Unknown":
            console.print(
                "[bold white][!] Newer package release detected on PyPI[/bold white]"
            )
            console.print("  Executing pip upgrade package...\n")
            _safe_pip_upgrade()
        else:
            console.print(
                "[bold white][+] Current installation matches latest PyPI release[/bold white]\n"
            )

    except Exception as e:
        console.print(f"[red][-] Diagnostic query failed: {e}[/red]\n")

    input("Press Enter to continue...")


def handle_generate_mode(ai=False, path="."):
    try:
        root = Path(path).resolve()

        # Validate path
        if not root.exists():
            console.print(
                f"[red][-] Target path '{path}' could not be resolved on disk.[/red]"
            )
            console.print("[dim]  Verify directory structure or permissions.[/dim]")
            input("\nPress Enter to continue...")
            return

        if not root.is_dir():
            console.print(
                f"[red][-] Target '{path}' is a file rather than a directory root.[/red]"
            )
            console.print("[dim]  Provide the root project directory path.[/dim]")
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
                        from projectreadmegen.exceptions import (
                            APIError as CustomAPIError,
                        )

                        if isinstance(ai_error, CustomAPIError):
                            progress.stop()
                            console.print(f"[yellow]⚠ {ai_error.user_message}[/yellow]")
                            console.print(
                                "[dim]Falling back to template-based generation...[/dim]"
                            )
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
                        console.print(
                            f"[red]✗ Save Error: {save_error.user_message}[/red]"
                        )
                    else:
                        console.print(
                            f"[red]✗ Failed to save README: {save_error}[/red]"
                        )
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
                console.print("[red][-] Configuration Error:[/red]")
                console.print(f"[dim]  {e.user_message}[/dim]")
            else:
                console.print(f"[red][-] Configuration Error: {e}[/red]")
            input("\nPress Enter to continue...")
            return

        if ai:
            if not usagetracker.check_api_key():
                can_continue = usagetracker.require_api_key()
                if not can_continue:
                    return

            console.print(
                "\n[bold white][*] Synthesizing AI documentation architecture...[/bold white]"
            )
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = grok.generate_ai_readme(scan, detection, config)
            except Exception as ai_error:
                from projectreadmegen.exceptions import ProjectReadmeGenException

                if isinstance(ai_error, ProjectReadmeGenException):
                    console.print(f"[yellow][!] {ai_error.user_message}[/yellow]")
                else:
                    logger.error(f"AI generation error: {ai_error}")
                    console.print(
                        f"[yellow][!] LPU engine unavailable. {str(ai_error)[:100]}[/yellow]"
                    )
                console.print(
                    "[dim][+] Fallback triggered: Deterministic template engine active.[/dim]"
                )
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
        else:
            console.print(
                "\n[bold white]Interactive Customization Studio[/bold white]\n"
            )

            # Collect user input with validation
            author = input("> Author name (optional): ").strip()
            if author:
                config["author"] = author

            github_user = input("> GitHub username (optional): ").strip()
            if github_user:
                if len(github_user) < 1 or len(github_user) > 39:
                    console.print(
                        "[yellow][!] GitHub username should be 1-39 characters. Skipping.[/yellow]"
                    )
                else:
                    config["github_username"] = github_user

            template = (
                input(
                    "> Template [minimal/standard/full/academic] (default: standard): "
                ).strip()
                or "standard"
            ).lower()

            # Validate template
            valid_templates = ["minimal", "standard", "full", "academic"]
            if template not in valid_templates:
                console.print(
                    f"[yellow][!] Unknown target '{template}'. Defaulting to 'standard'.[/yellow]"
                )
                template = "standard"
            config["template"] = template

            include_tree = (
                input("> Include ASCII folder structure? [Y/n]: ").strip().lower()
            )
            config["include_tree"] = include_tree != "n"

            # Scan and generate
            try:
                scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
                detection = detect_stack(scan)
                readme = generate_readme(scan, detection, config)
            except Exception as gen_error:
                from projectreadmegen.exceptions import ProjectReadmeGenException

                if isinstance(gen_error, ProjectReadmeGenException):
                    console.print(
                        f"[red][-] Generation Error: {gen_error.user_message}[/red]"
                    )
                else:
                    console.print(
                        f"[red][-] Failed to generate documentation: {gen_error}[/red]"
                    )
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
                console.print(
                    f"[red][-] File IO Error: {save_error.user_message}[/red]"
                )
            else:
                console.print(f"[red][-] Failed to write file: {save_error}[/red]")
            input("\nPress Enter to continue...")
            return

        credits_msg = usagetracker.get_remaining_credits()

        console.print(
            Panel(
                f"[bold white]Documentation Architecture Generated Successfully[/bold white]\n\n"
                f"  [bold white]Project  :[/bold white] {scan['name']}\n"
                f"  [bold white]Engine   :[/bold white] {'LPU AI Synthesis' if ai else 'Deterministic Template'}\n"
                f"  [bold white]Target   :[/bold white] {output_path}\n\n"
                f"[dim]{credits_msg}[/dim]",
                border_style="dim",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[dim]Operation aborted by user.[/dim]")
    except Exception as e:
        logger.error(f"Unexpected error in interactive mode: {e}", exc_info=True)
        console.print(f"[red][-] Runtime Error: {e}[/red]")

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
                handle_launch_web()
            elif choice == "9":
                console.print(
                    "\n[dim]Terminating Project README Gen Studio session. Goodbye.[/dim]\n"
                )
                break
            else:
                console.print(
                    "\n[red][-] Invalid selection. Choose a number between 1 and 9.[/red]"
                )
                input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            console.print(
                "\n\n[dim]Session terminated by user (`Ctrl+C`). Goodbye.[/dim]\n"
            )
            break
        except Exception as e:
            console.print(f"[red][-] Error: {e}[/red]")
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
[bold white]projectreadmegen[/bold white] [dim]v{__version__}[/dim]

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
            console.print(
                f"[yellow]⚠ Unknown template '{template}'. Using 'standard'.[/yellow]"
            )
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
                    console.print(
                        "[dim]Falling back to template-based generation...[/dim]"
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
                except Exception as ai_e:
                    logger.error(f"AI generation error: {ai_e}", exc_info=True)
                    progress.stop()
                    console.print(
                        "[yellow]⚠ AI generation failed, falling back to template[/yellow]"
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
                f"[bold white]Documentation Architecture Generated Successfully[/bold white]\n\n"
                f"  [bold white]Project  :[/bold white] {scan['name']}\n"
                f"  [bold white]Language :[/bold white] {detection['primary_lang']}\n"
                f"  [bold white]Type     :[/bold white] {detection['project_type']}\n"
                f"  [bold white]Template :[/bold white] {config['template']}\n"
                f"  [bold white]Saved to :[/bold white] {output_path}\n\n"
                f"[dim]{credits_msg}[/dim]",
                border_style="dim",
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
            if not usagetracker.require_api_key():
                console.print(
                    "[red]✗ Groq API key setup cancelled. Cannot proceed with AI generation.[/red]"
                )
                raise typer.Exit(code=1)

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
            console.print(
                "[yellow]⚠ AI generation unavailable. Falling back to template.[/yellow]"
            )
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
            config["github_username"] = typer.prompt(
                "Your GitHub username (optional)", default=""
            )

            template = typer.prompt(
                "Template [minimal/standard/full/academic]", default="standard"
            ).lower()

            # Validate template
            valid_templates = ["minimal", "standard", "full", "academic"]
            if template not in valid_templates:
                console.print(
                    f"[yellow]⚠ Unknown template '{template}'. Using 'standard'.[/yellow]"
                )
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
            console.print(f"[red][-] Failed to generate documentation: {e}[/red]")
            logger.error(f"Generation error: {e}", exc_info=True)
            raise typer.Exit(code=1)

    # Save README
    try:
        output_path = root / config["output_file"]
        save_readme(readme, str(output_path))
    except ProjectReadmeGenException as e:
        console.print(f"[red][-] Save Error: {e.user_message}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red][-] Failed to save target file: {e}[/red]")
        logger.error(f"Save error: {e}", exc_info=True)
        raise typer.Exit(code=1)

    credits_msg = usagetracker.get_remaining_credits()

    console.print(
        Panel(
            f"[bold white]Documentation Architecture Generated Successfully[/bold white]\n\n"
            f"  [bold white]Project  :[/bold white] {scan['name']}\n"
            f"  [bold white]Mode     :[/bold white] Interactive ({'LPU AI Synthesis' if ai else 'Deterministic Engine'})\n"
            f"  [bold white]Target   :[/bold white] {output_path}\n\n"
            f"[dim]{credits_msg}[/dim]",
            border_style="dim",
        )
    )


@app.command()
def web(
    port: int = typer.Option(
        8000, "--port", "-p", help="Port to run the Web Studio on"
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind to"),
):
    """Launch the Project README Gen Web UI Studio."""
    handle_launch_web(port=port, host=host)


@app.command()
def profile(
    username: str = typer.Option(..., "--username", "-u", help="GitHub username"),
    style: str = typer.Option(
        "professional",
        "--style",
        "-s",
        help="Style preset: professional/stylish/unique/basic",
    ),
    output: str = typer.Option(
        ".", "--output", "-o", help="Output directory or file path"
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        help="Optional GitHub API token (defaults to stored config)",
    ),
):
    """Generate a GitHub Profile README directly from the terminal."""
    if not usagetracker.check_api_key():
        console.print(
            "[red][-] Groq API Key required. Execute `python -m projectreadmegen config --key gsk_...` first.[/red]"
        )
        raise typer.Exit(code=1)

    is_valid, error = github_profile.validate_github_username(username)
    if not is_valid:
        console.print(f"[red][-] Invalid username: {error}[/red]")
        raise typer.Exit(code=1)

    profile_url = f"https://github.com/{username}"
    github_token = token or (
        usagetracker.get_github_token() if usagetracker.has_github_token() else None
    )

    console.print(
        f"\n[bold white][*] Querying GitHub REST endpoints for @{username}...[/bold white]"
    )
    user_data = github_profile.fetch_github_user(username, github_token)
    repos = github_profile.fetch_user_repos(username, github_token) if user_data else []
    languages = github_profile.calculate_language_stats(repos) if repos else {}

    console.print(
        f"[bold white][+] Indexed {len(repos)} repositories and aggregated language distribution[/bold white]"
    )
    console.print(
        f"[bold white][*] Synthesizing {style} profile architecture via Groq LPU engine...[/bold white]\n"
    )

    try:
        readme_content = github_profile.generate_readme_content(
            username=username,
            profile_url=profile_url,
            style=style,
            user_data=user_data,
            repos=repos,
            languages=languages,
        )

        success, folder_path = github_profile.create_output_folder(username, output)
        if not success:
            console.print(
                f"[red][-] Error creating destination path: {folder_path}[/red]"
            )
            raise typer.Exit(code=1)

        success, result = github_profile.save_github_readme(
            readme_content, folder_path, username
        )
        if success:
            console.print(
                Panel(
                    f"[bold white]GitHub Profile Architecture Generated Successfully[/bold white]\n\n"
                    f"  [bold white]Target Username :[/bold white] @{username}\n"
                    f"  [bold white]Architecture    :[/bold white] {style.capitalize()}\n"
                    f"  [bold white]Output Artifact :[/bold white] {result}\n",
                    border_style="dim",
                )
            )
        else:
            console.print(f"[red][-] Error writing artifact: {result}[/red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red][-] Profile synthesis exception: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def config(
    key: Optional[str] = typer.Option(
        None, "--key", "-k", help="Set Groq API Key (starts with gsk_)"
    ),
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="Set GitHub API Token (starts with ghp_)"
    ),
    remove_key: bool = typer.Option(
        False, "--remove-key", help="Remove stored Groq API Key"
    ),
    remove_token: bool = typer.Option(
        False, "--remove-token", help="Remove stored GitHub Token"
    ),
    show: bool = typer.Option(False, "--show", help="Show currently configured keys"),
):
    """Set or inspect API keys and tokens for both CLI and Web Studio usage."""
    if remove_key:
        usagetracker.clear_api_key()
        console.print("[bold white][+] Groq API Key removed.[/bold white]")
    if remove_token:
        usagetracker.clear_github_token()
        console.print("[bold white][+] GitHub API Token removed.[/bold white]")
    if key:
        if key.startswith("gsk_") and len(key) > 10:
            usagetracker.save_api_key(key)
            console.print(
                "[bold white][+] Groq API Key persisted atomically across CLI and Web Studio.[/bold white]"
            )
        else:
            console.print(
                "[red][-] Invalid key format. Key must start with 'gsk_' and exceed 10 characters.[/red]"
            )
            raise typer.Exit(code=1)
    if token:
        usagetracker.save_github_token(token)
        console.print(
            "[bold white][+] GitHub API Token persisted atomically across CLI and Web Studio.[/bold white]"
        )

    if show or (not key and not token and not remove_key and not remove_token):
        unified = usagetracker.get_unified_status_dict()
        console.print(
            Panel(
                f"[bold white]Active Configuration Settings[/bold white]\n\n"
                f"  [bold white]Groq API Key :[/bold white] {'[bold white]Active (' + (unified['api_key_masked'] or '') + ')[/bold white]' if unified['api_key_configured'] else '[red]Not Set[/red]'}\n"
                f"  [bold white]GitHub Token :[/bold white] {'[bold white]Active (' + (unified['github_token_masked'] or '') + ')[/bold white]' if unified['github_token_configured'] else '[dim]Optional (Not Set)[/dim]'}\n"
                f"  [bold white]Storage Path :[/bold white] [dim]{unified['storage_path']}[/dim]\n",
                border_style="dim",
            )
        )


@app.command()
def status():
    """Show real-time diagnostic status, API keys, and credits in the terminal."""
    unified = usagetracker.get_unified_status_dict()
    console.print(
        Panel(
            f"[bold white]Project README Gen Studio — System Diagnostics[/bold white]\n\n"
            f"  [bold white]Engine Version :[/bold white] {__version__}\n"
            f"  [bold white]Groq API Key   :[/bold white] {'[bold white]Active (' + (unified['api_key_masked'] or '') + ')[/bold white]' if unified['api_key_configured'] else '[red]Not Configured[/red]'}\n"
            f"  [bold white]GitHub Token   :[/bold white] {'[bold white]Active (' + (unified['github_token_masked'] or '') + ')[/bold white]' if unified['github_token_configured'] else '[dim]Optional (Not Set)[/dim]'}\n"
            f"  [bold white]Storage Path   :[/bold white] [dim]{unified['storage_path']}[/dim]\n\n"
            f"  [dim]{unified['credits_message']}[/dim]\n",
            border_style="dim",
        )
    )


if __name__ == "__main__":
    app()

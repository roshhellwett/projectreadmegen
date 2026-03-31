# cli.py

import sys
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
from projectreadmegen.config import PRESETS
from projectreadmegen import grok
from projectreadmegen import usagetracker

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

from projectreadmegen import __version__

app = typer.Typer(help="projectreadmegen — Auto-generate README files from folder structure.", add_completion=False)
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
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
):
    if version:
        print_version()


def show_main_menu():
    console.clear()
    console.print(Panel(
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
  [green]7[/green]  Exit
        """,
        title="projectreadmegen Menu",
        border_style="cyan",
    ))
    choice = input("\nEnter your choice (1-7): ").strip()
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
        console.print(f"""
[bold yellow]Current Status:[/bold yellow]
  You have your own API key configured.

[bold]Options:[/bold]
  [green]1[/green]  Update API Key (replace current)
  [green]2[/green]  Remove API Key (use free credits)
  [green]3[/green]  Go Back
        """)
    else:
        console.print(f"""
[bold yellow]Current Status:[/bold yellow]
  No custom API key set. Using free credits (5/day).

[bold]Options:[/bold]
  [green]1[/green]  Add Your Own API Key
  [green]2[/green]  Go Back
        """)
    
    choice = input("\nEnter choice: ").strip()
    
    if has_key and choice == "1":
        key = input("\nEnter your new Groq API key: ").strip()
        if key and key.startswith("gsk_"):
            os.environ["GROQ_API_KEY"] = key
            data = usagetracker.load_usage_data()
            data["user_key_set"] = True
            usagetracker.save_usage_data(data)
            console.print("[green]API key updated successfully![/green]")
        else:
            console.print("[red]Invalid key format. Key should start with 'gsk_'[/red]")
        input("\nPress Enter to continue...")
    elif has_key and choice == "2":
        del os.environ["GROQ_API_KEY"]
        data = usagetracker.load_usage_data()
        data["user_key_set"] = False
        usagetracker.save_usage_data(data)
        console.print("[green]API key removed. Now using free credits.[/green]")
        input("\nPress Enter to continue...")
    elif not has_key and choice == "1":
        console.print(f"""
[bold]Get your free API key:[/bold]
1. Visit: https://console.groq.com/keys
2. Click "Create Key"
3. Copy the key and paste below
        """)
        key = input("\nEnter your Groq API key: ").strip()
        if key and key.startswith("gsk_"):
            os.environ["GROQ_API_KEY"] = key
            data = usagetracker.load_usage_data()
            data["user_key_set"] = True
            usagetracker.save_usage_data(data)
            console.print("[green]API key added successfully![/green]")
        else:
            console.print("[red]Invalid key format. Key should start with 'gsk_'[/red]")
        input("\nPress Enter to continue...")
    elif choice == "3" or choice == "2":
        return


def handle_credits_status():
    msg = usagetracker.get_remaining_credits()
    data = usagetracker.load_usage_data()
    
    user_key = os.environ.get("GROQ_API_KEY")
    has_key = bool(user_key) or data.get("user_key_set")
    
    console.print(f"""
[bold yellow]Credits Status:[/bold yellow]

  API Key: {'[green]Configured[/green]' if has_key else '[red]Not configured[/red]'}
  {msg}

[bold]Details:[/bold]
  - Free tier: 5 uses per day
  - With own API: Unlimited uses
  - Credits reset at midnight
    """)
    input("\nPress Enter to continue...")


def handle_help():
    console.print(f"""
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


def handle_update():
    import subprocess
    console.print("\n[bold cyan]Checking for updates...[/bold cyan]\n")
    
    try:
        result = subprocess.run(
            ["pip", "index", "versions", "projectreadmegen"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            available_versions = []
            for line in lines:
                if 'Available versions:' in line:
                    available_versions = line.replace('Available versions:', '').strip().split(', ')
                    break
            
            current_result = subprocess.run(
                ["pip", "show", "projectreadmegen"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            current_version = "Unknown"
            for line in current_result.stdout.split('\n'):
                if line.startswith('Version:'):
                    current_version = line.replace('Version:', '').strip()
                    break
            
            latest_version = available_versions[-1] if available_versions else "Unknown"
            
            console.print(f"  Current version: [yellow]{current_version}[/yellow]")
            console.print(f"  Latest version:  [green]{latest_version}[/green]\n")
            
            if current_version != latest_version and latest_version != "Unknown":
                console.print("[bold yellow]A new version is available![/bold yellow]")
                console.print("  Updating now...\n")
                
                update_result = subprocess.run(
                    ["pip", "install", "--upgrade", "projectreadmegen"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if update_result.returncode == 0:
                    console.print("[green]Update successful![/green]\n")
                    
                    new_result = subprocess.run(
                        ["pip", "show", "projectreadmegen"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    for line in new_result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            new_version = line.replace('Version:', '').strip()
                            console.print(f"  Updated to: [green]{new_version}[/green]\n")
                            break
                else:
                    console.print(f"[red]Update failed: {update_result.stderr}[/red]\n")
            else:
                console.print("[green]You are on the latest version![/green]\n")
        else:
            console.print("[red]Could not check for updates.[/red]\n")
            
    except Exception as e:
        console.print(f"[red]Error checking for updates: {e}[/red]\n")
    
    input("Press Enter to continue...")


def handle_generate_mode(ai=False, path="."):
    try:
        root = Path(path).resolve()
        if not root.exists():
            console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
            input("\nPress Enter to continue...")
            return
        
        if not root.is_dir():
            console.print(f"[red]Error: '{path}' is not a directory.[/red]")
            input("\nPress Enter to continue...")
            return
        
        config = load_config(str(root))
        
        if ai:
            usagetracker.show_key_setup()
            allowed, message = usagetracker.check_free_limit()
            
            if not allowed:
                can_continue = usagetracker.handle_exhausted()
                if not can_continue:
                    return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Scanning project...", total=None)
            scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            
            progress.update(task, description="Detecting stack...")
            detection = detect_stack(scan)
            
            if ai:
                progress.update(task, description="Generating README with AI...")
                readme = grok.generate_ai_readme(scan, detection, config)
            else:
                progress.update(task, description="Generating README...")
                readme = generate_readme(scan, detection, config)
        
        output_path = root / config["output_file"]
        save_readme(readme, str(output_path))
        
        credits_msg = usagetracker.get_remaining_credits()
        
        console.print(Panel(
            f"[green]README generated![/green]\n\n"
            f"  Project  : [bold]{scan['name']}[/bold]\n"
            f"  Language : [bold]{detection['primary_lang']}[/bold]\n"
            f"  Type     : [bold]{detection['project_type']}[/bold]\n"
            f"  Mode     : [bold]{'AI' if ai else 'Template'}[/bold]\n"
            f"  Saved to : [bold]{output_path}[/bold]\n\n"
            f"{credits_msg}",
            title="projectreadmegen",
            border_style="green",
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    input("\nPress Enter to continue...")


def handle_interactive_mode(ai=False, path="."):
    try:
        root = Path(path).resolve()
        if not root.exists():
            console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
            input("\nPress Enter to continue...")
            return
        
        config = load_config(str(root))
        
        if ai:
            usagetracker.show_key_setup()
            allowed, message = usagetracker.check_free_limit()
            
            if not allowed:
                can_continue = usagetracker.handle_exhausted()
                if not can_continue:
                    return
            
            console.print("\n[yellow]Generating AI-powered README...[/yellow]")
            scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            detection = detect_stack(scan)
            readme = grok.generate_ai_readme(scan, detection, config)
        else:
            console.print("\n[bold cyan]Interactive Mode[/bold cyan]\n")
            
            config["author"] = input("Your name: ").strip()
            config["github_username"] = input("Your GitHub username: ").strip()
            config["template"] = input("Template [minimal/standard/full/academic] (default: standard): ").strip() or "standard"
            include_tree = input("Include folder tree? [Y/n]: ").strip().lower()
            config["include_tree"] = include_tree != "n"
            
            scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
            detection = detect_stack(scan)
            readme = generate_readme(scan, detection, config)
        
        output_path = root / config["output_file"]
        save_readme(readme, str(output_path))
        
        credits_msg = usagetracker.get_remaining_credits()
        
        console.print(Panel(
            f"[green]README generated![/green]\n\n"
            f"  Project  : [bold]{scan['name']}[/bold]\n"
            f"  Mode     : [bold]Interactive {'(AI)' if ai else '(Template)'}[/bold]\n"
            f"  Saved to : [bold]{output_path}[/bold]\n\n"
            f"{credits_msg}",
            title="projectreadmegen",
            border_style="green",
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
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
                console.print("\n[cyan]Thank you for using projectreadmegen![/cyan]\n")
                break
            else:
                console.print("\n[red]Invalid choice. Please try again.[/red]")
                input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            console.print("\n\n[cyan]Goodbye! Thank you for using projectreadmegen![/cyan]\n")
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
    console = Console()
    console.print(f"""
[bold cyan]projectreadmegen[/bold cyan] version 1.6.5

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
    template: str | None = typer.Option(None, "--template", "-t",
        help="Template to use: minimal | standard | full | academic"),
    output: str = typer.Option("README.md", "--output", "-o",
        help="Output filename (default: README.md)"),
    no_badges: bool = typer.Option(False, "--no-badges",
        help="Disable badge generation"),
    depth: int = typer.Option(3, "--depth", "-d",
        help="Max folder tree depth (default: 3)"),
    dry_run: bool = typer.Option(False, "--dry-run",
        help="Print README to terminal without saving to file"),
    force: bool = typer.Option(False, "--force", "-f",
        help="Overwrite existing README.md without confirmation"),
    ai: bool = typer.Option(False, "--ai", "-a", "--grok",
        help="Use Grok AI to generate enhanced README"),
    auto_ai: bool = typer.Option(False, "--auto-ai",
        help="Auto-detect and use AI when API key is available"),
):
    console = Console()
    root = Path(path).resolve()
    
    if not root.exists():
        console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)
    
    if not root.is_dir():
        console.print(f"[red]Error:[/red] '{path}' is not a directory.")
        raise typer.Exit(code=1)
    
    config = load_config(str(root))
    
    if not template:
        template = usagetracker.get_project_last_template(str(root))
    
    if template:
        config["template"] = template
    if no_badges:
        config["include_badges"] = False
    config["max_tree_depth"] = depth
    
    if ai:
        config["ai_enabled"] = True
    if auto_ai:
        config["ai_enabled"] = True
    
    use_ai = config.get("ai_enabled", False) or auto_ai
    
    if use_ai:
        usagetracker.show_key_setup()
    
    output_path = root / output
    if output_path.exists() and not dry_run and not force:
        readme_info = usagetracker.get_project_readme_info(str(root))
        
        if readme_info.get("last_readme_mtime"):
            current_mtime = output_path.stat().st_mtime
            last_gen_time = readme_info.get("last_generate_time", 0)
            
            if current_mtime > last_gen_time:
                console.print(f"[yellow]Warning: README.md has been modified since last generation.[/yellow]")
                console.print("[dim]Use --force to overwrite or regenerate manually.[/dim]")
        
        overwrite = typer.confirm(f"'{output}' already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Scanning project...", total=None)
        scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
        
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
            except Exception as e:
                console.print(f"[yellow]AI generation failed: {e}, falling back to template[/yellow]")
                readme = generate_readme(scan, detection, config)
        else:
            progress.update(task, description="Generating README...")
            readme = generate_readme(scan, detection, config)
    
    if dry_run:
        console.print(Panel(readme, title="[cyan]README Preview[/cyan]", expand=False))
    else:
        save_readme(readme, str(output_path))
        
        usagetracker.save_project_cache(str(root), {"template": config.get("template", "standard")})
        usagetracker.save_project_readme_info(str(root), str(output_path))
        
        credits_msg = usagetracker.get_remaining_credits()
        
        console.print(Panel(
            f"[green]README generated![/green]\n\n"
            f"  Project  : [bold]{scan['name']}[/bold]\n"
            f"  Language : [bold]{detection['primary_lang']}[/bold]\n"
            f"  Type     : [bold]{detection['project_type']}[/bold]\n"
            f"  Template : [bold]{config['template']}[/bold]\n"
            f"  Saved to : [bold]{output_path}[/bold]\n\n"
            f"{credits_msg}",
            title="projectreadmegen",
            border_style="green",
        ))


@app.command()
def interactive(
    path: str = typer.Argument(".", help="Path to the project directory"),
    ai: bool = typer.Option(False, "--ai", "-a", "--grok",
        help="Use Grok AI to generate enhanced README"),
):
    """Interactive mode — answer questions to customize your README."""
    console = Console()
    console.print("[bold cyan]projectreadmegen — Interactive Mode[/bold cyan]\n")
    
    root = Path(path).resolve()
    config = load_config(str(root))
    
    if ai:
        usagetracker.show_key_setup()
        allowed, message = usagetracker.check_free_limit()
        
        if not allowed:
            can_continue = usagetracker.handle_exhausted()
            if not can_continue:
                raise typer.Exit(code=1)
        
        console.print("[yellow]Using AI to generate README...[/yellow]")
        scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
        detection = detect_stack(scan)
        readme = grok.generate_ai_readme(scan, detection, config)
    else:
        config["author"] = typer.prompt("Your name")
        config["github_username"] = typer.prompt("Your GitHub username")
        config["template"] = typer.prompt(
            "Template [minimal/standard/full/academic]", default="standard"
        )
        include_tree = typer.confirm("Include folder tree in README?", default=True)
        config["include_tree"] = include_tree
        
        scan = scan_directory(str(root), max_depth=config["max_tree_depth"])
        detection = detect_stack(scan)
        readme = generate_readme(scan, detection, config)
    
    output_path = root / config["output_file"]
    save_readme(readme, str(output_path))
    
    credits_msg = usagetracker.get_remaining_credits()
    
    console.print(Panel(
        f"[green]README generated![/green]\n\n"
        f"  Project  : [bold]{scan['name']}[/bold]\n"
        f"  Mode     : [bold]Interactive {'(AI)' if ai else '(Template)'}[/bold]\n"
        f"  Saved to : [bold]{output_path}[/bold]\n\n"
        f"{credits_msg}",
        title="projectreadmegen",
        border_style="green",
    ))


if __name__ == "__main__":
    main_menu_loop()

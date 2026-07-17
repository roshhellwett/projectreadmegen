![Repo Size](https://img.shields.io/github/repo-size/roshhellwett/projectreadmegen?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/roshhellwett/projectreadmegen?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/roshhellwett/projectreadmegen?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/roshhellwett/projectreadmegen?style=for-the-badge)
![Markdown](https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white)

# PROJECT README GEN

Auto-generate professional README files from folder structure with AI power.

![SAMPLE](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/sample.png)

---

## Overview

Point it at any project folder. It scans your directory structure, detects the tech stack, and generates a polished `README.md` — in seconds. v7.0.0 introduces the **Web UI Studio** — a browser-based interface with a FastAPI backend — plus a unified pipeline that all UI surfaces share.

**Three generation paths:**
- **Template-based** — 4 ready-made templates (minimal, standard, full, academic)
- **AI-powered** — connects to Groq API for intelligent, project-aware READMEs
- **Web UI Studio** — browser-based SPA with visual controls, real-time preview, and graph-based AI chat

---

## Features

- **Auto-detection** — identifies language, framework, license, project type, install/run commands
- **4 templates** — minimal, standard, full, academic — each with varying detail levels
- **AI generation** — uses Groq's LLM (llama-3.3-70b-versatile) for smart, contextual READMEs
- **Web UI Studio** — launch a full FastAPI web app with SPA frontend for browser-based README generation
- **Pipeline orchestration** — single canonical `pipeline.py` used by all UI surfaces (CLI, menu, Web API)
- **Interactive mode** — answers questions to customize output
- **GitHub Profile README** — generates profile READMEs with stats cards, language graphs, and style presets
- **CLI profile command** — generate GitHub Profile READMEs directly from the terminal (`projectreadmegen profile --username <user>`)
- **API key management** — manage Groq API keys and GitHub tokens via CLI (`config` command) or menu
- **System diagnostics** — real-time key status and quota inspection via `status` command
- **Multi-provider ready** — AI provider abstraction (`ai_provider.py`) designed to support multiple LLM backends
- **Badge support** — automatic language + license badges via shields.io
- **Folder tree** — includes an ASCII directory tree in your README
- **Safe writes** — atomic file writes via temp file + move, disk space checks, permission validation
- **Smart caching** — reuses previous scan results when project hasn't changed

---

## Installation

```bash
pip install projectreadmegen
```

Verify it installed correctly:

```bash
projectreadmegen --version
```

Or run via Python module:

```bash
python -m projectreadmegen --version
```

---

## Quick Start

### Generate a README for any project

```bash
# Navigate to your project
cd my-project

# Generate a README using the standard template
projectreadmegen generate .

# Generate with AI (requires API key — see setup below)
projectreadmegen generate . --ai
```

That's it. Your `README.md` is created in the current directory.

---

## Commands

All commands support `--help` for inline documentation.

### `generate` — Generate a README

The primary command. Scans a project directory and writes `README.md`.

```bash
projectreadmegen generate [PATH] [OPTIONS]
```

**Arguments:**

| Argument | Description | Default |
|---|---|---|
| `PATH` | Path to your project directory | `.` (current dir) |

**Options:**

| Flag | Description |
|---|---|
| `--template, -t` | Template: `minimal`, `standard`, `full`, `academic` |
| `--ai, -a, --grok` | Use Groq AI to generate the README |
| `--auto-ai` | Auto-use AI when API key is available |
| `--output, -o` | Output filename (default: `README.md`) |
| `--depth, -d` | Max folder tree depth (1–10, default: 3) |
| `--no-badges` | Disable shields.io badge generation |
| `--force, -f` | Overwrite existing README without confirmation |
| `--dry-run` | Print README to terminal, don't save to file |

**Examples:**

```bash
# Basic — standard template
projectreadmegen generate .

# Choose a template
projectreadmegen generate . --template full
projectreadmegen generate . -t minimal

# AI-powered README
projectreadmegen generate . --ai

# Include folder tree up to 5 levels deep
projectreadmegen generate . --depth 5

# Preview without saving
projectreadmegen generate . --dry-run --template full

# Custom output file
projectreadmegen generate . --output PROFILE.md

# Disable badges
projectreadmegen generate . --no-badges

# Overwrite existing README silently
projectreadmegen generate . --force

# All flags together
projectreadmegen generate ./my-project -t full --ai --depth 4 --no-badges --output README.md
```

### `interactive` — Interactive customization

Walks you through questions to customize the generated README.

```bash
projectreadmegen interactive [PATH] [OPTIONS]
```

**Options:**

| Flag | Description |
|---|---|
| `--ai, -a, --grok` | Use AI generation during interactive session |

**Example workflow:**

```bash
# Template-based interactive
projectreadmegen interactive .
# Asks for: your name, GitHub username, template choice, include tree?

# AI-powered interactive
projectreadmegen interactive . --ai
# Uses AI to generate, falls back to template if API key is missing
```

### `start` — Launch the interactive menu

Opens the full-featured menu system shown below in the [Interactive Menu](#interactive-menu) section.

```bash
projectreadmegen start
```

### `version` — Show version

```bash
projectreadmegen version
projectreadmegen --version
projectreadmegen -V
```

### `update` — Check and apply updates

```bash
projectreadmegen update
```

Checks PyPI for a newer version and upgrades automatically if one exists.

### `web` — Launch Web UI Studio

Starts the FastAPI web server with a full SPA frontend for browser-based README generation.

```bash
projectreadmegen web --port 8000 --host 127.0.0.1
```

**Options:**

| Flag | Description |
|---|---|
| `--port, -p` | Port to bind (default: `8000`) |
| `--host` | Host interface (default: `127.0.0.1`) |

Open `http://localhost:8000` in your browser to use the Studio.

### `profile` — Generate GitHub Profile README

Creates a profile README for your `github.com/<username>` repository directly from the terminal.

```bash
projectreadmegen profile --username roshhellwett --style professional
```

**Options:**

| Flag | Description |
|---|---|
| `--username, -u` | GitHub username (required) |
| `--style, -s` | Style preset: `basic`, `professional`, `stylish`, `unique` |
| `--output, -o` | Output directory or file path |
| `--token, -t` | Optional GitHub API token (overrides stored config) |

### `config` — Manage API keys and tokens

Set, inspect, or remove Groq API keys and GitHub tokens for both CLI and Web Studio.

```bash
# Set API key
projectreadmegen config --key gsk_your_key_here

# Set GitHub token
projectreadmegen config --token ghp_your_token_here

# Show current configuration
projectreadmegen config --show

# Remove credentials
projectreadmegen config --remove-key
projectreadmegen config --remove-token
```

### `status` — System diagnostics

Shows real-time diagnostic status, API key configuration, GitHub token status, and credits.

```bash
projectreadmegen status
```

---

## Interactive Menu

Run `projectreadmegen start` to open the menu:

```
┌──────────────────────────────────────────────┐
│     PROJECT README GEN STUDIO v7.0.0          │
│   Architectural Documentation & Web Suite     │
│                                              │
│  Select an execution mode:                   │
│                                              │
│  1  Create README with AI Architecture        │
│  2  Create Normal README (Deterministic)      │
│  3  Manage API Key & Credentials              │
│  4  View Quota & System Diagnostics           │
│  5  Update Package Version                   │
│  6  Help & Command Reference                 │
│  7  Create GitHub Profile README              │
│  8  Launch Web UI Studio                     │
│  9  Exit Suite                               │
└──────────────────────────────────────────────┘
```

### Option 1 — Create README with AI
1. Choose mode: `1` (quick generate) or `2` (interactive)
2. Enter project path (or press Enter for current dir)
3. If no API key is detected, you'll be prompted to add one
4. README is generated via Groq AI (llama-3.3-70b-versatile) and saved

### Option 2 — Create Normal README
1. Choose mode: `1` (quick generate) or `2` (interactive)
2. In interactive mode you can customize: author name, GitHub username, template, and whether to include the folder tree
3. README is generated from templates and saved

### Option 3 — Manage API Key & Credentials
- **If no key configured:** Add your own Groq API key or manage a GitHub token
- **If key configured:** Update, remove, or manage GitHub token
- API keys must start with `gsk_` and are stored locally in `%APPDATA%\projectreadmegen\` (Windows) or `~/.projectreadmegen/`
- GitHub tokens are optional but enable higher API rate limits (5,000 req/hr)

### Option 4 — View Quota & System Diagnostics
Shows real-time Groq API key status, GitHub token status, storage path, and quota information.

### Option 5 — Update
Same as the `update` command — checks PyPI for the latest version.

### Option 6 — Help & Command Reference
Quick reference of all CLI commands, flags, and environment setup.

### Option 7 — Create GitHub Profile README
See dedicated section below.

### Option 8 — Launch Web UI Studio
Starts the FastAPI web server and opens the browser-based SPA for visual README generation, scanning, and profile creation.

### Option 9 — Exit Suite
Exits the menu.

---

## Web UI Studio

v7.0.0 introduces a full FastAPI web server with a packaged single-page application (SPA) frontend.

**Access via:** Menu option `8` or the `web` CLI command.

```bash
projectreadmegen web --port 8000
# Open http://localhost:8000 in your browser
```

### What it does:
1. Starts a FastAPI server on `localhost:8000`
2. Serves the Obsidian-based SPA frontend from `web_dist/`
3. Provides REST API endpoints for all README generation features
4. Supports graph-based chat with AI context for code exploration

### API Endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Server status, version, key configuration |
| `/api/scan` | POST | Scan a project directory and detect tech stack |
| `/api/generate` | POST | Generate template-based README |
| `/api/generate-ai` | POST | Generate AI-powered README via Groq |
| `/api/profile` | POST | Generate GitHub Profile README |
| `/api/key` | POST | Set/update Groq API key |
| `/api/skills` | GET | List available OpenCode skills |
| `/api/graph-chat` | POST | AI chat with graph and code context |
| `/` | GET | Serves the SPA frontend |

**Note:** The API is designed for local development only. No authentication is enforced.

---

## GitHub Profile README

Generates a README for your `github.com/<username>` profile repository.

**Access via:** Menu option `7`, CLI `profile` command, or programmatically through the `github_profile` module.

### What it does:
1. Asks for your GitHub username and profile URL
2. Fetches your profile data, repositories, and language stats via the GitHub API
3. Lets you choose a style
4. Generates an AI-powered profile README using Groq

### Styles:

| # | Style | Description |
|---|---|---|
| 1 | **Basic** | Clean, minimal, professional |
| 2 | **Professional** | Career-focused with detailed sections |
| 3 | **Stylish** | Stats cards, typing effects, badges |
| 4 | **Unique** | Most detailed, creative, and eye-catching |

### Example flow:

```bash
# Via CLI (v7.0.0+)
projectreadmegen profile --username roshhellwett --style professional

# Via menu
projectreadmegen start
# Select option 7, enter username, choose style

# The tool:
# 1. Validates the GitHub username
# 2. Fetches profile data from api.github.com
# 3. Aggregates language stats across all repos
# 4. Generates README with shields.io badges and stats cards
# 5. Saves to ./<username>/README.md
```

> **Note:** Requires a Groq API key. A GitHub token is optional but enables richer data (all repos, accurate stats, 5,000 req/hr rate limit).

---

## API Key Setup

AI features require a free Groq API key.

### Get your key:
1. Visit [console.groq.com/keys](https://console.groq.com/keys)
2. Click **Create Key**
3. Copy the key (starts with `gsk_`)

### Set it:

**Via the menu:**
```bash
projectreadmegen start
# Select option 3 → Add Your Own API Key
```

**Via environment variable (recommended for scripts):**
```bash
# PowerShell
$env:GROQ_API_KEY = "gsk_your_key_here"

# CMD
set GROQ_API_KEY=gsk_your_key_here
```

The key is stored locally and used for all AI features (README generation, GitHub Profile README).

---

## Templates

| Template | Best For | Sections |
|---|---|---|
| **minimal** | Small utilities, scripts | Title, description, install, usage, license |
| **standard** | Most projects | Overview, prerequisites, install, usage, structure, tests, contributing, license |
| **full** | Major applications | Table of contents, features grid, tech stack table, install/usage with copy-ready commands, structure, tests with coverage, contributing, license, footer |
| **academic** | Coursework, research | About, objectives checklist, install, run, file structure, concepts, author |

```bash
# Specify a template
projectreadmegen generate . --template academic
projectreadmegen generate . -t full
```

The last-used template per project is remembered (stored in the local cache).

---

## Configuration

Create a `readmegen.config.json` in your project root to set persistent defaults:

```json
{
  "template": "standard",
  "output_file": "README.md",
  "include_tree": true,
  "max_tree_depth": 3,
  "include_badges": true,
  "ai_enabled": false,
  "ai_provider": "groq",
  "author": "",
  "github_username": "your-username"
}
```

**Available keys:**

| Key | Type | Default | Description |
|---|---|---|---|---|
| `template` | string | `"standard"` | Default template name |
| `output_file` | string | `"README.md"` | Output filename |
| `include_tree` | bool | `true` | Include folder tree in README |
| `max_tree_depth` | int | `3` | Maximum tree depth (1–10) |
| `include_badges` | bool | `true` | Show shields.io badges |
| `ai_enabled` | bool | `false` | Always use AI generation |
| `ai_provider` | string | `"groq"` | AI provider backend |
| `groq_api_key` | string | `""` | Groq API key for AI features |
| `author` | string | `""` | Author name for generated README |
| `github_username` | string | `""` | GitHub username for repo links |

---

## Error Handling

projectreadmegen handles common errors gracefully:

| Scenario | Behavior |
|---|---|
| Path does not exist | Clear error message, exit code 1 |
| Path is a file, not a directory | Clear error message, exit code 1 |
| No read permission | Permission error with actionable guidance |
| API key missing | Prompts to add one, falls back to template generation |
| AI generation fails | Automatically falls back to template-based generation |
| API rate limited | Exponential backoff with retries (up to 3), then clear error |
| Disk space low | Writes prevented with space requirement info |
| Invalid config JSON | Error message with JSON syntax details |

---

## Examples

### Generate README for a Python project

```bash
cd my-python-project
projectreadmegen generate . --template full
# Output: ./README.md with title, description, install/run commands, folder tree
```

### Generate README for a web app

```bash
projectreadmegen generate ./react-app --template full --depth 5
# Detects: React, TypeScript, npm
# Includes: tech stack table, full feature list, folder tree
```

### Preview before saving

```bash
projectreadmegen generate . --dry-run --template standard
# Prints the generated README to the terminal
```

### AI-powered (with API key)

```bash
projectreadmegen generate . --ai
# Sends project context to Groq API, receives a customized README
```

---

## Project Structure

```
projectreadmegen/
├── src/
│   └── projectreadmegen/
│       ├── __init__.py          # Version info (v7.0.0)
│       ├── __main__.py          # Entry: python -m projectreadmegen
│       ├── ai_provider.py       # Groq AI client (OpenAI-compatible, multi-provider ready)
│       ├── badges.py            # shields.io badge generation
│       ├── cli.py               # CLI commands, menu system, all entry points
│       ├── config.py            # Language patterns, skip lists, defaults (legacy)
│       ├── constants.py         # Centralized constants (LANG_PATTERNS, SKIP_DIRS, etc.)
│       ├── detector.py          # Language, license, project type detection
│       ├── exceptions.py        # Custom exception hierarchy
│       ├── generator.py         # Template rendering + file writing
│       ├── github_profile.py    # GitHub profile README generation
│       ├── grok.py              # Backward-compat re-exports from ai_provider
│       ├── pipeline.py          # Single pipeline: scan → detect → generate → save
│       ├── scanner.py           # Directory traversal + caching
│       ├── server.py            # FastAPI web server + REST API
│       ├── skills_manager.py    # OpenCode skills discovery and management
│       ├── usagetracker.py      # API key storage, usage tracking, unified status
│       ├── utils.py             # Path validation, symlink checks, disk space
│       ├── web_dist/            # Packaged SPA frontend for Web Studio
│       │   ├── index.html
│       │   ├── favicon.png
│       │   └── assets/
│       └── templates/
│           ├── minimal.md.j2
│           ├── standard.md.j2
│           ├── full.md.j2
│           └── academic.md.j2
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/                   # Component-level unit tests
│   │   ├── test_ai_provider.py
│   │   ├── test_badges.py
│   │   ├── test_cli_commands.py
│   │   ├── test_config.py
│   │   ├── test_constants.py
│   │   ├── test_detector.py
│   │   ├── test_exceptions.py
│   │   ├── test_generator.py
│   │   ├── test_github_profile.py
│   │   ├── test_pipeline.py
│   │   ├── test_scanner.py
│   │   ├── test_server.py
│   │   ├── test_skills_manager.py
│   │   └── test_usagetracker.py
│   ├── smoke/                  # Rapid smoke sanity tests
│   │   └── test_smoke.py
│   └── e2e/                    # Full lifecycle end-to-end tests
│       ├── test_e2e_cli.py
│       └── test_e2e_web.py
├── examples/                   # Sample projects for testing detection
├── pyproject.toml
├── readmegen.config.json
└── readme.md
```

---
© 2026 [Zenith Open Source Projects](https://zenithopensourceprojects.vercel.app/). All Rights Reserved. Zenith is a Open Source Project Idea's by [@roshhellwett](https://github.com/roshhellwett)

![Repo Size](https://img.shields.io/github/repo-size/roshhellwett/projectreadmegen?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/roshhellwett/projectreadmegen?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/roshhellwett/projectreadmegen?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/roshhellwett/projectreadmegen?style=for-the-badge)
![Markdown](https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white)

# PROJECT README GEN

**Auto-generate state-of-the-art documentation, AI-powered project architectures, interactive graph models, and GitHub profile masterpieces — in seconds.**

![Web UI Studio](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/sampleone.png?raw=true)

---

## Overview

Writing comprehensive, professional documentation by hand takes hours. **Project README Gen** transforms how developers document software. Point it at any repository path (`.`), and it instantly scans your directory, detects your programming languages, frameworks, build engines, and licenses, and generates a structured, publication-ready `README.md`.

Whether you prefer one-line terminal automation, interactive guided questionnaires, or a sleek glassmorphic **Web UI Studio** in your browser, **Project README Gen** delivers identical, high-fidelity results backed by a unified architectural pipeline.

---

## Why Project README Gen? (Benefits & How It Helps You)

### 🚀 Zero-Friction Documentation
Stop spending hours formatting tables, writing installation prerequisites, and organizing sections. Project README Gen automates the entire boilerplate so you can focus on building code while maintaining world-class repository standards.

### 🧠 Intelligent Tech-Stack & Dependency Detection
Never manually type your dependencies or prerequisites again. The deep scanner automatically identifies:
- **Languages**: Python, JavaScript/TypeScript, Go, Rust, Java, C++, Ruby, PHP, and more.
- **Package Managers**: `pip`, `poetry`, `npm`, `yarn`, `pnpm`, `cargo`, `go modules`.
- **Frameworks & Build Tools**: React, Next.js, FastAPI, Django, Flask, Vite, Docker.
- **Licenses**: MIT, Apache-2.0, GPL-3.0, BSD, or proprietary detections.

### 🤖 Groq AI Architect (`llama-3.3-70b-versatile`)
Unlike generic templates, our integrated AI Architect synthesizes your exact codebase context. It reads your project structure and generates custom architectural explanations, module descriptions, and usage instructions with unmatched precision and speed.

### 🎨 Multi-Surface Workflow
Work exactly how you want across three dedicated interfaces:
1. **Web UI Studio**: A modern browser SPA with real-time markdown previewing, template switching, and AI co-pilot chat.
2. **Terminal CLI**: Fast, scriptable commands perfect for CI/CD pipelines, Git pre-commit hooks, and rapid terminal workflows.
3. **Interactive TUI Suite**: An intuitive terminal menu system that guides you through generation without remembering any syntax.

### 🛡️ Atomic & Safe Execution
Your existing files are protected. All documentation is built via atomic temporary file writing, comprehensive disk space validation, and permission checks to guarantee zero data loss.

### 🌟 GitHub Profile Mastery
Stand out to recruiters and peers. Instantly generate custom `github.com/<username>` profile repositories complete with animated typing taglines, live shields, multi-language breakdown cards, and visual theme presets (`professional`, `stylish`, `unique`, `basic`).

---

## Installation

Install directly from PyPI via `pip`:

```bash
pip install projectreadmegen
```

Verify your installation and inspect the CLI:

```bash
projectreadmegen --version
```

*Note: You can also invoke the module directly via `python -m projectreadmegen`.*

---

## How to Use (3 Execution Paths)

### 1. Web UI Studio (Browser SPA)
Launch the visual browser studio with real-time markdown rendering, AI controls, and interactive graph exploration:

```bash
projectreadmegen web --port 8000
```
Then open `http://localhost:8000` in any web browser to access the studio.

### 2. Terminal CLI (Direct Commands)
Run instant one-line commands directly inside your target project folder:

```bash
# Navigate to your repository
cd my-awesome-app

# Generate documentation using the 'full' template
projectreadmegen generate . --template full

# Generate an intelligent, AI-powered README
projectreadmegen generate . --ai
```

### 3. Interactive Suite (TUI Menu)
Launch the full terminal navigation suite for guided, step-by-step documentation generation:

```bash
projectreadmegen start
```

---

## Studio Gallery & Sample Previews

Here is a look at what Project README Gen builds across our Web Studio and generated output samples:

### Project Scanner & Detection Studio
![Project Scanner](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/sampleone.png?raw=true)

### README Template & Live Preview Studio
![README Studio](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/sampletwo.png?raw=true)

### AI Architect & Interactive Graph Studio
![AI Architect Studio](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/samplethree.png?raw=true)

### GitHub Profile Studio
![GitHub Profile Studio](https://github.com/roshhellwett/projectreadmegen/blob/main/Sample/samplefour.png?raw=true)

---

## All Commands & Their Usage

Every command supports `--help` for comprehensive inline documentation right inside your terminal.

### `generate` — Create Project Documentation
The core command of the suite. Scans a directory, detects technologies, applies templates or AI models, and writes the `README.md`.

```bash
projectreadmegen generate [PATH] [OPTIONS]
```

**Arguments:**
- `PATH` — Target project root directory (`.` by default).

**Options:**
| Option | Description |
|---|---|
| `-t, --template` | Choose template preset: `minimal`, `standard`, `full`, `academic` (Default: `standard`). |
| `-a, --ai, --grok` | Enable Groq AI (`llama-3.3-70b`) for intelligent, project-aware documentation. |
| `--auto-ai` | Automatically use AI if an API key is configured; otherwise fallback to template cleanly. |
| `-o, --output` | Custom output filename (Default: `README.md`). |
| `--depth, -d` | Maximum folder depth to analyze during scan (`1` to `10`, Default: `3`). |
| `--no-badges` | Disable automatic shields.io header badge generation. |
| `-f, --force` | Overwrite existing README without confirmation prompts. |
| `--dry-run` | Render and display the generated README in your terminal without saving to disk. |

**Practical Examples:**
```bash
# Basic generation with standard template
projectreadmegen generate .

# Generate an academic/research project README
projectreadmegen generate . --template academic

# Generate using Groq AI and write to custom file
projectreadmegen generate . --ai --output ARCHITECTURE.md

# Preview a full template cleanly in terminal without saving
projectreadmegen generate . -t full --dry-run
```

---

### `interactive` — Guided Q&A Customization
Walks you through an interactive terminal session to customize author names, repository details, badge selections, and section preferences before building.

```bash
projectreadmegen interactive [PATH] [OPTIONS]
```

**Options:**
| Option | Description |
|---|---|
| `-a, --ai, --grok` | Enable AI synthesis during the interactive questionnaire. |

**Practical Examples:**
```bash
# Start interactive walkthrough for current folder
projectreadmegen interactive .

# Guided walkthrough with AI enhancements
projectreadmegen interactive . --ai
```

---

### `start` — Launch TUI Interactive Suite
Opens the full interactive navigation menu inside your terminal window.

```bash
projectreadmegen start
```

**Menu Options Available:**
1. **Create README with AI Architecture** — Fast or interactive AI generation.
2. **Create Normal README (Deterministic)** — Fast or interactive template generation.
3. **Manage API Key & Credentials** — Set Groq API keys and optional GitHub personal access tokens.
4. **View Quota & System Diagnostics** — Check real-time API connectivity and rate limits.
5. **Update Package Version** — Self-upgrade to the latest release from PyPI.
6. **Help & Command Reference** — Display syntax manuals.
7. **Create GitHub Profile README** — Build customized developer profile repositories.
8. **Launch Web UI Studio** — Start the local web server and open the browser studio.
9. **Exit Suite** — Clean exit.

---

### `web` — Launch Web UI Studio
Starts the FastAPI backend server and serves the single-page application (SPA) frontend.

```bash
projectreadmegen web [OPTIONS]
```

**Options:**
| Option | Description |
|---|---|
| `-p, --port` | Port number to bind the server (`8000` by default). |
| `--host` | Network host interface (`127.0.0.1` by default). |

**Practical Examples:**
```bash
# Launch on default port 8000
projectreadmegen web

# Launch on custom port 3000 accessible across local network
projectreadmegen web --port 3000 --host 0.0.0.0
```

---

### `profile` — Generate GitHub Profile README
Crafts a dynamic profile README for your `github.com/<username>` repository complete with shields, stats cards, and language breakdown meters directly from your shell.

```bash
projectreadmegen profile [OPTIONS]
```

**Options:**
| Option | Description |
|---|---|
| `-u, --username` | **(Required)** Your GitHub target username. |
| `-s, --style` | Visual preset: `basic`, `professional`, `stylish`, `unique` (Default: `professional`). |
| `-o, --output` | Output directory or custom file destination. |
| `-t, --token` | GitHub API personal access token (Optional for higher API rate limits). |

**Practical Examples:**
```bash
# Create a professional profile README
projectreadmegen profile --username roshhellwett --style professional

# Create a stylish bento-card profile and save to local folder
projectreadmegen profile --username roshhellwett --style stylish --output ./profile/README.md
```

---

### `config` — Manage API Keys and Credentials
Securely store, update, or remove credentials required for AI generation (`Groq API Key`) and extended GitHub stats (`GitHub Token`). Credentials are saved safely inside your local application directory (`%APPDATA%/projectreadmegen` on Windows or `~/.projectreadmegen/` on macOS/Linux).

```bash
projectreadmegen config [OPTIONS]
```

**Options:**
| Option | Description |
|---|---|
| `--key` | Set and save your Groq API key (starts with `gsk_`). |
| `--token` | Set and save your GitHub personal access token (starts with `ghp_`). |
| `--show` | Display currently configured credentials and masked tokens. |
| `--remove-key` | Delete the saved Groq API key from your system. |
| `--remove-token` | Delete the saved GitHub personal access token from your system. |

**Practical Examples:**
```bash
# Save your Groq API key for AI generation
projectreadmegen config --key gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Check stored credentials status
projectreadmegen config --show
```

---

### `status` — Real-Time Quota & System Diagnostics
Performs a live system check, inspects Groq API connectivity, checks remaining rate limit credits, verifies GitHub token permissions, and outputs storage paths.

```bash
projectreadmegen status
```

---

### `update` — Self-Upgrade from PyPI
Checks the official Python Package Index (PyPI) for newer versions of `projectreadmegen` and performs an in-place upgrade automatically.

```bash
projectreadmegen update
```

---

### `version` — Display Version Info
Outputs the active build version and environment details.

```bash
projectreadmegen version
# Also accessible via:
projectreadmegen --version
projectreadmegen -V
```

---

## Built-In Templates & Customization

Project README Gen ships with 4 carefully structured documentation templates tailored for different project scales:

| Template | Ideal For | Key Sections Included |
|---|---|---|
| `minimal` | Single scripts, utilities, microservices | Title, Badges, Quick Description, Installation, Usage, License. |
| `standard` | General applications, libraries, APIs | Overview, Prerequisites, Installation, Usage, Running Tests, Contributing, License. |
| `full` | Enterprise projects, major frameworks | Table of Contents, Features Grid, Tech Stack Table, Detailed Installation & Usage, Folder Tree, Test Coverage, Contributing Guidelines, License, Footer. |
| `academic` | Research papers, university coursework | Abstract/About, Research Objectives Checklist, Requirements, Execution Setup, System Architecture & Concepts, Author Attribution. |

### Persistent Configuration (`readmegen.config.json`)
To set project-specific defaults without passing CLI flags every time, create a `readmegen.config.json` inside your project root:

```json
{
  "template": "full",
  "output_file": "README.md",
  "include_tree": false,
  "max_tree_depth": 3,
  "include_badges": true,
  "ai_enabled": true,
  "ai_provider": "groq",
  "author": "Rosh Hellwett",
  "github_username": "roshhellwett"
}
```

---

## Groq AI Setup (Free API Key)

To unlock AI-powered README architecture and intelligent repository analysis, grab a free Groq API key:
1. Visit [console.groq.com/keys](https://console.groq.com/keys) and sign in.
2. Click **Create API Key** and copy your key (`gsk_...`).
3. Configure it using either of these methods:
   ```bash
   # Via CLI
   projectreadmegen config --key gsk_your_api_key_here

   # Or via environment variable in your shell/CI
   export GROQ_API_KEY="gsk_your_api_key_here"
   ```

---

© 2026 [Zenith Open Source Projects](https://zenithopensourceprojects.vercel.app/). All Rights Reserved. Zenith is an Open Source Project Idea by [@roshhellwett](https://github.com/roshhellwett).

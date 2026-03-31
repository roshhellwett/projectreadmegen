![Repo Size](https://img.shields.io/github/repo-size/roshhellwett/projectreadmegen?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/roshhellwett/projectreadmegen?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/roshhellwett/projectreadmegen?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/roshhellwett/projectreadmegen?style=for-the-badge)
![Markdown](https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white)

# PROJECT README GEN

Auto-generate README files from folder structure with optional AI enhancement using Groq API.

![SAMPLE](https://github.com/roshhellwett/projectreadmegen/blob/6ea4f99fbcdba0531e59835f7f492329fbefaab0/Sample/sample.png)

## Installation

```bash
pip install projectreadmegen

OR

PyPi - (https://pypi.org/project/projectreadmegen)
```

## Quick Start

```bash
# Run directly with Python
python -m projectreadmegen generate .

# Or add to PATH for convenience
set PATH=%PATH%;%APPDATA%\Python\Python314\Scripts

# Then use simple command
projectreadmegen generate .
```

## Usage

### Generate README (Quick Mode)

```bash
# Basic - template-based
python -m projectreadmegen generate .

# With AI enhancement
python -m projectreadmegen generate . --ai
python -m projectreadmegen generate . -a

# Auto-detect AI when API key available
python -m projectreadmegen generate . --auto-ai
```

### Interactive Mode

```bash
# Start menu
python -m projectreadmegen

# Or CLI-based interactive
python -m projectreadmegen interactive .
python -m projectreadmegen interactive . --ai
```

### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--template` | `-t` | Template: minimal, standard, full, academic |
| `--output` | `-o` | Output filename (default: README.md) |
| `--depth` | `-d` | Tree depth (default: 3) |
| `--ai` | `-a`, `--grok` | Use Groq AI for enhanced README |
| `--auto-ai` | | Auto-use AI when API key available |
| `--force` | `-f` | Overwrite without confirmation |
| `--dry-run` | | Preview without saving |
| `--no-badges` | | Disable badge generation |
| `--version` | `-V` | Show version |

### Commands

| Command | Description |
|---------|-------------|
| `generate` | Generate README from folder |
| `interactive` | Interactive Q&A mode |
| `start` | Start interactive menu |
| `update` | Check and install updates |
| `version` | Show version info |

## Menu Mode

Run `python -m projectreadmegen` for interactive menu:

```
1  Create README with AI
2  Create Normal README (template-based)
3  Manage API Key
4  View Credits Status
5  Update projectreadmegen
6  Help & Commands
7  Exit
```

## Configuration

Create `readmegen.config.json` in project root:

```json
{
    "template": "standard",
    "ai_enabled": true,
    "groq_api_key": "your_key_here",
    "include_badges": true,
    "include_tree": true,
    "max_tree_depth": 3,
    "output_file": "README.md"
}
```

## API Key

Get free Groq API key: https://console.groq.com/keys

```bash
# Set environment variable
export GROQ_API_KEY=your_key_here

# Windows
$env:GROQ_API_KEY="your_key_here"
```

## Features

- **Auto-detect** - Project type and tech stack detection
- **Folder Tree** - ASCII tree visualization
- **AI Generation** - Groq-powered enhanced README
- **4 Templates** - minimal, standard, full, academic
- **Badges** - Auto language and license badges
- **Smart Caching** - Faster repeated scans
- **Template Memory** - Remembers last template per project
- **Update Detection** - Warns if README modified externally
- **Credit System** - 5 free AI uses/day (then use your own key)

## Credits

- 5 free AI uses per day
- Add your own Groq API key for unlimited use
- Data stored in `%APPDATA%\projectreadmegen\`

---

© 2026 [Zenith Open Source Projects](https://zenithopensourceprojects.vercel.app/). All Rights Reserved. Zenith is a Open Source Project Idea's by @roshhellwett

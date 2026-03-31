# src/detector.py

import logging
from pathlib import Path
from projectreadmegen.config import LANG_PATTERNS, LICENSE_NAMES

logger = logging.getLogger(__name__)


def detect_stack(scan_result: dict) -> dict:
    """
    Analyze scan result and detect languages, license, and project type.

    Parameters:
        scan_result (dict): Output from scanner.scan_directory().

    Returns:
        dict: {
            "languages":     list[str] — detected languages in priority order,
            "primary_lang":  str — most likely main language,
            "license":       str — license identifier or "None",
            "project_type":  str — one of: "library", "cli-tool", "web-app",
                                   "telegram-bot", "game", "script", "unknown",
            "description_hint": str — one sentence hint for README description,
            "has_tests":     bool,
            "has_docs":      bool,
            "install_cmd":   str — likely install command,
            "run_cmd":       str — likely run command,
        }
    """
    files = scan_result["files"]
    dirs  = scan_result["dirs"]
    exts  = scan_result["file_extensions"]
    name  = scan_result["name"]
    
    logger.debug(f"Detecting stack for project: {name}")
    
    languages   = _detect_languages(files, exts)
    primary     = languages[0] if languages else "Unknown"
    license_id  = _detect_license(files, scan_result["root"])
    proj_type   = _detect_project_type(files, dirs, languages, name)
    desc_hint   = _build_description_hint(name, primary, proj_type)
    install_cmd = _detect_install_command(files, primary)
    run_cmd     = _detect_run_command(files, dirs, primary, proj_type)
    
    logger.info(f"Detected: {primary} ({proj_type})")
    
    return {
        "languages":        languages,
        "primary_lang":     primary,
        "license":          license_id,
        "project_type":     proj_type,
        "description_hint": desc_hint,
        "has_tests":        any(d in dirs for d in ["tests", "test", "__tests__", "spec"]),
        "has_docs":         any(d in dirs for d in ["docs", "doc", "documentation"]),
        "install_cmd":      install_cmd,
        "run_cmd":          run_cmd,
    }


def _detect_languages(files: list, extensions: list) -> list:
    """
    Detect languages from files and extensions, returns sorted by confidence.
    """
    scores = {}
    
    for lang, patterns in LANG_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if pattern.startswith("*."):
                ext = pattern[1:]
                if ext in extensions:
                    score += 2
            else:
                if pattern in files:
                    score += 5
        
        if score > 0:
            scores[lang] = score
    
    return sorted(scores.keys(), key=lambda l: scores[l], reverse=True)


def _detect_license(files: list, root: str) -> str:
    """
    Detect license type from license files.
    """
    for fname in files:
        if fname.upper() in [f.upper() for f in LICENSE_NAMES.keys()]:
            try:
                license_path = Path(root) / fname
                with open(license_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().upper()
                
                if "MIT" in first_line:
                    return "MIT"
                elif "APACHE" in first_line:
                    return "Apache-2.0"
                elif "GNU GENERAL PUBLIC" in first_line:
                    return "GPL-3.0"
                elif "BSD" in first_line:
                    return "BSD-3-Clause"
                else:
                    return "See LICENSE"
            except (IOError, UnicodeDecodeError):
                return "See LICENSE"
    
    return "None"


def _detect_project_type(files: list, dirs: list, languages: list, name: str) -> str:
    """
    Classify project type based on files, dirs, and detected languages.
    """
    name_lower = name.lower()
    
    if any(f in files for f in ["bot.py", "main.py"]) and "Python" in languages:
        if any(kw in name_lower for kw in ["bot", "telegram", "monolith"]):
            return "telegram-bot"
    
    if any(f in files for f in ["package.json", "index.html", "tsconfig.json"]):
        if any(d in dirs for d in ["src", "public", "pages", "components"]):
            return "web-app"
    
    if any(f in files for f in ["cli.py", "main.py", "setup.py", "pyproject.toml"]):
        if "Python" in languages:
            return "cli-tool"
    
    if "CMakeLists.txt" in files or "Makefile" in files:
        if "C++" in languages:
            return "cli-tool"
    
    if any(f.endswith(".sh") or f.endswith(".ps1") for f in files):
        return "script"
    
    if any(kw in name_lower for kw in ["game", "numsuko", "logic"]):
        return "game"
    
    return "unknown"


def _build_description_hint(name: str, lang: str, proj_type: str) -> str:
    """
    Build a one-sentence description template based on detected metadata.
    """
    type_phrases = {
        "telegram-bot": f"A Telegram bot built with {lang}",
        "web-app":      f"A web application built with {lang}",
        "cli-tool":     f"A command-line tool written in {lang}",
        "game":         f"An interactive game written in {lang}",
        "script":       f"A collection of automation scripts",
        "library":      f"A {lang} library",
        "unknown":      f"A {lang} project",
    }
    
    phrase = type_phrases.get(proj_type, f"A {lang} project")
    return f"{phrase} — {name.replace('-', ' ').replace('_', ' ').title()}."


def _detect_install_command(files: list, primary_lang: str) -> str:
    """
    Return the most likely install command based on detected stack.
    """
    if "requirements.txt" in files:
        return "pip install -r requirements.txt"
    elif "pyproject.toml" in files:
        return "pip install ."
    elif "package.json" in files:
        return "npm install"
    elif "Cargo.toml" in files:
        return "cargo build"
    elif "CMakeLists.txt" in files:
        return "cmake -B build && cmake --build build"
    elif "Makefile" in files:
        return "make"
    else:
        return "# See setup instructions below"


def _detect_run_command(files: list, dirs: list, primary_lang: str, proj_type: str) -> str:
    """
    Return the most likely run command.
    """
    if proj_type == "cli-tool" and "cli.py" in files:
        return "python cli.py"
    elif proj_type == "cli-tool" and "main.py" in files:
        return "python main.py"
    elif proj_type == "telegram-bot":
        return "python bot.py"
    elif proj_type == "web-app" and "package.json" in files:
        return "npm run dev"
    elif "CMakeLists.txt" in files:
        return "./build/projectname"
    elif "Makefile" in files:
        return "make run"
    else:
        return "# See usage section below"


if __name__ == "__main__":
    import sys
    from src.scanner import scan_directory
    
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    scan  = scan_directory(path, max_depth=3)
    detec = detect_stack(scan)
    
    print(f"Languages : {detec['languages']}")
    print(f"Primary   : {detec['primary_lang']}")
    print(f"Type      : {detec['project_type']}")
    print(f"License   : {detec['license']}")
    print(f"Install   : {detec['install_cmd']}")
    print(f"Run       : {detec['run_cmd']}")
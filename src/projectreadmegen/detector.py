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
            "languages":     list[str],
            "primary_lang":  str,
            "license":       str,
            "project_type":  str,
            "description_hint": str,
            "has_tests":     bool,
            "has_docs":      bool,
            "install_cmd":   str,
            "run_cmd":       str,
        }
    """
    files = scan_result["files"]
    dirs = scan_result["dirs"]
    exts = scan_result["file_extensions"]
    name = scan_result["name"]
    root = scan_result["root"]

    logger.debug(f"Detecting stack for project: {name}")

    languages = _detect_languages(files, exts)
    primary = languages[0] if languages else "Unknown"
    license_id = _detect_license(files, root)
    proj_type = _detect_project_type(files, dirs, languages, exts, name)
    desc_hint = _build_description_hint(name, primary, proj_type)
    install_cmd = _detect_install_command(files, primary)
    run_cmd = _detect_run_command(files, dirs, primary, proj_type)

    logger.info(f"Detected: {primary} ({proj_type})")

    return {
        "languages": languages,
        "primary_lang": primary,
        "license": license_id,
        "project_type": proj_type,
        "description_hint": desc_hint,
        "has_tests": any(d in dirs for d in ["tests", "test", "__tests__", "spec"]),
        "has_docs": any(d in dirs for d in ["docs", "doc", "documentation"]),
        "install_cmd": install_cmd,
        "run_cmd": run_cmd,
    }


def _detect_languages(files: list, extensions: list) -> list:
    """Detect languages from files and extensions, sorted by confidence."""
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
    """Detect license type by checking known license files and scanning first 5 lines."""
    license_identifiers = {
        "MIT": ["MIT", "Permission is hereby granted, free of charge"],
        "Apache-2.0": ["Apache License", "Apache Software License"],
        "GPL-3.0": ["GNU GENERAL PUBLIC LICENSE", "GNU General Public License"],
        "GPL-2.0": [
            "GNU GENERAL PUBLIC LICENSE Version 2",
            "GNU General Public License, version 2",
        ],
        "BSD-3-Clause": ["Redistribution and use in source and binary", "BSD"],
        "BSD-2-Clause": ["BSD"],
        "MPL-2.0": ["Mozilla Public License"],
        "AGPL-3.0": ["GNU AFFERO GENERAL PUBLIC"],
        "LGPL-3.0": ["GNU LESSER GENERAL PUBLIC"],
        "Unlicense": ["This is free and unencumbered software"],
    }

    license_names_upper = [f.upper() for f in LICENSE_NAMES.keys()]

    for fname in files:
        if fname.upper() in license_names_upper:
            try:
                license_path = Path(root) / fname
                with open(license_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = ""
                    for _ in range(5):
                        content += f.readline().upper()

                for lic_id, keywords in license_identifiers.items():
                    if any(kw.upper() in content for kw in keywords):
                        return lic_id
            except (IOError, OSError):
                continue

    if any(f.upper() in license_names_upper for f in files):
        return "See LICENSE"

    return "None"


def _detect_project_type(
    files: list, dirs: list, languages: list, extensions: list, name: str
) -> str:
    """Classify project type based on files, dirs, languages, and extensions."""
    name_lower = name.lower()

    # API / web framework
    web_frameworks = {
        "Django",
        "Flask",
        "FastAPI",
        "React",
        "Next",
        "Angular",
        "Vue",
        "Express",
    }
    if any(f in files for f in ["app.py", "manage.py", "wsgi.py", "asgi.py"]):
        return "web-app"
    if any(f in files for f in ["package.json", "index.html", "tsconfig.json"]):
        if any(d in dirs for d in ["src", "public", "pages", "components", "app"]):
            return "web-app"
    if any(
        f in files
        for f in ["vite.config", "next.config", "nuxt.config", "tailwind.config"]
    ):
        return "web-app"
    if "webpack.config.js" in files or "next.config.js" in files:
        return "web-app"

    # Bot
    if any(f in files for f in ["bot.py", "telegram_bot.py"]) and "Python" in languages:
        return "telegram-bot"

    # Library
    has_init = "__init__.py" in files or "lib.rs" in files or "mod.rs" in files
    has_no_main = not any(
        f in files
        for f in ["main.py", "main.cpp", "main.c", "main.go", "main.rs", "cli.py"]
    )
    if has_init and has_no_main:
        return "library"

    # CLI
    cli_files = {
        "cli.py",
        "main.py",
        "__main__.py",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
    }
    if cli_files & set(files):
        if "Python" in languages or "C++" in languages or "Rust" in languages:
            return "cli-tool"

    # Game
    if any(kw in name_lower for kw in ["game", "engine", "play", "puzzle"]):
        return "game"

    # Script
    if any(
        f.endswith(".sh") or f.endswith(".ps1") or f.endswith(".bash") for f in files
    ):
        if not any(f.endswith((".py", ".js", ".ts", ".rs", ".go")) for f in files):
            return "script"

    # Build system projects
    if "CMakeLists.txt" in files and "C++" in languages:
        return "cli-tool"
    if "Cargo.toml" in files:
        return "cli-tool"
    if "go.mod" in files:
        return "cli-tool"

    return "unknown"


def _build_description_hint(name: str, lang: str, proj_type: str) -> str:
    """Build a one-sentence description template based on detected metadata."""
    type_phrases = {
        "telegram-bot": f"A Telegram bot built with {lang}",
        "web-app": f"A web application built with {lang}",
        "cli-tool": f"A command-line tool written in {lang}",
        "game": f"An interactive game written in {lang}",
        "script": f"A collection of automation scripts",
        "library": f"A {lang} library",
        "unknown": f"A {lang} project",
    }

    phrase = type_phrases.get(proj_type, f"A {lang} project")
    return f"{phrase} — {name.replace('-', ' ').replace('_', ' ').title()}."


def _detect_install_command(files: list, primary_lang: str) -> str:
    """Return the most likely install command based on detected stack."""
    if "pyproject.toml" in files or "setup.py" in files:
        return "pip install ."
    if "requirements.txt" in files:
        return "pip install -r requirements.txt"
    if "Pipfile" in files:
        return "pipenv install"
    if "poetry.lock" in files:
        return "poetry install"
    if "package-lock.json" in files or "package.json" in files:
        return "npm install"
    if "pnpm-lock.yaml" in files:
        return "pnpm install"
    if "yarn.lock" in files:
        return "yarn install"
    if "Cargo.toml" in files:
        return "cargo build --release"
    if "CMakeLists.txt" in files:
        return "cmake -B build && cmake --build build"
    if "Makefile" in files:
        return "make"
    if "go.mod" in files:
        return "go mod download"
    if "build.gradle" in files or "build.gradle.kts" in files:
        return "gradle build"
    if "pom.xml" in files:
        return "mvn install"

    return "# See setup instructions below"


def _detect_run_command(
    files: list, dirs: list, primary_lang: str, proj_type: str
) -> str:
    """Return the most likely run command."""
    if proj_type == "cli-tool" and "main.py" in files:
        return "python main.py"
    if proj_type == "cli-tool" and "cli.py" in files:
        return "python cli.py"
    if proj_type == "telegram-bot":
        entry = "bot.py" if "bot.py" in files else "main.py"
        return f"python {entry}"
    if proj_type == "web-app":
        if "next.config.js" in files:
            return "npm run dev"
        if "package.json" in files:
            return "npm run dev"
        return "# See usage section below"
    if "pyproject.toml" in files:
        return "python -m projectname"
    if "Cargo.toml" in files:
        return "cargo run --release"
    if "CMakeLists.txt" in files:
        return "./build/projectname"
    if "Makefile" in files:
        return "make run"
    if "go.mod" in files:
        return "go run main.go"

    return "# See usage section below"


if __name__ == "__main__":
    import sys
    from projectreadmegen.scanner import scan_directory

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    scan = scan_directory(path, max_depth=3)
    detec = detect_stack(scan)

    print(f"Languages : {detec['languages']}")
    print(f"Primary   : {detec['primary_lang']}")
    print(f"Type      : {detec['project_type']}")
    print(f"License   : {detec['license']}")
    print(f"Install   : {detec['install_cmd']}")
    print(f"Run       : {detec['run_cmd']}")

# src/config.py

import logging
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

LANG_PATTERNS = {
    "Python":     ["requirements.txt", "setup.py", "pyproject.toml", "*.py", "Pipfile", "poetry.lock", "venv"],
    "JavaScript": ["package.json", "package-lock.json", "*.js", ".eslintrc", ".babelrc", "yarn.lock"],
    "TypeScript": ["tsconfig.json", "*.ts", "*.tsx", "pnpm-lock.yaml"],
    "C++":        ["CMakeLists.txt", "*.cpp", "*.hpp", "Makefile", "*.cc", "*.hxx"],
    "C":          ["*.c", "*.h", "Makefile", "CMakeLists.txt"],
    "Rust":       ["Cargo.toml", "Cargo.lock", "*.rs"],
    "Go":         ["go.mod", "go.sum", "*.go"],
    "Java":       ["pom.xml", "build.gradle", "build.gradle.kts", "*.java", "gradlew"],
    "C#":         ["*.csproj", "*.sln", "*.cs", "NuGet.config"],
    "PHP":        ["composer.json", "composer.lock", "*.php", "phpunit.xml"],
    "Ruby":       ["Gemfile", "Gemfile.lock", "*.rb", "Rakefile"],
    "Swift":      ["Package.swift", "*.swift", "Podfile"],
    "Kotlin":    ["build.gradle.kts", "*.kt", "settings.gradle.kts"],
    "Scala":      ["build.sbt", "*.scala"],
    "HTML/CSS":   ["*.html", "*.css", "*.scss", "*.sass", "tailwind.config.js"],
    "Shell":      ["*.sh", "*.bash", "Makefile"],
    "PowerShell": ["*.ps1", "*.psm1"],
    "Docker":     ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "Terraform":  ["*.tf", "terraform.tfvars"],
    "Vue":        ["vite.config.js", "vue.config.js", "*.vue"],
    "React":      ["webpack.config.js", "next.config.js"],
    "Angular":    ["angular.json", "ngsw-config.json"],
}

LICENSE_NAMES = {
    "LICENSE":        "Unknown",
    "LICENSE.md":     "Unknown",
    "LICENSE.txt":   "Unknown",
    "LICENSE-MIT":    "MIT",
    "LICENSE-APACHE": "Apache-2.0",
    "COPYING":        "GPL-3.0",
    "COPYING.md":     "GPL-3.0",
}

SKIP_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules",
    ".venv", "venv", "env", ".env", ".tox",
    "dist", "build", ".next", ".nuxt", ".svelte",
    "target", "bin", "obj", "out",
    ".idea", ".vscode", ".vs",
    ".cache", ".parcel-cache", ".turbo",
    "coverage", ".nyc_output", ".pytest_cache",
    "vendor", "third_party", "deps",
}

SKIP_FILES = {
    ".DS_Store", "Thumbs.db", "desktop.ini", "途",
    "*.pyc", "*.pyo", "*.class", "*.o", "*.so",
    "*.dll", "*.exe", "*.dylib",
    "*.log", "*.tmp", "*.temp",
    "package-lock.json",  # Skip if using yarn/pnpm
}

VALID_TEMPLATES = ["minimal", "standard", "full", "academic"]

VALID_CONFIG_KEYS = {
    "template": str,
    "output_file": str,
    "include_tree": bool,
    "max_tree_depth": int,
    "include_badges": bool,
    "gemini_enabled": bool,
    "ai_enabled": bool,
    "ai_provider": str,
    "groq_api_key": str,
    "author": str,
    "github_username": str,
}

DEFAULT_CONFIG = {
    "template":          "standard",
    "output_file":       "README.md",
    "include_tree":      True,
    "max_tree_depth":    3,
    "include_badges":    True,
    "gemini_enabled":    False,
    "ai_enabled":        False,
    "ai_provider":       "groq",
    "groq_api_key":      "",
    "author":            "",
    "github_username":   "",
    "free_uses_remaining": 5,
    "last_usage_date":   "",
}

FREE_USES_LIMIT = 5
USAGE_FILE = "projectreadmegen_usage.json"

PRESETS = {
    "django": {
        "template": "standard",
        "include_badges": True,
        "include_tree": True,
    },
    "react": {
        "template": "full",
        "include_badges": True,
        "include_tree": True,
    },
    "flask": {
        "template": "standard",
        "include_badges": True,
        "include_tree": True,
    },
    "fastapi": {
        "template": "standard",
        "include_badges": True,
        "include_tree": True,
    },
    "nodejs": {
        "template": "full",
        "include_badges": True,
        "include_tree": True,
    },
    "nextjs": {
        "template": "full",
        "include_badges": True,
        "include_tree": True,
    },
    "rust-cli": {
        "template": "standard",
        "include_badges": True,
        "include_tree": True,
    },
    "go-cli": {
        "template": "standard",
        "include_badges": True,
        "include_tree": True,
    },
}

TEMPLATES_DIR = "templates"
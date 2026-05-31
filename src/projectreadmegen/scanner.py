# src/scanner.py

import os
import json
import logging
import hashlib
import pickle
from fnmatch import fnmatch
from pathlib import Path

from projectreadmegen.config import SKIP_DIRS, SKIP_FILES

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".projectreadmegen" / "cache"
_CACHE_FILE = _CACHE_DIR / "scan_cache.pkl"


def _ensure_cache_dir():
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _is_skipped_file(filename: str) -> bool:
    return any(fnmatch(filename, pattern) for pattern in SKIP_FILES)


def _is_skipped_dir(dirname: str) -> bool:
    return dirname.startswith(".") or any(fnmatch(dirname, pattern) for pattern in SKIP_DIRS)


def _get_dir_hash(root: Path) -> str:
    """Generate a quick hash based on directory structure and modification times."""
    hasher = hashlib.sha256()

    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not _is_skipped_dir(d)]

            rel_path = Path(dirpath).relative_to(root)
            hasher.update(str(rel_path).encode())

            for f in sorted(filenames):
                if (
                    (not f.startswith(".") or f in [".gitignore", ".env.example"])
                    and not _is_skipped_file(f)
                ):
                    fpath = Path(dirpath) / f
                    try:
                        mtime = fpath.stat().st_mtime
                        hasher.update(f"{f}:{mtime}".encode())
                    except Exception:
                        pass
    except Exception:
        pass

    return hasher.hexdigest()


def _load_cache() -> dict:
    """Load scan cache from disk."""
    _ensure_cache_dir()
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    """Save scan cache to disk."""
    _ensure_cache_dir()
    try:
        with open(_CACHE_FILE, "wb") as f:
            pickle.dump(cache, f)
    except Exception:
        pass


def scan_directory(
    root_path: str, max_depth: int | None = None, use_cache: bool = True
) -> dict:
    """
    Walk a directory and collect metadata about its structure.

    Parameters:
        root_path (str): Absolute or relative path to the project root.
        max_depth (int): Maximum depth to traverse. None = unlimited.

    Returns:
        dict: {
            "root": str — absolute path,
            "name": str — folder name (used as project title),
            "files": list[str] — all file names found (not paths),
            "dirs":  list[str] — all directory names found,
            "tree":  str — ASCII tree representation,
            "has_license": bool,
            "has_contributing": bool,
            "has_gitignore": bool,
            "has_existing_readme": bool,
            "file_extensions": list[str] — unique extensions found,
        }
    """
    from projectreadmegen.exceptions import InvalidPathError, PermissionError as PermErr

    # Validate input
    if not root_path or not isinstance(root_path, str):
        raise InvalidPathError(
            f"Invalid path provided: {root_path}",
            "Please provide a valid directory path.",
        )

    root = Path(root_path).resolve()

    if not root.exists():
        raise InvalidPathError(
            f"Directory does not exist: {root}",
            f"The path '{root_path}' does not exist. Please check the path and try again.",
        )

    if not root.is_dir():
        raise InvalidPathError(
            f"Path is not a directory: {root}",
            f"'{root_path}' is a file, not a directory. Please provide a directory path.",
        )

    # Check for symlink attacks (circular symlinks)
    from projectreadmegen.utils import is_symlink_chain
    if is_symlink_chain(root):
        raise InvalidPathError(
            f"Symlink chain or circular reference detected: {root}",
            f"The path '{root_path}' contains a problematic symlink. Please use a regular directory.",
        )

    # Check read permissions
    try:
        root.iterdir()
    except PermissionError:
        raise PermErr(
            f"Permission denied accessing directory: {root}",
            f"You don't have permission to read '{root_path}'. Please check the folder permissions.",
        )

    logger.debug(
        f"Scanning directory: {root} (max_depth={max_depth}, use_cache={use_cache})"
    )

    cache = _load_cache() if use_cache else {}
    dir_hash = _get_dir_hash(root)
    cache_key = f"{root}:{max_depth}"

    if use_cache and cache_key in cache:
        cached = cache[cache_key]
        if cached.get("hash") == dir_hash:
            logger.debug(f"Using cached scan for {root}")
            return cached["data"]

    all_files = []
    all_dirs = []
    extensions = set()

    for dirpath, dirnames, filenames in os.walk(root):
        current_depth = len(Path(dirpath).relative_to(root).parts)

        if max_depth is not None and current_depth >= max_depth:
            dirnames.clear()
            continue

        dirnames[:] = [d for d in dirnames if not _is_skipped_dir(d)]

        for filename in filenames:
            if filename.startswith(".") and filename not in [
                ".gitignore",
                ".env.example",
            ]:
                continue
            if _is_skipped_file(filename):
                continue

            all_files.append(filename)
            ext = Path(filename).suffix.lower()
            if ext:
                extensions.add(ext)

        for dirname in dirnames:
            all_dirs.append(dirname)

    tree_str = _build_tree(root, max_depth)

    logger.debug(
        f"Found {len(all_files)} files, {len(all_dirs)} directories, {len(extensions)} extensions"
    )

    files_lower = [f.lower() for f in all_files]
    result = {
        "root": str(root),
        "name": root.name,
        "files": all_files,
        "dirs": all_dirs,
        "tree": tree_str,
        "has_license": any(
            f.lower() in files_lower
            for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "license"]
        ),
        "has_contributing": any(
            f.lower() in files_lower
            for f in ["CONTRIBUTING", "CONTRIBUTING.MD", "CONTRIBUTING.TXT"]
        ),
        "has_gitignore": ".gitignore" in files_lower,
        "has_existing_readme": "readme.md" in files_lower,
        "file_extensions": sorted(list(extensions)),
    }

    if use_cache:
        cache[cache_key] = {"hash": dir_hash, "data": result}
        _save_cache(cache)
        logger.debug(f"Cached scan result for {root}")

    return result


def _build_tree(
    root: Path, max_depth: int | None = None, prefix: str = "", current_depth: int = 0
) -> str:
    """
    Recursively build an ASCII directory tree string.

    Parameters:
        root (Path): Current directory path.
        max_depth (int): Maximum recursion depth.
        prefix (str): Indentation prefix for the current level.
        current_depth (int): Tracks current recursion depth.

    Returns:
        str: Multi-line ASCII tree string.
    """
    if max_depth is not None and current_depth > max_depth:
        return ""

    lines = []

    try:
        entries = sorted(root.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        return ""

    entries = [
        e
        for e in entries
        if (
            (not e.name.startswith(".") or e.name in [".gitignore", ".env.example"])
            and (e.is_file() or not _is_skipped_dir(e.name))
            and (e.is_dir() or not _is_skipped_file(e.name))
        )
    ]

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "`-- " if is_last else "|-- "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "|   "
            subtree = _build_tree(
                entry, max_depth, prefix + extension, current_depth + 1
            )
            if subtree:
                lines.append(subtree)

    return "\n".join(lines)


def load_config(root_path: str) -> dict:
    """
    Load readmegen.config.json from the project root if it exists,
    otherwise return DEFAULT_CONFIG.

    Parameters:
        root_path (str): Path to the project root.

    Returns:
        dict: Merged configuration (user config overrides defaults).
    """
    from projectreadmegen.config import DEFAULT_CONFIG, logger
    from projectreadmegen.exceptions import ConfigurationError

    config_path = Path(root_path) / "readmegen.config.json"
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        logger.debug(f"Loading config from {config_path}")
        try:
            # Verify readable
            if not config_path.is_file():
                logger.warning(f"Config path is not a file: {config_path}")
                return config

            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            # Validate config is dict
            if not isinstance(user_config, dict):
                raise ConfigurationError(
                    f"Invalid config format: expected dict, got {type(user_config).__name__}",
                    "Configuration file must be a valid JSON object.",
                )

            # Validate and merge
            for key, value in user_config.items():
                if key in config:
                    config[key] = value
                else:
                    logger.warning(f"Unknown config key in readmegen.config.json: {key}")

            logger.debug(f"Loaded user config: {config}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_path}: {e}")
            raise ConfigurationError(
                f"Invalid JSON in {config_path}: {e}",
                "The readmegen.config.json file contains invalid JSON. Please fix the syntax.",
            )
        except (IOError, OSError) as e:
            logger.error(f"Cannot read config file {config_path}: {e}")
            raise ConfigurationError(
                f"Cannot read config file {config_path}: {e}",
                f"Unable to read configuration file: {e}",
            )
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise ConfigurationError(
                f"Error loading config from {config_path}: {e}",
                f"An error occurred while loading configuration: {e}",
            )

    return config


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = scan_directory(path, max_depth=3)
    print(f"Project: {result['name']}")
    print(f"Files found: {len(result['files'])}")
    print(f"Extensions: {result['file_extensions']}")
    print(f"\nTree:\n{result['tree']}")

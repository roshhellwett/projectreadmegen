# src/projectreadmegen/scanner.py

import os
import json
import logging
import hashlib
from fnmatch import fnmatch
from pathlib import Path

from projectreadmegen.config import SKIP_DIRS, SKIP_FILES

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".projectreadmegen" / "cache"
_CACHE_FILE = _CACHE_DIR / "scan_cache.json"


def _ensure_cache_dir():
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _is_skipped_file(filename: str) -> bool:
    return any(fnmatch(filename, pattern) for pattern in SKIP_FILES)


def _is_skipped_dir(dirname: str) -> bool:
    return dirname.startswith(".") or any(fnmatch(dirname, pattern) for pattern in SKIP_DIRS)


def _get_dir_hash(root: Path, max_depth: int | None = None) -> str:
    """Generate a quick hash based on directory structure and modification times up to max_depth."""
    hasher = hashlib.sha256()

    try:
        for dirpath, dirnames, filenames in os.walk(root):
            current_depth = len(Path(dirpath).relative_to(root).parts)
            if max_depth is not None and current_depth >= max_depth:
                dirnames.clear()
                continue

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
    """Load scan cache from disk (JSON-based, no pickle)."""
    _ensure_cache_dir()
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    """Save scan cache to disk (JSON-based, no pickle)."""
    _ensure_cache_dir()
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def scan_directory(
    root_path: str, max_depth: int | None = 3, use_cache: bool = True
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
    dir_hash = _get_dir_hash(root, max_depth)
    cache_key = f"{root}:{max_depth}"

    if use_cache and cache_key in cache:
        cached = cache[cache_key]
        if (
            cached.get("hash") == dir_hash
            and "data" in cached
            and isinstance(cached["data"], dict)
            and cached["data"].get("graph") is not None
            and isinstance(cached["data"]["graph"], dict)
            and cached["data"]["graph"].get("stats") is not None
        ):
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
    graph_data = _build_graph_data(root, max_depth)

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
        "graph": graph_data,
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


def _build_graph_data(root: Path, max_depth: int | None = 3) -> dict:
    """Build structured nodes and edges for visual mind map / graph rendering."""
    import re
    nodes = []
    edges = []
    node_ids = set()

    root_id = "root"
    nodes.append({
        "id": root_id,
        "label": root.name,
        "type": "root",
        "path": "",
        "depth": 0,
        "summary": f"Project Root ({root.name})"
    })
    node_ids.add(root_id)

    dir_count = 0
    file_count = 0
    import_edges = 0
    MAX_GRAPH_NODES = 400

    js_import_re = re.compile(r'^\s*(?:import\s+.*from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\))', re.MULTILINE)

    for dirpath, dirnames, filenames in os.walk(root):
        if len(nodes) >= MAX_GRAPH_NODES:
            break

        current_depth = len(Path(dirpath).relative_to(root).parts)
        if max_depth is not None and current_depth >= max_depth:
            dirnames.clear()
            continue

        dirnames[:] = [d for d in dirnames if not _is_skipped_dir(d)]
        rel_dir = Path(dirpath).relative_to(root)
        dir_id = root_id if str(rel_dir) == "." else f"dir:{rel_dir.as_posix()}"

        if dir_id not in node_ids and dir_id != root_id:
            parent_rel = rel_dir.parent
            parent_id = root_id if str(parent_rel) == "." else f"dir:{parent_rel.as_posix()}"
            nodes.append({
                "id": dir_id,
                "label": rel_dir.name,
                "type": "dir",
                "path": rel_dir.as_posix(),
                "depth": current_depth,
                "parent": parent_id,
                "summary": f"Directory ({rel_dir.name})"
            })
            node_ids.add(dir_id)
            if parent_id in node_ids:
                edges.append({
                    "source": parent_id,
                    "target": dir_id,
                    "relation": "contains"
                })
            dir_count += 1

        for filename in sorted(filenames):
            if len(nodes) >= MAX_GRAPH_NODES:
                break
            if filename.startswith(".") and filename not in [".gitignore", ".env.example"]:
                continue
            if _is_skipped_file(filename):
                continue

            rel_file = rel_dir / filename if str(rel_dir) != "." else Path(filename)
            file_id = f"file:{rel_file.as_posix()}"
            if file_id in node_ids:
                continue

            ext = rel_file.suffix.lower()
            node_type = "file"
            if ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c"]:
                node_type = "module"
            elif ext in [".json", ".toml", ".yaml", ".yml", ".ini", ".env", ".cfg"]:
                node_type = "config"
            elif ext in [".md", ".txt", ".rst"]:
                node_type = "doc"
            elif ext in [".html", ".css", ".scss", ".vue"]:
                node_type = "ui"
            elif "test" in filename.lower() or "spec" in filename.lower():
                node_type = "test"

            size_bytes = 0
            try:
                size_bytes = (root / rel_file).stat().st_size
            except Exception:
                pass

            nodes.append({
                "id": file_id,
                "label": filename,
                "type": node_type,
                "path": rel_file.as_posix(),
                "depth": current_depth + 1,
                "parent": dir_id,
                "size_bytes": size_bytes,
                "summary": f"{node_type.upper()} ({size_bytes} B)"
            })
            node_ids.add(file_id)
            edges.append({
                "source": dir_id,
                "target": file_id,
                "relation": "contains"
            })
            file_count += 1

            if node_type == "module" and size_bytes < 100_000:
                try:
                    content = (root / rel_file).read_text(encoding="utf-8", errors="ignore")
                    if ext == ".py":
                        for line in content.splitlines()[:60]:
                            if "import " in line:
                                for other_node in nodes:
                                    if other_node["type"] == "module" and other_node["id"] != file_id:
                                        stem = Path(other_node["label"]).stem
                                        if f"import {stem}" in line or f"from {stem}" in line or f".{stem}" in line or f"projectreadmegen.{stem}" in line:
                                            edges.append({
                                                "source": file_id,
                                                "target": other_node["id"],
                                                "relation": "imports"
                                            })
                                            import_edges += 1
                    elif ext in [".js", ".ts", ".jsx", ".tsx"]:
                        for line in content.splitlines()[:60]:
                            for match in js_import_re.findall(line):
                                imp_path = match[0] or match[1]
                                if imp_path.startswith("./") or imp_path.startswith("../"):
                                    imp_name = Path(imp_path).name
                                    for other_node in nodes:
                                        if other_node["id"] != file_id and (other_node["label"] == imp_name or Path(other_node["label"]).stem == imp_name):
                                            edges.append({
                                                "source": file_id,
                                                "target": other_node["id"],
                                                "relation": "imports"
                                            })
                                            import_edges += 1
                except Exception:
                    pass

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "dir_count": dir_count,
            "file_count": file_count,
            "import_connections": import_edges
        }
    }


# Backwards-compatible re-export: load_config now lives in config.py
from projectreadmegen.config import load_config  # noqa: F401, E402


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = scan_directory(path, max_depth=3)
    print(f"Project: {result['name']}")
    print(f"Files found: {len(result['files'])}")
    print(f"Extensions: {result['file_extensions']}")
    print(f"\nTree:\n{result['tree']}")


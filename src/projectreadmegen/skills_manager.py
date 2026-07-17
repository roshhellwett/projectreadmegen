import os
import re
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set

import yaml

logger = logging.getLogger(__name__)


def _resolve_skills_root() -> Path:
    env = os.environ.get("PROJECTREADME_SKILLS_DIR")
    if env:
        return Path(env).resolve()

    script_dir = Path(__file__).resolve()

    candidates = [
        script_dir.parent.parent / "skills",
        script_dir.parent / "skills",
        script_dir.parent.parent.parent / "skills",
        script_dir.parent.parent.parent.parent / "skills",
    ]

    for p in candidates:
        if p.exists() and p.is_dir():
            return p

    return candidates[0]


_SKILLS_ROOT = _resolve_skills_root()

EXCLUDED_CATEGORIES = {"_sources", "Other"}

_TOOL_ALIASES = {
    "opencode": "opencode",
    "claude-code": "claude-code",
    "claude": "claude-code",
    "claude_code": "claude-code",
    "claudecode": "claude-code",
    "cursor": "cursor",
    "codex-cli": "codex-cli",
    "codex": "codex-cli",
    "codex_cli": "codex-cli",
    "codexcli": "codex-cli",
    "gemini-cli": "gemini-cli",
    "gemini": "gemini-cli",
    "gemini_cli": "gemini-cli",
    "geminicli": "gemini-cli",
    "windsurf": "windsurf",
    "cline": "cline",
    "vscode": "vscode",
    "vs-code": "vscode",
    "vs_code": "vscode",
}

_ALL_TOOL_IDS = [
    "opencode", "claude-code", "cursor", "codex-cli",
    "gemini-cli", "windsurf", "cline", "vscode",
]

_TOOL_DETECTION_PATHS = {
    "opencode": ["opencode.json", ".opencode"],
    "claude-code": [".claude", "CLAUDE.md"],
    "cursor": [".cursor", ".cursorrules"],
    "codex-cli": [".codex"],
    "gemini-cli": [".gemini", "GEMINI.md"],
    "windsurf": [".windsurf"],
    "cline": [".cline", ".clinerules"],
    "vscode": [".vscode", ".vscode/settings.json"],
}

_GLOBAL_TOOL_PATHS = {
    "opencode": [Path.home() / ".config" / "opencode"],
    "claude-code": [Path.home() / ".claude"],
    "cursor": [Path.home() / ".cursor"],
    "codex-cli": [Path.home() / ".codex"],
    "gemini-cli": [Path.home() / ".gemini"],
    "windsurf": [Path.home() / ".windsurf"],
    "cline": [Path.home() / ".cline"],
    "vscode": [Path.home() / ".vscode"],
}

_TOOL_LABELS = {
    "opencode": "OpenCode",
    "claude-code": "Claude Code",
    "cursor": "Cursor",
    "codex-cli": "Codex CLI",
    "gemini-cli": "Gemini CLI",
    "windsurf": "Windsurf",
    "cline": "Cline",
    "vscode": "VS Code",
}

_TOOL_GLOBAL_SKILL_DIRS = {
    "opencode": "skills",
    "claude-code": "skills",
    "cursor": "user/rules",
    "codex-cli": "skills",
    "gemini-cli": "skills",
    "windsurf": "skills",
    "cline": "skills",
    "vscode": "skills",
}


def _normalize_tool_names(raw_names: List[str]) -> List[str]:
    result = []
    for name in raw_names:
        canonical = _TOOL_ALIASES.get(name.strip().lower())
        if canonical and canonical not in result:
            result.append(canonical)
    return result


def _extract_yaml_frontmatter(text: str) -> Optional[dict]:
    """Extract and parse YAML frontmatter between --- delimiters."""
    stripped = text.lstrip("\ufeff")
    if not stripped.startswith("---"):
        return None
    end = stripped.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(stripped[3:end])
    except Exception:
        return None


def _read_skill_md(skill_dir: Path) -> dict:
    """Parse SKILL.md and return metadata dict."""
    result = {"description": "", "risk": "unknown", "source": "", "raw_category": "", "tools": []}
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return result
    text = skill_md.read_text("utf-8", errors="replace")

    frontmatter = _extract_yaml_frontmatter(text)
    if frontmatter:
        result["description"] = frontmatter.get("description") or ""
        result["risk"] = str(frontmatter.get("risk", "unknown"))
        result["source"] = frontmatter.get("source") or ""
        result["raw_category"] = frontmatter.get("category") or ""
        raw_tools = frontmatter.get("tools")
        if isinstance(raw_tools, list):
            result["tools"] = _normalize_tool_names(raw_tools)
        elif isinstance(raw_tools, str):
            result["tools"] = _normalize_tool_names(
                [t.strip().strip('"').strip("'") for t in raw_tools.split(",") if t.strip()]
            )
        return result

    desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if desc_match:
        result["description"] = desc_match.group(1).strip().strip('"')
    risk_match = re.search(r"^risk:\s*(.+?)\s*$", text, re.MULTILINE)
    if risk_match:
        result["risk"] = risk_match.group(1).strip()
    source_match = re.search(r"^source:\s*(.+?)\s*$", text, re.MULTILINE)
    if source_match:
        result["source"] = source_match.group(1).strip()
    cat_match = re.search(r'^category:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if cat_match:
        result["raw_category"] = cat_match.group(1).strip().strip('"')
    tools_match = re.search(r'^tools:\s*\[(.*?)\]', text, re.MULTILINE)
    if tools_match:
        items = [t.strip().strip('"').strip("'") for t in tools_match.group(1).split(",") if t.strip()]
        result["tools"] = _normalize_tool_names(items)
    tools_str_match = re.search(r'^tools:\s*(.+?)$', text, re.MULTILINE)
    if tools_str_match and not tools_match:
        raw = tools_str_match.group(1).strip()
        if raw and raw != "[]":
            items = [t.strip() for t in raw.split(",") if t.strip()]
            result["tools"] = _normalize_tool_names(items)
    return result


def _build_skill_entry(skill_id: str, cat_name: str, skill_dir: Path) -> dict:
    """Build a skill dict from a directory."""
    meta = _read_skill_md(skill_dir)
    return {
        "id": skill_id,
        "name": skill_id.replace("-", " ").title(),
        "description": meta["description"],
        "category": cat_name,
        "risk": meta["risk"],
        "source": meta["source"],
        "tools": meta["tools"],
        "_path": str(skill_dir),
    }


def discover_all_skills() -> List[Dict]:
    """Walk skills directory and return all skills grouped by category."""
    if not _SKILLS_ROOT.exists():
        logger.warning("Skills root not found: %s", _SKILLS_ROOT)
        return []

    skills = []
    seen_ids = set()

    # Phase 1: top-level category dirs (curated hierarchy)
    for cat_dir in sorted(_SKILLS_ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name
        if cat_name in EXCLUDED_CATEGORIES:
            continue
        for skill_dir in sorted(cat_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_id = skill_dir.name
            if skill_id in seen_ids:
                continue
            seen_ids.add(skill_id)
            skills.append(_build_skill_entry(skill_id, cat_name, skill_dir))

    # Phase 2: flat repos inside _sources/ (each skill has category: field in SKILL.md)
    sources_dir = _SKILLS_ROOT / "_sources"
    if sources_dir.exists():
        for repo_dir in sorted(sources_dir.iterdir()):
            repo_skills = repo_dir / "skills"
            if not repo_skills.is_dir():
                continue
            for skill_dir in sorted(repo_skills.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_id = skill_dir.name
                if skill_id in seen_ids:
                    continue
                seen_ids.add(skill_id)
                meta = _read_skill_md(skill_dir)
                cat_name = meta["raw_category"] or "Uncategorized"
                entry = _build_skill_entry(skill_id, cat_name, skill_dir)
                skills.append(entry)

    return skills


def search_skills(query: str, skills: List[Dict]) -> List[Dict]:
    """Fuzzy search across skill name, description, and category."""
    if not query or not query.strip():
        return skills

    q = query.strip().lower()
    scored = []

    for s in skills:
        name = s["name"].lower()
        desc = s["description"].lower()
        cat = s["category"].lower()
        skill_id = s["id"].lower()

        score = 0
        if q == name or q == skill_id:
            score = 100
        elif name.startswith(q) or skill_id.startswith(q):
            score = 80
        elif q in name or q in skill_id:
            score = 60
        elif q in cat:
            score = 40
        elif q in desc:
            score = 20

        if score > 0:
            scored.append((score, s))

    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [s for _, s in scored]


def install_skills(project_path: str, skill_ids: List[str]) -> Dict:
    """Copy selected skills into <project_path>/skill/ and return results."""
    project_dir = Path(project_path).resolve()
    skill_target = project_dir / "skill"

    all_skills = discover_all_skills()
    skill_map = {s["id"]: s for s in all_skills}

    installed = []
    errors = []

    for skill_id in skill_ids:
        skill_info = skill_map.get(skill_id)
        if not skill_info:
            errors.append({"id": skill_id, "error": "Skill not found"})
            continue

        src_dir = Path(skill_info["_path"])

        if not src_dir.exists():
            errors.append({"id": skill_id, "error": "Source directory missing"})
            continue

        dst_dir = skill_target / skill_id
        if dst_dir.exists():
            installed.append({"id": skill_id, "status": "already_installed"})
            continue

        try:
            shutil.copytree(str(src_dir), str(dst_dir), dirs_exist_ok=False)
            installed.append({"id": skill_id, "status": "installed"})
        except Exception as e:
            errors.append({"id": skill_id, "error": str(e)})

    return {"installed": installed, "errors": errors}


def ensure_agent_md(project_path: str, installed_skills: List[Dict]) -> str:
    """Create or update agent.md in the project root with skill references."""
    project_dir = Path(project_path).resolve()
    agent_md_path = project_dir / "agent.md"

    existing_skills = set()
    if agent_md_path.exists():
        content = agent_md_path.read_text("utf-8", errors="replace")
        existing = re.findall(r"^###\s+(.+)$", content, re.MULTILINE)
        existing_skills = {e.strip().lower() for e in existing}
    else:
        content = "# Skills Configuration\n\n"
        content += (
            "This directory contains AI agent skills installed for this project.\n"
        )
        content += (
            "This file instructs AI agents on available skills and how to use them.\n\n"
        )
        content += "## Installed Skills\n\n"
        agent_md_path.write_text(content, encoding="utf-8")
        content = agent_md_path.read_text("utf-8", errors="replace")

    additions = []
    for item in installed_skills:
        skill_id = item.get("id", "")
        skill_name = skill_id.replace("-", " ").title()
        key = skill_name.lower()
        if key in existing_skills:
            continue

        skill_md_path = project_dir / "skill" / skill_id / "SKILL.md"
        desc = ""
        if skill_md_path.exists():
            desc_match = re.search(
                r'^description:\s*"?(.+?)"?\s*$',
                skill_md_path.read_text("utf-8", errors="replace"),
                re.MULTILINE,
            )
            if desc_match:
                desc = desc_match.group(1).strip().strip('"')

        block = f"\n### {skill_name}\n"
        block += f"- **Path**: `skill/{skill_id}/`\n"
        if desc:
            block += f"- **Description**: {desc}\n"
        block += f"- **Instructions**: When working on tasks related to this domain, load the skill from `skill/{skill_id}/SKILL.md` for specialized guidance.\n"

        additions.append(block)
        existing_skills.add(key)

    if additions:
        content += "\n" + "\n".join(additions)
        agent_md_path.write_text(content, encoding="utf-8")

    return str(agent_md_path)


def _read_skill_md_from_path(skill_md_path: Path) -> dict:
    """Parse a SKILL.md from an arbitrary path and return metadata."""
    result = {"description": "", "risk": "unknown", "source": "", "raw_category": "", "tools": []}
    if not skill_md_path.exists():
        return result
    text = skill_md_path.read_text("utf-8", errors="replace")
    frontmatter = _extract_yaml_frontmatter(text)
    if frontmatter:
        result["description"] = frontmatter.get("description") or ""
        result["risk"] = str(frontmatter.get("risk", "unknown"))
        result["source"] = frontmatter.get("source") or ""
        result["raw_category"] = frontmatter.get("category") or ""
        raw_tools = frontmatter.get("tools")
        if isinstance(raw_tools, list):
            result["tools"] = _normalize_tool_names(raw_tools)
        elif isinstance(raw_tools, str):
            result["tools"] = _normalize_tool_names(
                [t.strip().strip('"').strip("'") for t in raw_tools.split(",") if t.strip()]
            )
        return result
    desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if desc_match:
        result["description"] = desc_match.group(1).strip().strip('"')
    tools_match = re.search(r'^tools:\s*\[(.*?)\]', text, re.MULTILINE)
    if tools_match:
        items = [t.strip().strip('"').strip("'") for t in tools_match.group(1).split(",") if t.strip()]
        result["tools"] = _normalize_tool_names(items)
    return result


def _generate_skill_block(project_dir: Path, skill_id: str, include_tools: bool = True) -> Optional[str]:
    """Generate a markdown section for a skill (used by AGENTS.md, CLAUDE.md, GEMINI.md)."""
    skill_md_path = project_dir / "skill" / skill_id / "SKILL.md"
    if not skill_md_path.exists():
        return None
    meta = _read_skill_md_from_path(skill_md_path)
    skill_name = skill_id.replace("-", " ").title()
    block = f"\n### {skill_name}\n"
    block += f"- **Path**: `skill/{skill_id}/`\n"
    if meta["description"]:
        block += f"- **Description**: {meta['description']}\n"
    if include_tools and meta["tools"]:
        block += f"- **AI Tools**: {', '.join(meta['tools'])}\n"
    block += f"- **Instructions**: When working on tasks related to this domain, load the skill from `skill/{skill_id}/SKILL.md` for specialized guidance.\n"
    return block


def _update_instructions_file(path: Path, installed_skills: List[Dict]) -> str:
    """Create or update an AI instructions file (AGENTS.md / CLAUDE.md / GEMINI.md) with skill references."""
    project_dir = path.parent
    existing_skills = set()
    if path.exists():
        content = path.read_text("utf-8", errors="replace")
        existing = re.findall(r"^###\s+(.+)$", content, re.MULTILINE)
        existing_skills = {e.strip().lower() for e in existing}
    else:
        tool_name = path.name.replace(".md", "")
        content = f"# {tool_name}\n\n"
        content += "This project has AI agent skills installed for specialized guidance.\n\n"
        content += "## Installed Skills\n\n"
        path.write_text(content, encoding="utf-8")
        content = path.read_text("utf-8", errors="replace")

    additions = []
    for item in installed_skills:
        skill_id = item.get("id", "")
        skill_name = skill_id.replace("-", " ").title()
        key = skill_name.lower()
        if key in existing_skills:
            continue
        block = _generate_skill_block(project_dir, skill_id)
        if block:
            additions.append(block)
            existing_skills.add(key)

    if additions:
        content += "\n" + "\n".join(additions)
        path.write_text(content, encoding="utf-8")
    return str(path)


def _write_agents_md(project_dir: Path, installed_skills: List[Dict]) -> str:
    """Create or update AGENTS.md (recognized by opencode and codex-cli)."""
    return _update_instructions_file(project_dir / "AGENTS.md", installed_skills)


def _write_claude_md(project_dir: Path, installed_skills: List[Dict]) -> str:
    """Create or update CLAUDE.md (recognized by claude-code)."""
    return _update_instructions_file(project_dir / "CLAUDE.md", installed_skills)


def _write_gemini_md(project_dir: Path, installed_skills: List[Dict]) -> str:
    """Create or update GEMINI.md (recognized by gemini-cli)."""
    return _update_instructions_file(project_dir / "GEMINI.md", installed_skills)


def _write_cursor_rule(project_dir: Path, skill_id: str) -> Optional[str]:
    """Create a cursor rule file (.cursor/rules/<skill-id>.md) for a skill."""
    skill_md_path = project_dir / "skill" / skill_id / "SKILL.md"
    if not skill_md_path.exists():
        return None
    meta = _read_skill_md_from_path(skill_md_path)
    skill_name = skill_id.replace("-", " ").title()
    text = skill_md_path.read_text("utf-8", errors="replace")
    body = text
    frontmatter = _extract_yaml_frontmatter(text)
    if frontmatter is not None:
        end = text.find("---", 3)
        if end != -1:
            body = text[end + 3:].strip()

    rules_dir = project_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_path = rules_dir / f"{skill_id}.md"
    if rule_path.exists():
        return str(rule_path)

    rule_content = f"""---
description: {meta['description'] or skill_name}
globs: 
---

# {skill_name}

{body}
"""
    rule_path.write_text(rule_content, encoding="utf-8")
    return str(rule_path)


def _detect_installed_tools(project_dir: Path) -> Set[str]:
    """Detect which AI coding tools are configured in the target project."""
    detected: Set[str] = set()
    for tool, paths in _TOOL_DETECTION_PATHS.items():
        for p in paths:
            if (project_dir / p).exists():
                detected.add(tool)
                break
    return detected


def detect_global_tools() -> List[Dict]:
    """Return ALL known AI tool IDs with detection status.

    Returns one entry per known tool. Each entry has `detected: True/False`
    so the frontend can show all tools to the user and pre-check detected ones.
    """
    results: List[Dict] = []
    for tool in _ALL_TOOL_IDS:
        paths = _GLOBAL_TOOL_PATHS.get(tool, [])
        found = False
        config_path = None
        for p in paths:
            try:
                if p.exists():
                    found = True
                    config_path = str(p)
                    break
            except (PermissionError, OSError):
                continue
        results.append({
            "id": tool,
            "name": _TOOL_LABELS.get(tool, tool),
            "config_path": config_path,
            "detected": found,
        })
    return results


# ---- config file registration helpers -----------------------------------
# GOLDEN RULE: If a config file exists and fails to parse, NEVER write back
# a partial/minimal config. Log the error and return False. The user's
# original file is preserved intact.

def _strip_comments(text: str) -> str:
    """Remove // and /* */ comments from JSONC text, respecting strings."""
    out = []
    i = 0
    in_str = False
    while i < len(text):
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_str = not in_str
        if not in_str:
            if ch == '/' and i + 1 < len(text):
                if text[i + 1] == '/':
                    end = text.find('\n', i)
                    if end == -1:
                        end = len(text)
                    i = end
                    continue
                if text[i + 1] == '*':
                    end = text.find('*/', i + 2)
                    if end == -1:
                        end = len(text) - 2
                    i = end + 2
                    continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _append_to_json_array(text: str, key_path: List[str], value: str) -> Optional[str]:
    """Add `value` to the JSON array at `key_path` in the text, preserving formatting.

    key_path = ["skills"] or ["skills", "paths"]
    Returns modified text or None if the array can't be found.
    """
    if not key_path:
        return None

    # Build regex: walk the key path
    pattern_parts = []
    for i, key in enumerate(key_path):
        if i == 0:
            pattern_parts.append(r'"' + re.escape(key) + r'"\s*:\s*')
        else:
            pattern_parts.append(r'\{[^}]*?"' + re.escape(key) + r'"\s*:\s*')

    if len(key_path) > 1:
        pattern_parts[-1] = r'\{[^}]*?"' + re.escape(key_path[-1]) + r'"\s*:\s*'

    pattern = ''.join(pattern_parts) + r'\[(.*?)\]'

    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return None

    array_content = match.group(1).strip()
    if value in array_content:
        return text

    if not array_content or array_content == '':
        new_array = f'\n    "{value}"\n  '
    elif array_content.endswith(','):
        new_array = array_content + f'\n    "{value}"'
    else:
        new_array = array_content + f',\n    "{value}"'

    new_array = new_array.rstrip(',') + ('' if new_array.rstrip().endswith(']') else '')

    return text[:match.start(1)] + new_array + text[match.end(1):]


def _safe_update_json_config(
    file_path: Path,
    key_path: List[str],
    value: str,
    *,
    create_if_missing: bool = False,
    create_content: Optional[str] = None,
) -> bool:
    """Safely add a string value to a JSON array at key_path in a JSON/JSONC file.

    Safety rules:
      1. If file exists but can't be parsed → LOG, return False, NEVER write.
      2. If file doesn't exist and create_if_missing=False → return False.
      3. If file doesn't exist and create_if_missing=True → create with create_content.
      4. Write is atomic: write to .tmp, then os.rename().

    Returns True if the value was added (or already present).
    """
    try:
        if file_path.exists():
            original = file_path.read_text("utf-8", errors="replace")
            clean = _strip_comments(original)
            try:
                parsed = json.loads(clean)
            except json.JSONDecodeError as e:
                logger.error(
                    "Cannot modify %s: invalid JSON/JSONC. Refusing to write. Error: %s",
                    file_path, e,
                )
                return False

            # Validate key path exists in parsed structure
            obj = parsed
            valid = True
            for key in key_path:
                if isinstance(obj, dict) and key in obj:
                    obj = obj[key]
                else:
                    valid = False
                    break
            if not valid or not isinstance(obj, list):
                logger.error(
                    "Cannot modify %s: key_path %s not found or not a list. Refusing to write.",
                    file_path, key_path,
                )
                return False

            if value in obj:
                return True

            updated = _append_to_json_array(original, key_path, value)
            if updated is None or updated == original:
                return False

            # Atomic write: .tmp + rename
            tmp = file_path.with_suffix(file_path.suffix + ".tmp")
            tmp.write_text(updated, encoding="utf-8")
            tmp.replace(file_path)
            return True

        if not create_if_missing:
            logger.info("Config file %s does not exist, skipping.", file_path)
            return False

        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = create_content or json.dumps(
            _build_json_stub(key_path, value), indent=2
        )
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(file_path)
        return True

    except Exception as e:
        logger.error("Failed to update config %s: %s", file_path, e)
        return False


def _build_json_stub(key_path: List[str], value: str) -> dict:
    """Build a stub JSON object from a key path and value.

    e.g. (["skills", "paths"], "foo") → {"skills": {"paths": ["foo"]}}
         (["skills"], "foo")           → {"skills": ["foo"]}
    """
    result: dict = {}
    current = result
    for i, key in enumerate(key_path):
        if i == len(key_path) - 1:
            current[key] = [value]
        else:
            current[key] = {}
            current = current[key]
    return result


def _register_in_opencode_config(skill_id: str) -> bool:
    """Ensure ~/.config/opencode/opencode.jsonc contains the skills path."""
    config_path = Path.home() / ".config" / "opencode" / "opencode.jsonc"
    return _safe_update_json_config(
        config_path,
        key_path=["skills", "paths"],
        value="~/.config/opencode/skills",
    )


def _register_in_codex_config(skill_id: str) -> bool:
    """Ensure ~/.codex/codex.json contains the skills path.

    Codex CLI uses flat JSON: {"skills": ["path1", "path2"]}
    If the file doesn't exist, create it with the skills path.
    """
    config_path = Path.home() / ".codex" / "codex.json"
    return _safe_update_json_config(
        config_path,
        key_path=["skills"],
        value=str(Path.home() / ".codex" / "skills"),
        create_if_missing=True,
        create_content=json.dumps(
            {"skills": [str(Path.home() / ".codex" / "skills")]}, indent=2
        ),
    )


def _register_in_vscode_settings(project_dir: Path, skill_ids: List[str]) -> bool:
    """Add skill references to .vscode/settings.json in the project.

    VS Code settings.json supports JSONC (comments, trailing commas).
    This function adds entries to the "skills.installed" array.
    """
    config_path = project_dir / ".vscode" / "settings.json"
    success = True
    for sid in skill_ids:
        ok = _safe_update_json_config(
            config_path,
            key_path=["skills.installed"],
            value=sid,
            create_if_missing=True,
            create_content=json.dumps({"skills.installed": [sid]}, indent=2),
        )
        if not ok:
            success = False
    return success


# ---- file installation helpers -------------------------------------------

def _copy_skill_dir(src: Path, dst: Path) -> bool:
    """Copy skill directory from src to dst. Returns True on success."""
    try:
        if dst.exists():
            return True
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(src), str(dst), dirs_exist_ok=False)
        return True
    except Exception:
        return False


def _write_cursor_rule_file(target_path: Path, src_dir: Path, skill_id: str) -> bool:
    """Write a cursor-compatible rule .md file from a SKILL.md."""
    try:
        skill_md = src_dir / "SKILL.md"
        if not skill_md.exists():
            return False
        text = skill_md.read_text("utf-8", errors="replace")
        frontmatter = _extract_yaml_frontmatter(text)
        body = text
        if frontmatter is not None:
            end = text.find("---", 3)
            if end != -1:
                body = text[end + 3:].strip()
        description = (
            frontmatter.get("description", skill_id.replace("-", " ").title())
            if frontmatter
            else skill_id.replace("-", " ").title()
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            f"""---
description: {description}
globs:
---

# {skill_id.replace('-', ' ').title()}

{body}
""",
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def _install_skill_to_global(tool: str, skill_id: str, src_dir: Path) -> dict:
    """Install a single skill to a tool's global config directory.

    Returns: dict with keys: tool, skill_id, status, path, scope, verified.
    """
    result = {
        "tool": tool,
        "skill_id": skill_id,
        "status": "skipped",
        "path": None,
        "scope": "global",
        "verified": False,
    }

    if not src_dir.exists():
        return result

    config_paths = _GLOBAL_TOOL_PATHS.get(tool)
    if not config_paths:
        return result

    base = config_paths[0]
    sub = _TOOL_GLOBAL_SKILL_DIRS.get(tool, "skills")

    # --- cursor: writes a rule file ---
    if tool == "cursor":
        target_file = base / sub / f"{skill_id}.md"
        if target_file.exists():
            result["status"] = "already_registered"
            result["path"] = str(target_file)
            result["verified"] = True
            return result
        ok = _write_cursor_rule_file(target_file, src_dir, skill_id)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_file)
            result["verified"] = target_file.exists()
        return result

    # --- opencode / codex-cli: copy dir + update config ---
    if tool in ("opencode", "codex-cli"):
        target_dir = base / sub / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        if tool == "opencode":
            _register_in_opencode_config(skill_id)
        elif tool == "codex-cli":
            _register_in_codex_config(skill_id)
        return result

    # --- all other tools: copy dir into skills/ ---
    target_dir = base / sub / skill_id
    ok = _copy_skill_dir(src_dir, target_dir)
    if ok:
        result["status"] = "registered"
        result["path"] = str(target_dir)
        result["verified"] = target_dir.exists()
    return result


def _install_skill_to_project(tool: str, skill_id: str, src_dir: Path, project_dir: Path) -> dict:
    """Install a single skill to a tool's project-level directory.

    For opencode/codex-cli this is a no-op (they use AGENTS.md).
    For all others the skill is placed under .<tool>/skills/<id>/.
    """
    result = {
        "tool": tool,
        "skill_id": skill_id,
        "status": "skipped",
        "path": None,
        "scope": "project",
        "verified": False,
    }

    if not src_dir.exists():
        return result

    # opencode / codex-cli → referenced via AGENTS.md, no physical copy needed
    if tool in ("opencode", "codex-cli"):
        result["status"] = "registered"
        result["path"] = f"skill/{skill_id}/"
        result["verified"] = True
        return result

    # cursor → .cursor/rules/<id>.md
    if tool == "cursor":
        target_file = project_dir / ".cursor" / "rules" / f"{skill_id}.md"
        if target_file.exists():
            result["status"] = "already_registered"
            result["path"] = str(target_file)
            result["verified"] = True
            return result
        ok = _write_cursor_rule_file(target_file, src_dir, skill_id)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_file)
            result["verified"] = target_file.exists()
        return result

    # claude-code → .claude/skills/<id>/
    if tool == "claude-code":
        target_dir = project_dir / ".claude" / "skills" / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        return result

    # vscode → .vscode/skills/<id>/ + update settings.json
    if tool == "vscode":
        target_dir = project_dir / ".vscode" / "skills" / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        if result["status"] in ("registered", "already_registered"):
            _register_in_vscode_settings(project_dir, [skill_id])
        return result

    # gemini-cli → .gemini/skills/<id>/
    if tool == "gemini-cli":
        target_dir = project_dir / ".gemini" / "skills" / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        return result

    # windsurf → .windsurf/skills/<id>/
    if tool == "windsurf":
        target_dir = project_dir / ".windsurf" / "skills" / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        return result

    # cline → .cline/skills/<id>/
    if tool == "cline":
        target_dir = project_dir / ".cline" / "skills" / skill_id
        ok = _copy_skill_dir(src_dir, target_dir)
        if ok:
            result["status"] = "registered"
            result["path"] = str(target_dir)
            result["verified"] = target_dir.exists()
        return result

    return result


def register_installed_skills(
    project_dir: Path,
    installed_skills: List[Dict],
    detected_tools: Optional[Set[str]] = None,
) -> Dict:
    """
    Register installed skills with AI coding tools.

    For each user-specified tool:
      1. Try global install (into ~/.config/<tool>/skills/<id>/ etc.).
      2. Fall back to project-level install (./<tool>/skills/<id>/).
      3. If neither works, register under the project skill/ dir.

    AGENTS.md, CLAUDE.md, and GEMINI.md are always written in the project.

    Returns:
        dict with keys:
          - agents_md: path to AGENTS.md
          - claude_md: path to CLAUDE.md (if claude-code selected)
          - gemini_md: path to GEMINI.md (if gemini-cli selected)
          - detected_tools: sorted list of selected tools
          - registrations: list of per-tool-per-skill results
          - errors: list of errors
    """
    if detected_tools is None:
        detected_tools = {t["id"] for t in detect_global_tools() if t["detected"]}
        if not detected_tools:
            detected_tools = {"opencode"}
    elif not detected_tools:
        detected_tools = {"opencode"}

    result: Dict = {
        "agents_md": None,
        "claude_md": None,
        "gemini_md": None,
        "detected_tools": sorted(detected_tools),
        "registrations": [],
        "errors": [],
    }

    try:
        result["agents_md"] = _write_agents_md(project_dir, installed_skills)
    except Exception as e:
        result["errors"].append({"tool": "opencode", "skill_id": "*", "error": f"AGENTS.md: {e}"})

    for tool in detected_tools:
        for item in installed_skills:
            skill_id = item.get("id", "")
            if not skill_id:
                continue
            try:
                src_dir = project_dir / "skill" / skill_id
                # Always try global first
                if tool in _GLOBAL_TOOL_PATHS:
                    reg = _install_skill_to_global(tool, skill_id, src_dir)
                    if reg["status"] == "skipped" or not reg["verified"]:
                        # Fall back to project-level
                        proj_reg = _install_skill_to_project(tool, skill_id, src_dir, project_dir)
                        if proj_reg["status"] != "skipped" and proj_reg["verified"]:
                            reg = proj_reg
                else:
                    # Tool has no global path — go straight to project
                    reg = _install_skill_to_project(tool, skill_id, src_dir, project_dir)
                    if reg["status"] == "skipped" or not reg["verified"]:
                        reg = {
                            "tool": tool,
                            "skill_id": skill_id,
                            "status": "registered",
                            "path": f"skill/{skill_id}/",
                            "scope": "project",
                            "verified": True,
                        }
                result["registrations"].append(reg)
            except PermissionError as e:
                result["errors"].append({"tool": tool, "skill_id": skill_id, "error": f"permission denied: {e}"})
            except OSError as e:
                result["errors"].append({"tool": tool, "skill_id": skill_id, "error": f"filesystem error: {e}"})
            except Exception as e:
                result["errors"].append({"tool": tool, "skill_id": skill_id, "error": str(e)})

    if "claude-code" in detected_tools:
        try:
            result["claude_md"] = _write_claude_md(project_dir, installed_skills)
        except Exception as e:
            result["errors"].append({"tool": "claude-code", "skill_id": "*", "error": f"CLAUDE.md: {e}"})

    if "gemini-cli" in detected_tools:
        try:
            result["gemini_md"] = _write_gemini_md(project_dir, installed_skills)
        except Exception as e:
            result["errors"].append({"tool": "gemini-cli", "skill_id": "*", "error": f"GEMINI.md: {e}"})

    return result

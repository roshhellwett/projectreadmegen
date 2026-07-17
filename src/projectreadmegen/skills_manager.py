import os
import re
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def _resolve_skills_root() -> Path:
    env = os.environ.get("PROJECTREADME_SKILLS_DIR")
    if env:
        return Path(env).resolve()

    script_dir = Path(__file__).resolve()

    candidates = [
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


def _read_skill_md(skill_dir: Path) -> dict:
    """Parse SKILL.md and return metadata dict."""
    result = {"description": "", "risk": "unknown", "source": "", "raw_category": ""}
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return result
    text = skill_md.read_text("utf-8", errors="replace")
    desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if desc_match:
        result["description"] = desc_match.group(1).strip().strip('"')
    risk_match = re.search(r'^risk:\s*(.+?)\s*$', text, re.MULTILINE)
    if risk_match:
        result["risk"] = risk_match.group(1).strip()
    source_match = re.search(r'^source:\s*(.+?)\s*$', text, re.MULTILINE)
    if source_match:
        result["source"] = source_match.group(1).strip()
    cat_match = re.search(r'^category:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if cat_match:
        result["raw_category"] = cat_match.group(1).strip().strip('"')
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
        content += "This directory contains AI agent skills installed for this project.\n"
        content += "This file instructs AI agents on available skills and how to use them.\n\n"
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

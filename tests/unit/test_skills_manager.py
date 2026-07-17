import os
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from projectreadmegen.skills_manager import (
    discover_all_skills,
    search_skills,
    install_skills,
    ensure_agent_md,
)


def test_search_skills_exact_match():
    skills = [
        {
            "id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "category": "Testing",
        },
        {
            "id": "other",
            "name": "Other Skill",
            "description": "Something else",
            "category": "Dev",
        },
    ]
    result = search_skills("test-skill", skills)
    assert len(result) == 1
    assert result[0]["id"] == "test-skill"


def test_search_skills_prefix_match():
    skills = [
        {
            "id": "deployment",
            "name": "Deployment Skill",
            "description": "",
            "category": "DevOps",
        },
        {"id": "debug", "name": "Debug Tool", "description": "", "category": "Dev"},
    ]
    result = search_skills("dep", skills)
    assert len(result) == 1
    assert result[0]["id"] == "deployment"


def test_search_skills_substring_match():
    skills = [
        {
            "id": "my-skill",
            "name": "My Awesome Skill",
            "description": "",
            "category": "Other",
        },
        {"id": "other", "name": "Other", "description": "", "category": "Misc"},
    ]
    result = search_skills("awesome", skills)
    assert len(result) == 1
    assert result[0]["id"] == "my-skill"


def test_search_skills_category_match():
    skills = [
        {"id": "skill1", "name": "Skill One", "description": "", "category": "DevOps"},
        {"id": "skill2", "name": "Skill Two", "description": "", "category": "Testing"},
    ]
    result = search_skills("devops", skills)
    assert len(result) == 1
    assert result[0]["id"] == "skill1"


def test_search_skills_description_match():
    skills = [
        {
            "id": "skill1",
            "name": "S1",
            "description": "This tool helps with deployment",
            "category": "Tools",
        },
        {
            "id": "skill2",
            "name": "S2",
            "description": "Nothing relevant",
            "category": "Tools",
        },
    ]
    result = search_skills("deployment", skills)
    assert len(result) == 1
    assert result[0]["id"] == "skill1"


def test_search_skills_no_match():
    skills = [{"id": "abc", "name": "ABC", "description": "", "category": "X"}]
    result = search_skills("zzzz", skills)
    assert result == []


def test_search_skills_empty_query():
    skills = [{"id": "a", "name": "A", "description": "", "category": "X"}]
    result = search_skills("", skills)
    assert result == skills


def test_search_skills_scoring_order():
    skills = [
        {"id": "z-match", "name": "Exact Match", "description": "", "category": "X"},
        {
            "id": "a-match",
            "name": "Another Exact Match",
            "description": "",
            "category": "X",
        },
    ]
    result = search_skills("exact match", skills)
    assert len(result) >= 2


def test_discover_all_skills_no_root():
    with patch(
        "projectreadmegen.skills_manager._SKILLS_ROOT", Path("/nonexistent/path")
    ):
        result = discover_all_skills()
        assert result == []


@pytest.fixture
def skills_fs(tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    cat = skills_root / "Testing"
    cat.mkdir()
    skill_dir = cat / "test-skill"
    skill_dir.mkdir()
    md = skill_dir / "SKILL.md"
    md.write_text(
        'description: "A test skill"\nrisk: low\nsource: https://example.com\n',
        encoding="utf-8",
    )
    return skills_root


def test_discover_all_skills_found(skills_fs):
    with patch("projectreadmegen.skills_manager._SKILLS_ROOT", skills_fs):
        result = discover_all_skills()
        assert len(result) == 1
        assert result[0]["id"] == "test-skill"
        assert result[0]["name"] == "Test Skill"
        assert result[0]["description"] == "A test skill"
        assert result[0]["category"] == "Testing"
        assert result[0]["risk"] == "low"


def test_discover_all_skills_excludes_other_category(skills_fs):
    (skills_fs / "Other").mkdir()
    with patch("projectreadmegen.skills_manager._SKILLS_ROOT", skills_fs):
        result = discover_all_skills()
        assert len(result) == 1


def test_install_skills_skill_not_found(tmp_path):
    with patch("projectreadmegen.skills_manager.discover_all_skills", return_value=[]):
        result = install_skills(str(tmp_path), ["nonexistent"])
        assert len(result["errors"]) == 1
        assert result["errors"][0]["error"] == "Skill not found"


def test_install_skills_source_missing(skills_fs, tmp_path):
    with patch("projectreadmegen.skills_manager._SKILLS_ROOT", skills_fs):
        with patch("projectreadmegen.skills_manager.discover_all_skills") as mock_disc:
            mock_disc.return_value = [
                {
                    "id": "ghost",
                    "name": "Ghost",
                    "description": "",
                    "category": "Testing",
                    "_path": str(skills_fs / "Testing" / "ghost"),
                }
            ]
            result = install_skills(str(tmp_path), ["ghost"])
            assert len(result["errors"]) == 1


def test_install_skills_success(skills_fs, tmp_path):
    with patch("projectreadmegen.skills_manager._SKILLS_ROOT", skills_fs):
        result = install_skills(str(tmp_path), ["test-skill"])
        assert len(result["installed"]) == 1
        assert result["installed"][0]["status"] == "installed"
        assert (tmp_path / "skill" / "test-skill" / "SKILL.md").exists()


def test_install_skills_already_installed(skills_fs, tmp_path):
    (tmp_path / "skill" / "test-skill").mkdir(parents=True)
    with patch("projectreadmegen.skills_manager._SKILLS_ROOT", skills_fs):
        result = install_skills(str(tmp_path), ["test-skill"])
        assert result["installed"][0]["status"] == "already_installed"


def test_ensure_agent_md_creates_new(tmp_path):
    installed = [{"id": "test-skill", "status": "installed"}]
    (tmp_path / "skill" / "test-skill").mkdir(parents=True)
    (tmp_path / "skill" / "test-skill" / "SKILL.md").write_text(
        'description: "A test skill"\n', encoding="utf-8"
    )
    result = ensure_agent_md(str(tmp_path), installed)
    assert result == str(tmp_path / "agent.md")
    content = (tmp_path / "agent.md").read_text()
    assert "Test Skill" in content
    assert "skill/test-skill/" in content


def test_ensure_agent_md_appends_to_existing(tmp_path):
    agent_md = tmp_path / "agent.md"
    agent_md.write_text(
        "# Skills Configuration\n\n## Installed Skills\n\n### Existing Skill\n- **Path**: `skill/existing/`\n",
        encoding="utf-8",
    )
    installed = [{"id": "new-skill", "status": "installed"}]
    (tmp_path / "skill" / "new-skill").mkdir(parents=True)
    (tmp_path / "skill" / "new-skill" / "SKILL.md").write_text(
        'description: "A new skill"\n', encoding="utf-8"
    )
    result = ensure_agent_md(str(tmp_path), installed)
    content = (tmp_path / "agent.md").read_text()
    assert "Existing Skill" in content
    assert "New Skill" in content


def test_ensure_agent_md_no_duplicates(tmp_path):
    installed = [
        {"id": "test-skill", "status": "installed"},
        {"id": "test-skill", "status": "installed"},
    ]
    (tmp_path / "skill" / "test-skill").mkdir(parents=True)
    (tmp_path / "skill" / "test-skill" / "SKILL.md").write_text(
        'description: "A test skill"\n', encoding="utf-8"
    )
    result = ensure_agent_md(str(tmp_path), installed)
    content = (tmp_path / "agent.md").read_text()
    assert content.count("Test Skill") == 1

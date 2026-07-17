import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from projectreadmegen import usagetracker


def test_project_readme_info_round_trips(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    project = tmp_path / "project"
    project.mkdir()
    readme = project / "README.md"
    readme.write_text("# Demo\n", encoding="utf-8")

    monkeypatch.setattr(usagetracker, "get_cache_file_path", lambda: cache_file)

    usagetracker.save_project_cache(str(project), {"template": "full"})
    usagetracker.save_project_readme_info(str(project), str(readme))
    info = usagetracker.get_project_readme_info(str(project))

    assert info["last_readme_mtime"] is not None
    assert info["last_readme_hash"] is not None
    assert info["last_generate_time"] is not None


def test_usage_data_reads_legacy_file(tmp_path, monkeypatch):
    current = tmp_path / "projectreadmegen_usage.json"
    legacy = tmp_path / "+projectreadmegen_usage.json"
    legacy.write_text('{"user_key_set": true}', encoding="utf-8")

    monkeypatch.setattr(usagetracker, "get_usage_file_path", lambda: current)
    monkeypatch.setattr(usagetracker, "get_legacy_usage_file_path", lambda: legacy)

    assert usagetracker.load_usage_data()["user_key_set"] is True

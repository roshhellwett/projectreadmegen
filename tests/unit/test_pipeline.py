import pytest
from pathlib import Path
from projectreadmegen.pipeline import (
    PipelineConfig,
    PipelineResult,
    run_pipeline,
    save_pipeline_result,
)


def test_pipeline_config_defaults():
    cfg = PipelineConfig()
    assert cfg.path == "."
    assert cfg.use_ai is False
    assert cfg.template is None
    assert cfg.max_depth == 3
    assert cfg.dry_run is False
    assert cfg.force is False


def test_pipeline_result_defaults():
    result = PipelineResult(
        readme_content="# README",
        scan_result={"name": "test", "files": [], "dirs": [], "tree": ""},
        detection={"primary_lang": "Python", "languages": [], "project_type": "app"},
        config={"template": "standard"},
    )
    assert result.readme_content == "# README"
    assert result.mode == "template"
    assert result.ai_fallback_used is False
    assert result.output_path is None


def test_run_pipeline_invalid_path():
    cfg = PipelineConfig(path="/nonexistent/path/12345")
    from projectreadmegen.exceptions import InvalidPathError

    with pytest.raises(InvalidPathError):
        run_pipeline(cfg)


def test_run_pipeline_file_not_directory(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    cfg = PipelineConfig(path=str(f))
    from projectreadmegen.exceptions import InvalidPathError

    with pytest.raises(InvalidPathError):
        run_pipeline(cfg)


def test_run_pipeline_normal(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')")
    (tmp_path / "requirements.txt").write_text("typer")
    cfg = PipelineConfig(
        path=str(tmp_path),
        template="minimal",
        author="Tester",
        include_badges=False,
        include_tree=False,
    )
    result = run_pipeline(cfg)
    assert result.readme_content
    assert "Tester" in result.readme_content or "Tester" in result.config["author"]
    assert result.mode == "template"
    assert result.scan_result["name"]


def test_run_pipeline_ai_fallback(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("print('hi')")
    from projectreadmegen import ai_provider

    def fail_ai(*a, **kw):
        from projectreadmegen.exceptions import APIError

        raise APIError("API down")

    monkeypatch.setattr(ai_provider, "generate_ai_readme", fail_ai)
    cfg = PipelineConfig(path=str(tmp_path), use_ai=True, template="standard")
    result = run_pipeline(cfg)
    assert result.readme_content
    assert result.mode == "template" or result.ai_fallback_used


def test_run_pipeline_with_overrides(tmp_path):
    (tmp_path / "index.js").write_text("console.log('hi')")
    (tmp_path / "package.json").write_text('{"name": "test"}')
    cfg = PipelineConfig(
        path=str(tmp_path),
        template="full",
        output_file="CUSTOM_README.md",
        github_username="testuser",
    )
    result = run_pipeline(cfg)
    assert result.config["output_file"] == "CUSTOM_README.md"
    assert result.config["github_username"] == "testuser"


def test_save_pipeline_result(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')")
    cfg = PipelineConfig(path=str(tmp_path), template="standard")
    result = run_pipeline(cfg)
    output = tmp_path / "README.md"
    result.output_path = str(output)
    save_pipeline_result(result)
    assert output.exists()
    content = output.read_text()
    assert len(content) > 0


def test_save_pipeline_result_no_output_path():
    result = PipelineResult(
        readme_content="# README",
        scan_result={"name": "test", "files": [], "dirs": [], "tree": ""},
        detection={"primary_lang": "Python", "languages": [], "project_type": "app"},
        config={"template": "standard"},
    )
    with pytest.raises(ValueError, match="output_path"):
        save_pipeline_result(result)

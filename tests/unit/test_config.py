import json
import pytest
from projectreadmegen.config import load_config


def test_load_config_defaults(tmp_path):
    result = load_config(str(tmp_path))
    assert result["template"] == "standard"
    assert result["output_file"] == "README.md"
    assert result["include_tree"] is True
    assert result["max_tree_depth"] == 3


def test_load_config_with_file(tmp_path):
    config = {"template": "full", "author": "Test Author"}
    config_path = tmp_path / "readmegen.config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    result = load_config(str(tmp_path))
    assert result["template"] == "full"
    assert result["author"] == "Test Author"
    assert result["output_file"] == "README.md"


def test_load_config_unknown_keys_ignored(tmp_path):
    config = {"nonexistent_key": "value", "template": "minimal"}
    config_path = tmp_path / "readmegen.config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    result = load_config(str(tmp_path))
    assert result["template"] == "minimal"
    assert "nonexistent_key" not in result


def test_load_config_malformed_json(tmp_path):
    config_path = tmp_path / "readmegen.config.json"
    config_path.write_text("{invalid json}", encoding="utf-8")
    from projectreadmegen.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError):
        load_config(str(tmp_path))


def test_load_config_not_a_file(tmp_path):
    config_path = tmp_path / "readmegen.config.json"
    config_path.mkdir()
    result = load_config(str(tmp_path))
    assert result["template"] == "standard"


def test_load_config_non_dict_json(tmp_path):
    config_path = tmp_path / "readmegen.config.json"
    config_path.write_text('["list", "not", "dict"]', encoding="utf-8")
    from projectreadmegen.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError, match="expected dict"):
        load_config(str(tmp_path))


def test_load_config_io_error(tmp_path, monkeypatch):
    from projectreadmegen.exceptions import ConfigurationError
    def broken_open(*args, **kwargs):
        raise OSError("Permission denied")
    monkeypatch.setattr("builtins.open", broken_open)
    config_path = tmp_path / "readmegen.config.json"
    config_path.write_text('{"template": "full"}', encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(str(tmp_path))

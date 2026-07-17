from pathlib import Path
import pytest
from projectreadmegen.utils import (
    is_symlink_chain,
    sanitize_path,
    validate_writeable_path,
    validate_readable_path,
    safe_create_backup,
    truncate_string,
    validate_project_name,
)


def test_is_symlink_chain_no_symlink(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    assert is_symlink_chain(f) is False


def test_sanitize_path_valid(tmp_path):
    f = tmp_path / "subdir" / "file.txt"
    f.parent.mkdir()
    f.write_text("hello")
    result = sanitize_path(str(f))
    assert result == f.resolve()


def test_sanitize_path_empty():
    with pytest.raises(ValueError, match="non-empty"):
        sanitize_path("")


def test_sanitize_path_none():
    with pytest.raises(ValueError, match="non-empty"):
        sanitize_path(None)


def test_validate_writeable_path_file_exists(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("data")
    ok, msg = validate_writeable_path(f)
    assert ok is True
    assert msg == ""


def test_validate_writeable_path_parent_exists(tmp_path):
    f = tmp_path / "new_file.txt"
    ok, msg = validate_writeable_path(f)
    assert ok is True


def test_validate_writeable_path_parent_missing(tmp_path):
    f = tmp_path / "nonexistent" / "file.txt"
    ok, msg = validate_writeable_path(f)
    assert ok is False
    assert "Parent directory" in msg


def test_validate_readable_path_exists(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("data")
    ok, msg = validate_readable_path(f)
    assert ok is True


def test_validate_readable_path_not_exists(tmp_path):
    f = tmp_path / "does_not_exist.txt"
    ok, msg = validate_readable_path(f)
    assert ok is False
    assert "does not exist" in msg


def test_safe_create_backup_new_file(tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("original")
    backup = safe_create_backup(f)
    assert backup is not None
    assert backup.name == "readme.backup.md"
    assert not f.exists()


def test_safe_create_backup_file_not_exists(tmp_path):
    f = tmp_path / "nonexistent.md"
    backup = safe_create_backup(f)
    assert backup is None


def test_truncate_string_short():
    assert truncate_string("hello", 10) == "hello"


def test_truncate_string_long():
    result = truncate_string("hello world this is long", 10)
    assert len(result) == 10
    assert result.endswith("...")


def test_truncate_string_exact():
    assert truncate_string("1234567890", 10) == "1234567890"


def test_validate_project_name_valid():
    ok, msg = validate_project_name("my-project")
    assert ok is True
    assert msg == ""


def test_validate_project_name_empty():
    ok, msg = validate_project_name("")
    assert ok is False


def test_validate_project_name_none():
    ok, msg = validate_project_name(None)
    assert ok is False


def test_validate_project_name_too_long():
    ok, msg = validate_project_name("a" * 300)
    assert ok is False
    assert "too long" in msg


def test_validate_project_name_invalid_chars():
    ok, msg = validate_project_name("my<project>")
    assert ok is False
    assert "invalid character" in msg

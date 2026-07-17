from projectreadmegen.constants import (
    LANG_PATTERNS,
    LICENSE_NAMES,
    SKIP_DIRS,
    SKIP_FILES,
    VALID_TEMPLATES,
    VALID_CONFIG_KEYS,
    DEFAULT_CONFIG,
    USAGE_FILE,
    DEFAULT_AI_MODEL,
    TEMPLATES_DIR,
)


def test_lang_patterns_contains_python():
    assert "Python" in LANG_PATTERNS
    assert "*.py" in LANG_PATTERNS["Python"]


def test_lang_patterns_contains_javascript():
    assert "JavaScript" in LANG_PATTERNS
    assert "*.js" in LANG_PATTERNS["JavaScript"]


def test_lang_patterns_all_values_are_lists():
    for key, val in LANG_PATTERNS.items():
        assert isinstance(val, list), f"{key} patterns should be a list"


def test_license_names_contains_mit():
    assert LICENSE_NAMES["LICENSE-MIT"] == "MIT"


def test_skip_dirs_contains_node_modules():
    assert "node_modules" in SKIP_DIRS


def test_skip_dirs_contains_git():
    assert ".git" in SKIP_DIRS


def test_skip_dirs_is_set():
    assert isinstance(SKIP_DIRS, set)


def test_skip_files_contains_ds_store():
    assert ".DS_Store" in SKIP_FILES


def test_skip_files_is_set():
    assert isinstance(SKIP_FILES, set)


def test_valid_templates():
    assert "minimal" in VALID_TEMPLATES
    assert "standard" in VALID_TEMPLATES
    assert "full" in VALID_TEMPLATES
    assert "academic" in VALID_TEMPLATES
    assert len(VALID_TEMPLATES) == 4


def test_valid_config_keys():
    assert "template" in VALID_CONFIG_KEYS
    assert VALID_CONFIG_KEYS["template"] == str
    assert VALID_CONFIG_KEYS["include_tree"] == bool


def test_default_config():
    assert DEFAULT_CONFIG["template"] == "standard"
    assert DEFAULT_CONFIG["output_file"] == "README.md"
    assert DEFAULT_CONFIG["include_tree"] is True


def test_usage_file():
    assert USAGE_FILE == "projectreadmegen_usage.json"


def test_default_ai_model():
    assert DEFAULT_AI_MODEL == "llama-3.3-70b-versatile"


def test_templates_dir():
    assert TEMPLATES_DIR == "templates"

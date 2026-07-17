from projectreadmegen.badges import lang_badge, license_badge, build_badge_line


def test_lang_badge_python():
    result = lang_badge("Python")
    assert "Python" in result
    assert "3776AB" in result
    assert "shields.io" in result


def test_lang_badge_javascript():
    result = lang_badge("JavaScript")
    assert "JavaScript" in result
    assert "F7DF1E" in result


def test_lang_badge_unknown():
    result = lang_badge("Unknown")
    assert "Unknown" in result
    assert "555555" in result


def test_lang_badge_cplusplus():
    result = lang_badge("C++")
    assert "C%2B%2B" in result


def test_license_badge_mit():
    result = license_badge("MIT")
    assert "MIT" in result
    assert "License" in result


def test_license_badge_apache():
    result = license_badge("Apache-2.0")
    assert "Apache" in result


def test_license_badge_none():
    assert license_badge("None") == ""


def test_license_badge_unknown():
    assert license_badge("Unknown") == ""


def test_license_badge_empty():
    assert license_badge("") == ""


def test_build_badge_line_with_lang_and_license():
    detection = {"primary_lang": "Python", "license": "MIT"}
    result = build_badge_line(detection)
    assert "Python" in result
    assert "MIT" in result


def test_build_badge_line_only_lang():
    detection = {"primary_lang": "TypeScript", "license": "None"}
    result = build_badge_line(detection)
    assert "TypeScript" in result
    assert "shields.io" in result


def test_build_badge_line_only_license():
    detection = {"primary_lang": "Unknown", "license": "Apache-2.0"}
    result = build_badge_line(detection)
    assert "Apache" in result


def test_build_badge_line_neither():
    detection = {"primary_lang": "Unknown", "license": "None"}
    result = build_badge_line(detection)
    assert result == ""

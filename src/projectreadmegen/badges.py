# src/badges.py


def lang_badge(language: str) -> str:
    """Return a language badge."""
    colors = {
        "Python":     "3776AB",
        "JavaScript": "F7DF1E",
        "TypeScript": "3178C6",
        "C++":        "00599C",
        "C":          "A8B9CC",
        "Rust":       "000000",
        "Go":         "00ADD8",
        "Java":       "007396",
        "HTML/CSS":   "E34F26",
        "Shell":      "4EAA25",
        "PowerShell": "5391FE",
    }
    color = colors.get(language, "555555")
    label = language.replace("+", "%2B").replace("/", "%2F").replace(" ", "%20")
    return f"![Language](https://img.shields.io/badge/Language-{label}-{color})"


def license_badge(license_id: str) -> str:
    """Return a license badge."""
    if license_id in ["None", "Unknown", ""]:
        return ""
    label = license_id.replace("-", "--").replace(" ", "%20")
    return f"![License](https://img.shields.io/badge/License-{label}-blue)"


def platform_badge(platform: str) -> str:
    """Return a platform badge (Linux, Windows, Cross-Platform)."""
    colors = {
        "Linux":         "FCC624",
        "Windows":       "0078D6",
        "Cross-Platform":"brightgreen",
    }
    color = colors.get(platform, "lightgrey")
    return f"![Platform](https://img.shields.io/badge/Platform-{platform}-{color})"


def build_badge_line(detection: dict) -> str:
    """
    Build the full badge line for a README from detection results.

    Parameters:
        detection (dict): Output from detector.detect_stack().

    Returns:
        str: One line of Markdown with all relevant badges space-separated.
    """
    badges = []
    
    lang = detection.get("primary_lang", "")
    if lang and lang != "Unknown":
        badges.append(lang_badge(lang))
    
    lic = detection.get("license", "None")
    if lic and lic != "None":
        b = license_badge(lic)
        if b:
            badges.append(b)
    
    return "  ".join(badges)


if __name__ == "__main__":
    print(lang_badge("Python"))
    print(lang_badge("C++"))
    print(license_badge("MIT"))
    print(build_badge_line({"primary_lang": "TypeScript", "license": "MIT"}))
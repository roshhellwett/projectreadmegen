# src/generator.py

import sys
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from projectreadmegen.badges import build_badge_line

logger = logging.getLogger(__name__)


def generate_readme(scan_result: dict, detection: dict, config: dict) -> str:
    """
    Generate a complete README.md string from scan + detection data.

    Parameters:
        scan_result (dict): Output from scanner.scan_directory().
        detection   (dict): Output from detector.detect_stack().
        config      (dict): Merged config from scanner.load_config().

    Returns:
        str: Full README.md content as a string.
    """
    from projectreadmegen.config import VALID_TEMPLATES
    
    template_name   = config.get("template", "standard")
    template_file   = f"{template_name}.md.j2"
    templates_dir   = Path(__file__).parent / "templates"
    
    if template_name not in VALID_TEMPLATES:
        logger.warning(f"Unknown template '{template_name}', using 'standard'")
        template_name = "standard"
        template_file = f"{template_name}.md.j2"
    
    if not (templates_dir / template_file).exists():
        logger.error(f"Template '{template_file}' not found in {templates_dir}")
        raise FileNotFoundError(
            f"Template '{template_file}' not found in {templates_dir}. "
            f"Available: {', '.join(VALID_TEMPLATES)}"
        )
    
    logger.debug(f"Using template: {template_name}")
    
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    template = env.get_template(template_file)
    
    context = {
        "project_name":    _format_title(scan_result["name"]),
        "project_raw_name": scan_result["name"],
        "description":     detection["description_hint"],
        "author":          config.get("author", ""),
        "github_username": config.get("github_username", ""),
        
        "badge_line":      build_badge_line(detection) if config.get("include_badges") else "",
        
        "primary_lang":    detection["primary_lang"],
        "all_languages":   detection["languages"],
        "project_type":    detection["project_type"],
        
        "install_cmd":     detection["install_cmd"],
        "run_cmd":         detection["run_cmd"],
        
        "folder_tree":     scan_result["tree"] if config.get("include_tree") else "",
        
        "has_license":      scan_result["has_license"],
        "has_contributing": scan_result["has_contributing"],
        "has_tests":        detection["has_tests"],
        "has_docs":         detection["has_docs"],
        "license_id":       detection["license"],
    }
    
    logger.debug(f"Rendering template with context keys: {list(context.keys())}")
    
    return template.render(**context)


def save_readme(content: str, output_path: str) -> None:
    """
    Write the generated README content to a file.

    Parameters:
        content (str): The full README Markdown string.
        output_path (str): Full path where README.md should be written.
    """
    logger.info(f"Writing README to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"README successfully written ({len(content)} characters)")


def _format_title(raw_name: str) -> str:
    """
    Convert a folder name like 'projectreadmegen' or 'my-project'
    into a display title like 'Projectreadmegen' or 'My Project'.
    """
    return raw_name.replace("-", " ").replace("_", " ").title()
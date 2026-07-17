# src/projectreadmegen/pipeline.py
#
# Single source of truth for the scan → detect → generate → save pipeline.
#
# Every UI surface (CLI quick-mode, interactive-mode, CLI commands, web API)
# should call through here instead of reimplementing the pipeline.

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from projectreadmegen.scanner import scan_directory
from projectreadmegen.detector import detect_stack
from projectreadmegen.generator import generate_readme, save_readme
from projectreadmegen.config import load_config
from projectreadmegen.ai_provider import generate_ai_readme
from projectreadmegen import usagetracker

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a README generation pipeline run."""

    readme_content: str
    scan_result: dict
    detection: dict
    config: dict
    output_path: Optional[str] = None
    mode: str = "template"  # "template" or "ai"
    ai_fallback_used: bool = False


@dataclass
class PipelineConfig:
    """User-facing configuration for a pipeline run."""

    path: str = "."
    use_ai: bool = False
    template: Optional[str] = None
    output_file: Optional[str] = None
    max_depth: int = 3
    include_badges: bool = True
    include_tree: bool = True
    author: str = ""
    github_username: str = ""
    dry_run: bool = False
    force: bool = False


def run_pipeline(cfg: PipelineConfig) -> PipelineResult:
    """
    Execute the full scan → detect → generate pipeline.

    This is the single canonical pipeline that all UI surfaces should call.

    Args:
        cfg: Pipeline configuration.

    Returns:
        PipelineResult with the generated README and all metadata.

    Raises:
        projectreadmegen.exceptions.InvalidPathError: If path is invalid.
        projectreadmegen.exceptions.ConfigurationError: If config is bad.
        projectreadmegen.exceptions.APIError: If AI generation fails (and no fallback).
    """
    from projectreadmegen.exceptions import InvalidPathError, APIError

    root = Path(cfg.path).resolve()

    # Validate path
    if not root.exists():
        raise InvalidPathError(
            f"Directory does not exist: {root}",
            f"The path '{cfg.path}' does not exist. Please check the path and try again.",
        )
    if not root.is_dir():
        raise InvalidPathError(
            f"Path is not a directory: {root}",
            f"'{cfg.path}' is a file, not a directory. Please provide a directory path.",
        )

    # Load config from readmegen.config.json, merge with overrides
    config = load_config(str(root))

    if cfg.template:
        config["template"] = cfg.template
    if cfg.output_file:
        config["output_file"] = cfg.output_file
    config["max_tree_depth"] = cfg.max_depth
    config["include_badges"] = cfg.include_badges
    config["include_tree"] = cfg.include_tree
    if cfg.author:
        config["author"] = cfg.author
    if cfg.github_username:
        config["github_username"] = cfg.github_username

    # Scan
    scan = scan_directory(str(root), max_depth=config["max_tree_depth"])

    # Detect
    detection = detect_stack(scan)

    # Generate
    ai_fallback_used = False
    mode = "ai" if cfg.use_ai else "template"

    if cfg.use_ai:
        try:
            readme = generate_ai_readme(scan, detection, config)
        except (APIError, Exception) as e:
            logger.warning(f"AI generation failed, falling back to template: {e}")
            readme = generate_readme(scan, detection, config)
            ai_fallback_used = True
            mode = "template"
    else:
        readme = generate_readme(scan, detection, config)

    # Compute output path
    output_path = str(root / config["output_file"])

    return PipelineResult(
        readme_content=readme,
        scan_result=scan,
        detection=detection,
        config=config,
        output_path=output_path,
        mode=mode,
        ai_fallback_used=ai_fallback_used,
    )


def save_pipeline_result(result: PipelineResult) -> None:
    """Save the pipeline result to disk and update caches.

    Args:
        result: A completed PipelineResult with output_path set.
    """
    if not result.output_path:
        raise ValueError("output_path must be set before saving")

    save_readme(result.readme_content, result.output_path)

    # Track per-project metadata
    root_path = result.scan_result.get("root", ".")
    usagetracker.save_project_cache(
        root_path, {"template": result.config.get("template", "standard")}
    )
    usagetracker.save_project_readme_info(root_path, result.output_path)

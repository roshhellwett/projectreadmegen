"""
Production utilities for robust path handling, validation, and safety checks.
"""

import os
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def is_symlink_chain(path: Path, max_depth: int = 10) -> bool:
    """
    Check if a path is part of a symlink chain (circular or too deep).
    
    Args:
        path: Path to check
        max_depth: Maximum allowed symlink depth
        
    Returns:
        True if symlink chain detected, False otherwise
    """
    try:
        visited = set()
        current = path.resolve()
        depth = 0
        
        while depth < max_depth:
            if current in visited:
                logger.warning(f"Circular symlink detected: {current}")
                return True
            visited.add(current)
            
            if current.is_symlink():
                current = current.resolve()
                depth += 1
            else:
                break
        
        if depth >= max_depth:
            logger.warning(f"Symlink chain too deep for: {path}")
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error checking symlinks for {path}: {e}")
        return False


def sanitize_path(path: str) -> Path:
    """
    Sanitize and validate a file path.
    
    Args:
        path: Path string to sanitize
        
    Returns:
        Resolved Path object
        
    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")
    
    # Resolve to absolute path
    resolved = Path(path).resolve()
    
    # Check for symlink attacks
    if is_symlink_chain(resolved):
        raise ValueError(f"Symlink chain detected in path: {path}")
    
    return resolved


def validate_writeable_path(path: Path) -> Tuple[bool, str]:
    """
    Check if a path (or its parent directory) is writeable.
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (is_writeable, error_message)
    """
    try:
        # If path exists, check if it's writeable
        if path.exists():
            if not path.is_file():
                return False, f"Path exists but is not a file: {path}"
            if not os.access(path, os.W_OK):
                return False, f"No write permission for file: {path}"
        else:
            # Check if parent directory is writeable
            parent = path.parent
            if not parent.exists():
                return False, f"Parent directory does not exist: {parent}"
            if not os.access(parent, os.W_OK):
                return False, f"No write permission for directory: {parent}"
        
        return True, ""
    except Exception as e:
        return False, f"Error checking path permissions: {e}"


def validate_readable_path(path: Path) -> Tuple[bool, str]:
    """
    Check if a path is readable.
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (is_readable, error_message)
    """
    try:
        if not path.exists():
            return False, f"Path does not exist: {path}"
        
        if not os.access(path, os.R_OK):
            return False, f"No read permission: {path}"
        
        return True, ""
    except Exception as e:
        return False, f"Error checking path: {e}"


def estimate_disk_space_needed(file_size: int) -> Tuple[bool, str]:
    """
    Check if there's enough disk space for a file.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (has_space, error_message)
    """
    try:
        import shutil
        
        # Get the home directory stats
        stat = shutil.disk_usage(Path.home())
        
        # We need at least 10x the file size as buffer
        if stat.free < (file_size * 10):
            needed_mb = (file_size * 10) / (1024 * 1024)
            free_mb = stat.free / (1024 * 1024)
            return False, f"Low disk space. Need ~{needed_mb:.1f}MB, have {free_mb:.1f}MB"
        
        return True, ""
    except Exception as e:
        logger.warning(f"Error checking disk space: {e}")
        # Don't fail on disk check errors
        return True, ""


def safe_create_backup(file_path: Path) -> Path | None:
    """
    Create a backup of an existing file before overwriting.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file, or None if backup not needed
    """
    if not file_path.exists():
        return None
    
    try:
        backup_path = file_path.with_stem(f"{file_path.stem}.backup")
        file_path.rename(backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")
        return None


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Safely truncate a string for display/logging.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string with ellipsis if needed
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def validate_project_name(name: str) -> Tuple[bool, str]:
    """
    Validate a project name.
    
    Args:
        name: Project name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Project name must be a non-empty string"
    
    if len(name) > 255:
        return False, "Project name too long (max 255 characters)"
    
    # Allow common project name characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in name:
            return False, f"Project name contains invalid character: {char}"
    
    return True, ""

# src/projectreadmegen/__init__.py

"""
projectreadmegen - Auto-generate README files from folder structure

Usage:
    projectreadmegen generate <path> --template standard
"""

__version__ = "6.0.0"

try:
    from projectreadmegen import usagetracker
    # Auto-sync persistent credentials from disk (~/.projectreadmegen_usage.json) into os.environ
    usagetracker.get_api_key()
    usagetracker.get_github_token()
except Exception:
    pass

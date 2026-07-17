import sys
from pathlib import Path
import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


def pytest_collection_modifyitems(items):
    """Automatically assign markers based on parent directory (unit, smoke, e2e)."""
    for item in items:
        path_str = str(item.fspath).replace("\\", "/")
        if "/unit/" in path_str:
            item.add_marker(pytest.mark.unit)
        elif "/smoke/" in path_str:
            item.add_marker(pytest.mark.smoke)
        elif "/e2e/" in path_str:
            item.add_marker(pytest.mark.e2e)

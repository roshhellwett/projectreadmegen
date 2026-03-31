# tests/test_scanner.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from projectreadmegen.scanner import scan_directory, load_config


class TestScanner:
    def test_scan_directory_returns_dict(self):
        """Test that scan_directory returns a dictionary with expected keys."""
        result = scan_directory("examples/sample-cpp-project", max_depth=2)
        
        assert isinstance(result, dict)
        assert "root" in result
        assert "name" in result
        assert "files" in result
        assert "dirs" in result
        assert "tree" in result
        assert "file_extensions" in result
    
    def test_scan_cpp_project_detects_extensions(self):
        """Test that scanner detects .cpp extensions."""
        result = scan_directory("examples/sample-cpp-project", max_depth=2)
        
        assert ".cpp" in result["file_extensions"]
    
    def test_scan_python_bot_detects_py(self):
        """Test that scanner detects Python files."""
        result = scan_directory("examples/sample-python-bot", max_depth=2)
        
        assert ".py" in result["file_extensions"]
        assert "requirements.txt" in result["files"]
    
    def test_scan_web_project_detects_json(self):
        """Test that scanner detects web project files."""
        result = scan_directory("examples/sample-web-project", max_depth=2)
        
        assert ".json" in result["file_extensions"]
    
    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config("examples/sample-cpp-project")
        
        assert isinstance(config, dict)
        assert "template" in config
    
    def test_scan_nonexistent_path_raises(self):
        """Test that scanning a nonexistent path raises an error."""
        with pytest.raises(Exception):
            scan_directory("nonexistent/path/12345")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
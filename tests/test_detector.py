# tests/test_detector.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from projectreadmegen.detector import detect_stack


class TestDetector:
    def test_detect_python_project(self):
        """Test detection of Python project."""
        scan_result = {
            "files": ["main.py", "requirements.txt", "setup.py"],
            "dirs": ["tests", "src"],
            "file_extensions": [".py", ".txt"],
            "name": "my-python-bot",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert "Python" in result["languages"]
        assert result["primary_lang"] == "Python"
    
    def test_detect_cpp_project(self):
        """Test detection of C++ project."""
        scan_result = {
            "files": ["main.cpp", "CMakeLists.txt", "Makefile"],
            "dirs": ["src", "include"],
            "file_extensions": [".cpp", ".txt"],
            "name": "cpp-app",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert "C++" in result["languages"]
        assert result["primary_lang"] == "C++"
    
    def test_detect_typescript_project(self):
        """Test detection of TypeScript project."""
        scan_result = {
            "files": ["index.ts", "tsconfig.json", "package.json"],
            "dirs": ["src", "components"],
            "file_extensions": [".ts", ".json"],
            "name": "web-app",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert "TypeScript" in result["languages"]
        assert result["primary_lang"] == "TypeScript"
    
    def test_detect_telegram_bot(self):
        """Test detection of telegram bot project."""
        scan_result = {
            "files": ["bot.py", "requirements.txt"],
            "dirs": ["tests"],
            "file_extensions": [".py", ".txt"],
            "name": "telegram-bot",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert result["project_type"] == "telegram-bot"
    
    def test_detect_web_app(self):
        """Test detection of web application."""
        scan_result = {
            "files": ["package.json", "index.html", "tsconfig.json"],
            "dirs": ["src", "public", "components"],
            "file_extensions": [".json", ".html", ".ts"],
            "name": "my-web-app",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert result["project_type"] == "web-app"
    
    def test_detect_cli_tool(self):
        """Test detection of CLI tool."""
        scan_result = {
            "files": ["cli.py", "setup.py", "requirements.txt"],
            "dirs": ["tests"],
            "file_extensions": [".py", ".txt"],
            "name": "my-cli-tool",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert result["project_type"] == "cli-tool"
    
    def test_detect_has_tests(self):
        """Test that has_tests is detected correctly."""
        scan_result = {
            "files": ["main.py"],
            "dirs": ["tests", "src"],
            "file_extensions": [".py"],
            "name": "test-project",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert result["has_tests"] is True
    
    def test_detect_has_docs(self):
        """Test that has_docs is detected correctly."""
        scan_result = {
            "files": ["main.py"],
            "dirs": ["docs", "src"],
            "file_extensions": [".py"],
            "name": "doc-project",
            "root": "/path/to/project"
        }
        
        result = detect_stack(scan_result)
        
        assert result["has_docs"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    
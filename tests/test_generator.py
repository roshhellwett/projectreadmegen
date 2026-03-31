# tests/test_generator.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from projectreadmegen.generator import generate_readme


class TestGenerator:
    def test_generate_minimal_template(self):
        """Test that minimal template produces non-empty output."""
        scan_result = {
            "name": "test-project",
            "tree": "├── src/\n│   └── main.py",
            "has_license": False,
            "has_contributing": False,
        }
        
        detection = {
            "primary_lang": "Python",
            "languages": ["Python"],
            "project_type": "cli-tool",
            "description_hint": "A Python project — Test Project.",
            "install_cmd": "pip install -r requirements.txt",
            "run_cmd": "python main.py",
            "has_tests": False,
            "has_docs": False,
            "license": "None",
        }
        
        config = {
            "template": "minimal",
            "include_badges": False,
            "include_tree": True,
            "max_tree_depth": 3,
            "author": "Test Author",
            "github_username": "testuser",
        }
        
        result = generate_readme(scan_result, detection, config)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test Project" in result
    
    def test_generate_standard_template(self):
        """Test that standard template produces output."""
        scan_result = {
            "name": "my-cli-tool",
            "tree": "├── main.py",
            "has_license": True,
            "has_contributing": False,
        }
        
        detection = {
            "primary_lang": "Python",
            "languages": ["Python"],
            "project_type": "cli-tool",
            "description_hint": "A CLI tool written in Python.",
            "install_cmd": "pip install .",
            "run_cmd": "python cli.py",
            "has_tests": True,
            "has_docs": False,
            "license": "MIT",
        }
        
        config = {
            "template": "standard",
            "include_badges": True,
            "include_tree": True,
            "max_tree_depth": 2,
            "author": "",
            "github_username": "developer",
        }
        
        result = generate_readme(scan_result, detection, config)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_full_template(self):
        """Test that full template produces output."""
        scan_result = {
            "name": "web-app",
            "tree": "src/\n  index.ts",
            "has_license": True,
            "has_contributing": True,
        }
        
        detection = {
            "primary_lang": "TypeScript",
            "languages": ["TypeScript", "JavaScript"],
            "project_type": "web-app",
            "description_hint": "A web application built with TypeScript.",
            "install_cmd": "npm install",
            "run_cmd": "npm run dev",
            "has_tests": True,
            "has_docs": True,
            "license": "Apache-2.0",
        }
        
        config = {
            "template": "full",
            "include_badges": True,
            "include_tree": True,
            "max_tree_depth": 3,
            "author": "Dev",
            "github_username": "devuser",
        }
        
        result = generate_readme(scan_result, detection, config)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_academic_template(self):
        """Test that academic template produces output."""
        scan_result = {
            "name": "academic-project",
            "tree": "main.py",
            "has_license": False,
            "has_contributing": False,
        }
        
        detection = {
            "primary_lang": "Python",
            "languages": ["Python"],
            "project_type": "unknown",
            "description_hint": "A Python project.",
            "install_cmd": "pip install -r requirements.txt",
            "run_cmd": "python main.py",
            "has_tests": False,
            "has_docs": False,
            "license": "None",
        }
        
        config = {
            "template": "academic",
            "include_badges": False,
            "include_tree": True,
            "max_tree_depth": 2,
            "author": "Student",
            "github_username": "student",
        }
        
        result = generate_readme(scan_result, detection, config)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_invalid_template_raises(self):
        """Test that invalid template falls back to standard."""
        scan_result = {"name": "test", "tree": "", "has_license": False, "has_contributing": False}
        detection = {"primary_lang": "Python", "languages": ["Python"], "project_type": "unknown", "description_hint": "A Python project.", "install_cmd": "", "run_cmd": "", "has_tests": False, "has_docs": False, "license": "None"}
        config = {"template": "nonexistent", "include_badges": False, "include_tree": False, "max_tree_depth": 3, "author": "", "github_username": ""}
        
        result = generate_readme(scan_result, detection, config)
        assert isinstance(result, str)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
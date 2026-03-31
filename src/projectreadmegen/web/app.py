# src/web/app.py

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, request, jsonify
from src.scanner import scan_directory, load_config
from src.detector import detect_stack
from src.generator import generate_readme

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    """Render the main input page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Accept a folder tree string (textarea input),
    run the generator, return rendered README as JSON.
    """
    data = request.get_json()
    tree_txt = data.get("tree", "").strip()
    template = data.get("template", "standard")
    author = data.get("author", "")
    username = data.get("github_username", "")
    
    if not tree_txt:
        return jsonify({"error": "No folder tree provided."}), 400
    
    scan_result = _parse_tree_to_scan(tree_txt)
    
    config = {
        "template": template,
        "include_badges": True,
        "include_tree": True,
        "max_tree_depth": 3,
        "output_file": "README.md",
        "author": author,
        "github_username": username,
    }
    
    detection = detect_stack(scan_result)
    readme = generate_readme(scan_result, detection, config)
    
    return jsonify({
        "readme": readme,
        "language": detection["primary_lang"],
        "type": detection["project_type"],
        "license": detection["license"],
    })


def _parse_tree_to_scan(tree_text: str) -> dict:
    """
    Parse a pasted ASCII folder tree into a minimal scan_result dict.
    """
    lines = tree_text.strip().splitlines()
    files = []
    dirs = []
    extensions = set()
    
    project_name = lines[0].strip().rstrip("/") if lines else "my-project"
    
    for line in lines[1:]:
        name = line.replace("|--", "").replace("`--", "").replace("|", "").replace(" ", "").strip()
        
        if not name:
            continue
        
        if "." in name:
            files.append(name)
            ext = "." + name.split(".")[-1].lower()
            extensions.add(ext)
        else:
            dirs.append(name)
    
    return {
        "root": "",
        "name": project_name,
        "files": files,
        "dirs": dirs,
        "tree": "\n".join(lines[1:]),
        "has_license": any(f in files for f in ["LICENSE", "LICENSE.md", "license"]),
        "has_contributing": any("contributing" in f.lower() for f in files),
        "has_gitignore": ".gitignore" in files,
        "has_existing_readme": any(f.lower() == "readme.md" for f in files),
        "file_extensions": sorted(list(extensions)),
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
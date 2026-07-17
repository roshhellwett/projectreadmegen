# src/projectreadmegen/server.py

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from projectreadmegen.scanner import scan_directory, load_config
from projectreadmegen.detector import detect_stack
from projectreadmegen.generator import generate_readme
from projectreadmegen.grok import GrokClient, build_project_context, generate_ai_readme
from projectreadmegen.github_profile import (
    validate_github_username,
    fetch_github_user,
    fetch_user_repos,
    calculate_language_stats,
    build_profile_context,
    get_style_prompt,
    generate_readme_content as generate_profile_readme_content,
)
from projectreadmegen import usagetracker, __version__
from projectreadmegen.exceptions import APIError as CustomAPIError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Project README Gen Studio API",
    description="State-of-the-art Web Studio and API bridge for projectreadmegen.",
    version=__version__,
)

# Enable CORS — restricted to local dev origins only (security: no wildcard)
_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Request Models
class ScanRequest(BaseModel):
    path: str = Field(default=".", description="Path to directory to scan")
    use_cache: bool = Field(default=True, description="Whether to use scanner cache")
    max_depth: Optional[int] = Field(default=3, description="Maximum directory traversal depth")

class GenerateRequest(BaseModel):
    scan_result: Dict[str, Any]
    detection: Dict[str, Any]
    config: Dict[str, Any] = Field(default_factory=dict)

class GenerateAIRequest(BaseModel):
    scan_result: Optional[Dict[str, Any]] = None
    detection: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    path: Optional[str] = "."
    model: str = "llama-3.3-70b-versatile"
    tone: str = "professional"
    custom_instructions: str = ""

class GitHubProfileRequest(BaseModel):
    username: str
    style: str = "professional"
    token: Optional[str] = None
    custom_tagline: Optional[str] = ""

class APIKeyRequest(BaseModel):
    api_key: str = Field(..., description="Groq API Key (starts with gsk_)")

class GraphChatRequest(BaseModel):
    node_id: str
    node_label: str
    node_type: str
    node_path: Optional[str] = None
    node_summary: Optional[str] = None
    connected_imports: List[str] = []
    connected_imported_by: List[str] = []
    connected_children: List[str] = []
    parent_label: Optional[str] = None
    message: str = ""
    history: List[Dict[str, str]] = []
    model: str = "llama-3.3-70b-versatile"
    web_search: bool = False


# API Endpoints
@app.get("/api/status")
async def get_status():
    """Get server status, API key status, and usage metrics."""
    unified = usagetracker.get_unified_status_dict()
    return {
        "version": __version__,
        **unified,
    }


@app.post("/api/key")
async def set_api_key(req: APIKeyRequest):
    """Set or update the Groq API key."""
    key = req.api_key.strip()
    if not key or not key.startswith("gsk_") or len(key) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Groq API key format. Must start with 'gsk_'."
        )
    usagetracker.save_api_key(key)
    return {"status": "success", "message": "API key updated successfully!"}


# Configurable workspace root for path-traversal protection
_WORKSPACE_ROOT = Path.cwd().resolve()


def _validate_scan_path(raw_path: str) -> Path:
    """Validate and resolve a scan path on the local filesystem.

    Allows both relative paths (from current workspace) and absolute paths (like D:\\project or /home/user/project)
    so local developers can scan any directory on their system from both CLI and Web Studio.

    Raises:
        HTTPException: 404 if directory doesn't exist or isn't a valid directory.
    """
    stripped = raw_path.strip() or "."
    resolved = Path(stripped).resolve()

    if not resolved.exists() or not resolved.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: '{resolved}'. Please verify the folder path exists on your system.",
        )

    return resolved


@app.post("/api/scan")
async def api_scan_project(req: ScanRequest):
    """Scan a project directory and detect tech stack."""
    resolved_path = _validate_scan_path(req.path)

    try:
        scan_res = scan_directory(str(resolved_path), max_depth=req.max_depth or 3, use_cache=req.use_cache)
        detection_res = detect_stack(scan_res)
        config_res = load_config(str(resolved_path))
        
        return {
            "status": "success",
            "scan_result": scan_res,
            "detection": detection_res,
            "config": config_res,
            "resolved_path": str(resolved_path),
        }
    except Exception as e:
        logger.error(f"Error scanning directory {resolved_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan directory: {str(e)}"
        )


@app.post("/api/generate")
async def api_generate_readme(req: GenerateRequest):
    """Generate template-based README.md from scan & detection data."""
    try:
        content = generate_readme(req.scan_result, req.detection, req.config)
        return {
            "status": "success",
            "readme": content,
            "template_used": req.config.get("template", "standard"),
        }
    except Exception as e:
        logger.error(f"Error generating README: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate README: {str(e)}"
        )


@app.post("/api/generate-ai")
async def api_generate_ai_readme(req: GenerateAIRequest):
    """Generate AI-powered README using Groq API."""
    api_key = usagetracker.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Groq API key not configured. Please add your key in the Dashboard or Menu option 3."
        )
    
    try:
        scan_res = req.scan_result
        detection_res = req.detection
        config_res = req.config or {}
        
        if not scan_res or not detection_res:
            resolved_path = _validate_scan_path(req.path or ".")
            scan_res = scan_directory(str(resolved_path), use_cache=True)
            detection_res = detect_stack(scan_res)
            config_res = load_config(str(resolved_path))
        
        client = GrokClient(api_key=api_key)
        context = build_project_context(scan_res, detection_res, config_res)
        
        tone_prompts = {
            "professional": "Your tone is authoritative, highly polished, polished corporate/industry standard, and clean.",
            "technical": "Your tone is deeply technical, focusing on architecture, APIs, performance characteristics, and developer exactness.",
            "enthusiastic": "Your tone is vibrant, welcoming, modern, and engaging, encouraging developers to star, use, and contribute.",
            "concise": "Your tone is ultra-concise, direct, bullet-focused, and minimal without fluff.",
        }
        tone_desc = tone_prompts.get(req.tone.lower(), tone_prompts["professional"])
        
        system_prompt = f"""You are a world-class technical writer and AI software architect specializing in creating stunning, industry-standard README files for software projects.
{tone_desc}
- Use proper Markdown hierarchy with clear section headers (`#`, `##`, `###`).
- Include syntax-highlighted code blocks with accurate language identifiers.
- Format tech stacks, badges, features, and folder structures cleanly.
- Be specific, actionable, and visually stunning."""

        if req.custom_instructions:
            system_prompt += f"\n\nUSER CUSTOM INSTRUCTIONS:\n{req.custom_instructions}"
            
        readme_content = client.generate_readme(
            project_context=context,
            system_prompt=system_prompt,
            model=req.model,
            max_tokens=4500,
        )
        
        return {
            "status": "success",
            "readme": readme_content,
            "model_used": req.model,
        }
    except CustomAPIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error in AI generation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/github-profile")
async def api_generate_github_profile(req: GitHubProfileRequest):
    """Generate GitHub Profile README using live GitHub API and Groq AI."""
    api_key = usagetracker.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Groq API key not configured. Please set it in the Dashboard."
        )
    
    username = req.username.strip()
    is_valid, msg = validate_github_username(username)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    
    profile_url = f"https://github.com/{username}"
    
    try:
        user_data = fetch_github_user(username, token=req.token)
        repos = fetch_user_repos(username, token=req.token)
        languages = calculate_language_stats(repos) if repos else {}
        
        readme_content = generate_profile_readme_content(
            username=username,
            profile_url=profile_url,
            style=req.style,
            user_data=user_data,
            repos=repos,
            languages=languages,
        )
        
        if req.custom_tagline and "readme-typing-svg" in readme_content:
            import re
            readme_content = re.sub(
                r'lines=[^&]+',
                f'lines={req.custom_tagline.replace(" ", "+")}',
                readme_content
            )
            
        return {
            "status": "success",
            "readme": readme_content,
            "user_data": user_data,
            "languages": languages,
            "style_used": req.style,
        }
    except Exception as e:
        logger.error(f"Error generating GitHub profile README: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile generation failed: {str(e)}"
        )


@app.post("/api/ai/graph-chat")
async def api_graph_chat(req: GraphChatRequest):
    """Interactive AI architectural audit and grounded codebase chat."""
    api_key = usagetracker.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Groq API key not configured. Please set your API key in the API Dashboard tab."
        )

    try:
        # --- File reading: full content for code, skip for binaries ---
        file_preview = ""
        if req.node_path:
            p = Path(req.node_path)
            if p.exists() and p.is_file():
                suffix = p.suffix.lower()
                binary_exts = {'.png','.jpg','.jpeg','.gif','.bmp','.ico','.svg','.webp',
                               '.pdf','.exe','.dll','.so','.dylib','.bin','.dat',
                               '.zip','.tar','.gz','.rar','.7z',
                               '.mp3','.mp4','.avi','.mov','.wav','.ogg',
                               '.woff','.woff2','.ttf','.eot',
                               '.pyc','.pyo','.pyd','.obj','.o','.class'}
                if suffix in binary_exts:
                    file_preview = f"\n\n[Binary or image file — cannot preview contents. Filename: {req.node_path}]"
                else:
                    try:
                        MAX_FILE_BYTES = 100_000  # ~100KB limit
                        with open(p, "rb") as f:
                            raw = f.read(MAX_FILE_BYTES)
                        text = raw.decode("utf-8", errors="replace")
                        if len(raw) >= MAX_FILE_BYTES:
                            text += "\n\n[File truncated at 100KB]"
                        file_preview = f"\n\nFULL FILE ({req.node_path}):\n```\n" + text + "\n```"
                    except Exception:
                        file_preview = f"\n\n[Could not read file: {req.node_path}]"

        # --- Optional web search ---
        web_context = ""
        if req.web_search and req.message:
            try:
                import requests as http_req
                query = f"programming {req.message} {req.node_label}"
                encoded = __import__('urllib.parse').quote(query)
                resp = http_req.get(
                    f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1",
                    timeout=10
                )
                if resp.status_code == 200:
                    ddg = resp.json()
                    results = []
                    if ddg.get("AbstractText"):
                        results.append(ddg["AbstractText"])
                    if ddg.get("RelatedTopics"):
                        for t in ddg["RelatedTopics"][:5]:
                            if isinstance(t, dict) and "Text" in t:
                                results.append(t["Text"])
                    if results:
                        web_context = "\n\nWeb search results for your query:\n" + "\n".join(f"- {r}" for r in results)
            except Exception as exc:
                web_context = f"\n\n[Web search unavailable: {exc}]"

        system_prompt = f"""You are an AI coding assistant pair-programming with a developer. Talk naturally — like a smart colleague, not a corporate document.

# Context about the selected node
- Label: {req.node_label}
- Type: {req.node_type.upper()}
- Path: {req.node_path or 'Root Workspace'}
- Summary: {req.node_summary or 'No summary provided'}
- Parent: {req.parent_label or 'Root'}
- Imports ({len(req.connected_imports)}): {', '.join(req.connected_imports) if req.connected_imports else 'None'}
- Imported by ({len(req.connected_imported_by)}): {', '.join(req.connected_imported_by) if req.connected_imported_by else 'None'}
- Sub-elements ({len(req.connected_children)}): {', '.join(req.connected_children[:25]) if req.connected_children else 'None'}{file_preview}{web_context}

# Guidelines
1. Be direct, concise, and conversational. No emojis, no corporate fluff.
2. Adapt your response to the file type: code files get technical analysis; documentation/config files get practical summaries; binary/image files get honest acknowledgment of limitations.
3. Use GitHub Flavored Markdown with code blocks when showing code. Keep it readable.
4. When referencing other files in the project, format them as `filename.ext` (inline code style).
5. If asked for a review, give a practical assessment — what's good, what's not, what to fix.
6. Don't pretend non-code files have imports, coupling, or architecture. Be honest about what the file actually is.
7. If web search results were provided, you may reference them to support your answer."""

        client = GrokClient(api_key=api_key)
        messages = [{"role": "system", "content": system_prompt}]
        for turn in req.history:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        
        user_query = req.message if req.message != "AUDIT" else f"Review this file: what does it do, is it well structured, and what would you improve?"
        messages.append({"role": "user", "content": user_query})

        reply_content = client.generate_graph_chat(messages=messages, model=req.model)
        return {
            "status": "success",
            "reply": reply_content,
            "model_used": req.model
        }
    except CustomAPIError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error in Graph Chat: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =========================================================================
# GIT TRACK ENDPOINTS
# =========================================================================

import subprocess


def _run_git(cmd: list, cwd: str) -> subprocess.CompletedProcess:
    """Run a git command safely with timeout."""
    return subprocess.run(
        ["git"] + cmd,
        capture_output=True, text=True, cwd=cwd,
        timeout=15, errors="replace"
    )


def _resolve_git_dir(raw_path: str) -> str:
    """Resolve path and validate it's a git repo. Returns resolved path string."""
    resolved = _validate_scan_path(raw_path)
    # Quick check: is there a .git folder?
    git_dir = resolved / ".git"
    if not git_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not a git repository: '{resolved}' has no .git directory."
        )
    return str(resolved)


@app.get("/api/git/graph")
async def api_git_graph(dir: str = ".", count: int = 80):
    """Return structured git commit graph with branches and status."""
    repo_path = _resolve_git_dir(dir)

    try:
        # 1. Get commit log with details
        fmt = "HASH:%H%nPARENTS:%P%nAUTHOR:%an%nDATE:%ar%nREFS:%D%nMSG:%s"
        result = _run_git(
            ["log", "--all", f"-{count}", f"--format={fmt}", "--name-only"],
            repo_path
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr.strip() or "git log failed")

        commits = []
        current = None
        files_buf = []

        for line in result.stdout.split("\n"):
            if line.startswith("HASH:"):
                if current:
                    current["files"] = files_buf
                    commits.append(current)
                    files_buf = []
                current = {"hash": line[5:].strip(), "hash_short": line[5:12].strip()[:7]}
            elif line.startswith("PARENTS:"):
                raw = line[8:].strip()
                current["parents"] = raw.split() if raw else []
                current["parents_short"] = [p[:7] for p in (raw.split() if raw else [])]
            elif line.startswith("AUTHOR:"):
                current["author"] = line[7:].strip()
            elif line.startswith("DATE:"):
                current["date_rel"] = line[5:].strip()
            elif line.startswith("REFS:"):
                current["refs"] = line[5:].strip()
            elif line.startswith("MSG:"):
                current["message"] = line[4:].strip()
            elif current is not None and line.strip():
                files_buf.append(line.strip())

        if current:
            current["files"] = files_buf
            commits.append(current)

        # 2. Compute branch colors (stable by name)
        branch_colors = ["#18181b", "#52525b", "#71717a", "#a1a1aa", "#b45309", "#2563eb"]
        branch_map = {}
        col_idx = 0

        def _get_color(name):
            nonlocal col_idx
            if name not in branch_map:
                branch_map[name] = branch_colors[col_idx % len(branch_colors)]
                col_idx += 1
            return branch_map[name]

        branches = []
        seen_branches = set()
        for c in commits:
            ref = c.get("refs", "")
            if ref:
                for part in ref.split(", "):
                    name = part.strip()
                    if " -> " in name:
                        name = name.split(" -> ")[0]
                    if name and name not in seen_branches:
                        seen_branches.add(name)
                        branches.append({
                            "name": name,
                            "color": _get_color(name),
                            "head": c["hash_short"]
                        })

        # 3. Get status
        status_result = _run_git(["status", "--porcelain"], repo_path)
        status = {"modified": [], "staged": [], "untracked": []}
        if status_result.returncode == 0:
            for line in status_result.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue
                code = line[:2].strip()
                path = line[3:].strip()
                if code == "M":
                    status["modified"].append(path)
                elif code in ("A", "?"):
                    status["untracked"].append(path)

        # 4. Resolve HEAD branch name
        head_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        head_branch = head_result.stdout.strip() if head_result.returncode == 0 else "HEAD"

        return {
            "status": "success",
            "commits": commits,
            "branches": branches,
            "git_status": status,
            "head_branch": head_branch,
            "repo_path": repo_path
        }

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system PATH")
    except Exception as e:
        logger.error(f"Git graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/diff")
async def api_git_diff(file: str, hash: str = "", dir: str = "."):
    """Return diff for a file at a specific commit. If hash is empty, use working tree diff."""
    repo_path = _resolve_git_dir(dir)
    clean_file = file.replace('\\', '/')

    try:
        if hash:
            result = _run_git(["show", "--no-color", "--format=", hash, "--", clean_file], repo_path)
            if result.returncode != 0 or not result.stdout.strip():
                fallback = _run_git(["show", "--no-color", hash, "--", clean_file], repo_path)
                if fallback.returncode == 0 and fallback.stdout.strip():
                    result = fallback
        else:
            result = _run_git(["diff", "HEAD", "--no-color", "--", clean_file], repo_path)

        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr.strip() or "git diff failed")

        return {
            "status": "success",
            "diff": result.stdout,
            "file": file,
            "hash": hash
        }

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git diff timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system PATH")
    except Exception as e:
        logger.error(f"Git diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# STATIC FILES SETUP: Serve compiled frontend
# =========================================================================
PACKAGED_DIST = Path(__file__).parent / "web_dist"
REPO_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
FRONTEND_RAW = Path(__file__).parent.parent.parent / "frontend"

ACTIVE_DIST = (
    PACKAGED_DIST
    if (PACKAGED_DIST.exists() and (PACKAGED_DIST / "index.html").exists())
    else (REPO_DIST if (REPO_DIST.exists() and (REPO_DIST / "index.html").exists()) else None)
)

if ACTIVE_DIST:
    if (ACTIVE_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(ACTIVE_DIST / "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_dist_spa(full_path: str):
        file_path = ACTIVE_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(ACTIVE_DIST / "index.html")
elif FRONTEND_RAW.exists() and (FRONTEND_RAW / "index.html").exists():
    app.mount("/src", StaticFiles(directory=str(FRONTEND_RAW / "src")), name="src")
    @app.get("/{full_path:path}")
    async def serve_raw_spa(full_path: str):
        file_path = FRONTEND_RAW / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_RAW / "index.html")

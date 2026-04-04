import os
import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

USAGE_FILE = "+projectreadmegen_usage.json"
FREE_USES_LIMIT = 5
DEFAULT_API_KEY = "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"

GROQ_KEY_INFO = """
=============================================================
         Get Your Own Free Groq API Key
=============================================================

Steps to generate your own API key:
1. Visit: https://console.groq.com/keys
2. Click "Create Key" button
3. Copy the generated key
4. Set it as environment variable:
   
   Windows (PowerShell):
   $env:GROQ_API_KEY="your_key_here"
   
   Windows (CMD):
   set GROQ_API_KEY=your_key_here
   
   Linux/Mac:
   export GROQ_API_KEY=your_key_here

Or add to your project config file (readmegen.config.json):
{"groq_api_key": "your_key_here"}

=============================================================
"""

CACHE_FILE = "+projectreadmegen_cache.json"

def get_usage_file_path():
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / "projectreadmegen" / USAGE_FILE
    return Path.home() / USAGE_FILE

def get_cache_file_path():
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / "projectreadmegen" / CACHE_FILE
    return Path.home() / CACHE_FILE

def load_usage_data():
    path = get_usage_file_path()
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {"uses_today": 0, "date": "", "user_key_set": False}
    return {"uses_today": 0, "date": "", "user_key_set": False}

def save_usage_data(data):
    path = get_usage_file_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Could not save usage data: {e}")

def load_project_cache(project_path):
    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())
    
    if path.exists():
        try:
            with open(path, 'r') as f:
                cache = json.load(f)
                return cache.get(cache_key, {})
        except Exception:
            return {}
    return {}

def save_project_cache(project_path, data):
    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())
    
    try:
        cache = {}
        if path.exists():
            with open(path, 'r') as f:
                cache = json.load(f)
        
        cache[cache_key] = {
            "last_template": data.get("template", "standard"),
            "last_used": str(date.today()),
            "path": cache_key
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Could not save cache: {e}")

def check_free_limit():
    data = load_usage_data()
    today = str(date.today())
    
    if data.get("date") != today:
        data["uses_today"] = 0
        data["date"] = today
    
    user_key = os.environ.get("GROQ_API_KEY") or os.environ.get("groq_api_key")
    if user_key:
        data["user_key_set"] = True
    
    if data.get("user_key_set"):
        return True, "Using your own API key"
    
    if data["uses_today"] >= FREE_USES_LIMIT:
        return False, "exhausted"
    
    data["uses_today"] += 1
    save_usage_data(data)
    remaining = FREE_USES_LIMIT - data["uses_today"]
    return True, f"Free use ({data['uses_today']}/{FREE_USES_LIMIT}), {remaining} remaining today"


def handle_exhausted():
    print("\n" + "="*50)
    print("  Free credits exhausted!")
    print("="*50)
    print("  1 - Wait 24 hours")
    print("  2 - Add your own Groq API key")
    print("="*50)
    
    choice = input("Choose option (1/2): ").strip()
    
    if choice == "2":
        print("\nGet free key at: https://console.groq.com/keys")
        key = input("Paste your Groq API key: ").strip()
        if key and key.startswith("gsk_"):
            os.environ["GROQ_API_KEY"] = key
            data = load_usage_data()
            data["user_key_set"] = True
            save_usage_data(data)
            print("\nAPI key saved! You can now use --ai unlimited times.")
            return True
        else:
            print("Invalid key format. Key should start with 'gsk_'")
            return False
    else:
        print("\nPlease try again after 24 hours.")
        return False

def show_key_setup():
    data = load_usage_data()
    
    if data.get("user_key_set"):
        return
    
    user_key = os.environ.get("GROQ_API_KEY") or os.environ.get("groq_api_key")
    if user_key:
        data["user_key_set"] = True
        save_usage_data(data)
        return
    
    if data.get("setup_shown"):
        return
    
    data["setup_shown"] = True
    save_usage_data(data)
    
    print(GROQ_KEY_INFO)
    
    response = input("Do you want to use your own API key? (y/n): ").strip().lower()
    
    if response == 'y':
        key = input("Paste your Groq API key here: ").strip()
        if key:
            os.environ["GROQ_API_KEY"] = key
            data["user_key_set"] = True
            save_usage_data(data)
            print("Your API key is now set!")
    else:
        print(f"\nUsing free tier: {FREE_USES_LIMIT} uses per day")
        print("After exhausting, either wait 24 hours or get your own key.")

def get_api_key():
    user_key = os.environ.get("GROQ_API_KEY") or os.environ.get("groq_api_key")
    if user_key:
        return user_key
    return DEFAULT_API_KEY


def get_remaining_credits():
    data = load_usage_data()
    today = str(date.today())
    
    if data.get("date") != today:
        remaining = FREE_USES_LIMIT
    else:
        remaining = FREE_USES_LIMIT - data.get("uses_today", 0)
    
    if data.get("user_key_set") or os.environ.get("GROQ_API_KEY"):
        return "[dim]Using your own API key | Powered by Zenith Open Source Projects | Developer - roshhellwett[/dim]"
    
    if remaining > 0:
        return f"[dim]{remaining} free credit(s) remaining today | Powered by Zenith Open Source Projects | Developer - roshhellwett[/dim]"
    else:
        return "[dim]Free credits exhausted | Powered by Zenith Open Source Projects | Developer - roshhellwett[/dim]"


def get_project_last_template(project_path):
    cache = load_project_cache(project_path)
    return cache.get("last_template", "standard")


def get_project_readme_info(project_path):
    """Get README modification time from project cache."""
    cache = load_project_cache(project_path)
    project_data = cache.get(str(Path(project_path).resolve()), {})
    return {
        "last_readme_mtime": project_data.get("last_readme_mtime"),
        "last_readme_hash": project_data.get("last_readme_hash"),
        "last_generate_time": project_data.get("last_generate_time"),
    }


def save_project_readme_info(project_path, readme_path):
    """Save README info for smart update detection."""
    import time
    path = get_cache_file_path()
    cache_key = str(Path(project_path).resolve())
    
    try:
        cache = {}
        if path.exists():
            with open(path, 'r') as f:
                cache = json.load(f)
        
        readme_mtime = 0
        readme_hash = ""
        if Path(readme_path).exists():
            stat = Path(readme_path).stat()
            readme_mtime = stat.st_mtime
            with open(readme_path, 'rb') as f:
                import hashlib
                readme_hash = hashlib.md5(f.read()).hexdigest()[:16]
        
        if cache_key not in cache:
            cache[cache_key] = {}
        
        cache[cache_key].update({
            "last_readme_mtime": readme_mtime,
            "last_readme_hash": readme_hash,
            "last_generate_time": time.time(),
            "path": cache_key
        })
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Could not save README info: {e}")

import sys

if __name__ == "__main__":
    from projectreadmegen import __version__
    
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"projectreadmegen version {__version__}")
        sys.exit(0)
    
    from projectreadmegen.cli import app
    app()

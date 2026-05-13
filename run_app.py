import streamlit.web.cli as stcli
import os, sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # This is the entry point for the packaged executable
    # It tells streamlit to run 'main.py'
    
    main_script = get_resource_path("main.py")
    
    if not os.path.exists(main_script):
        # Fallback for development
        main_script = os.path.join(os.path.dirname(__file__), "main.py")

    sys.argv = [
        "streamlit",
        "run",
        main_script,
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())

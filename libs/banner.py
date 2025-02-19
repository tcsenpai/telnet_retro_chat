from pathlib import Path


def load_banner():
    """Load and return the banner from file."""
    banner_file = Path("data/banner.txt")

    if not banner_file.exists():
        # Return a simple default banner if file doesn't exist
        return """
/======================================\\
|         Welcome to TCServer          |
\\======================================/
"""

    try:
        with open(banner_file, "r") as f:
            return f.read()
    except:
        # Return simple banner if there's any error
        return "Welcome to TCServer\r\n"

"""
Utility functions
"""

import sys
from pathlib import Path

def ensure_requirements():
    """Check if required packages are installed"""
    missing = []
    try:
        import fitz
    except ImportError:
        missing.append("PyMuPDF (fitz)")
    
    try:
        from pptx import Presentation
    except ImportError:
        missing.append("python-pptx")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    if missing:
        print("Missing required packages: " + ", ".join(missing))
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

def slugify_filename(s: str) -> str:
    """Convert string to filesystem-safe filename"""
    return "".join(c if c.isalnum() else "_" for c in s)[:200]
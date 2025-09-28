"""
Configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_URL = os.environ.get("OPENROUTER_API_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL")
VISION_MODEL = os.environ.get("OPENROUTER_VISION_MODEL")

# Image processing
THUMB_MAX_DIM = 1024
THUMB_QUALITY = 70
IMAGE_SEND_MAX_BYTES = int(os.environ.get("IMAGE_SEND_MAX_BYTES", 600_000))

# Web search
MAX_SEARCH_RESULTS = 5
MAX_RESOURCES = 15
USER_AGENT = "Mozilla/5.0 (compatible; PitchDeckAnalyzer/1.0; +https://example.com)"
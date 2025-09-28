"""
Web search and content fetching
"""

from .search import duckduckgo_search
from .fetcher import fetch_page_text

__all__ = ['duckduckgo_search', 'fetch_page_text']
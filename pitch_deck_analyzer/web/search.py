"""
DuckDuckGo search functionality
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote, urljoin
from pitch_deck_analyzer.config import USER_AGENT, MAX_SEARCH_RESULTS

def _unwrap_duckduckgo_redirect(href: str) -> str:
    """Unwrap DuckDuckGo redirect URLs"""
    try:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if 'uddg' in qs:
            return unquote(qs['uddg'][0])
    except Exception:
        pass
    return href

def duckduckgo_search(query: str, max_results: int = MAX_SEARCH_RESULTS):
    """Perform DuckDuckGo search and return cleaned URLs"""
    url = "https://duckduckgo.com/html/"
    headers = {"User-Agent": USER_AGENT}
    
    try:
        resp = requests.get(url, params={"q": query}, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    for a in soup.select("a.result__a"):
        href = a.get('href') or a.get('data-href')
        if not href:
            continue
        href = _unwrap_duckduckgo_redirect(href)
        if href.startswith('/'):
            href = urljoin('https://duckduckgo.com', href)
        links.append(href)
        if len(links) >= max_results:
            break

    if not links:
        for a in soup.select('a[href]'):
            h = a.get('href')
            if h and h.startswith('http'):
                links.append(h)
            if len(links) >= max_results:
                break

    cleaned = []
    seen = set()
    for link in links:
        if not link or link in seen:
            continue
        seen.add(link)
        cleaned.append(link)
    
    return cleaned[:max_results]
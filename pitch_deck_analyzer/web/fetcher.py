"""
Web page content fetching
"""

import requests
from bs4 import BeautifulSoup
from pitch_deck_analyzer.config import USER_AGENT

def fetch_page_text(url: str) -> str:
    """Fetch and extract main text content from web page"""
    headers = {"User-Agent": USER_AGENT}
    
    try:
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        if r.status_code != 200:
            return ""
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    parts = []
    
    if soup.title and soup.title.text:
        parts.append(soup.title.text.strip())
    
    meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if meta and meta.get('content'):
        parts.append(meta.get('content').strip())

    ps = soup.find_all('p')
    for p in ps[:10]:
        txt = p.get_text().strip()
        if txt and len(txt) > 30:
            parts.append(txt)
    
    return "\n\n".join(parts)
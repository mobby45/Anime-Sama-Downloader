"""french-manga: search."""
import re
import json
import time
import base64
import string
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, urljoin, urlencode
from bs4 import BeautifulSoup
from src.var import get_domain, print_status
from src.utils.config.config import get_domain_cookies
from src.sites._utils import dedupe as _dedupe
from src.sites.french_manga import http as _http

def _search_frenchmanga_one(query, headers=None):
    base_site = "https://w16.french-manga.net"
    try:
        r = _http.post(
            f"{base_site}/engine/ajax/search.php",
            data={"query": query},
            timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException:
        return []

    resultats = []
    soup = BeautifulSoup(r.text, "html.parser")
    for carte in soup.select("div.search-item"):
        info = carte.select_one("div.search-info")
        onclick = carte.get("onclick") or ""
        m_id = re.search(r"/(\d+)-", onclick)
        if not info or not m_id:
            continue
        # the title without the date: "One Piece (1999)" -> "One Piece"
        m_titre = re.search(r"[^()]+", info.get_text(strip=True))
        if not m_titre:
            continue
        titre = m_titre.group(0).strip()
        # the series name without "- Saison N ...": the site then returns all its seasons
        titre_base = re.sub(r"\s*[-:]\s*Saison\s*\d+.*$", "", titre, flags=re.I).strip() or titre
        # the URL carries the anime's name: it is all that reaches expand_frenchmanga_url
        url = f"{base_site}/{m_id.group(1)}-x.html?" + urlencode({"title_base": titre_base})

        # match_title: the series name, without "- Saison N" (the fallback compares it with Sonarr's title)
        resultats.append({"title": titre, "url": url, "support": "Anime Supported", "site": "french-manga",
                          "match_title": titre_base})

    return resultats

def search_frenchmanga(queries, headers=None):
    queries = [queries] if isinstance(queries, str) else queries
    return _dedupe([r for q in queries for r in _search_frenchmanga_one(q, headers)])

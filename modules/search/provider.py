"""Search provider for V1.1. Uses DuckDuckGo HTML results; no API key required."""
import re
import urllib.parse
from datetime import datetime
import requests


class SearchProvider:
    SOURCE_DOMAINS = {
        "Behance": "behance.net", "Dribbble": "dribbble.com", "Openclipart": "openclipart.org",
        "Pixabay": "pixabay.com", "GrabCAD": "grabcad.com", "3D ContentCentral": "3dcontentcentral.com",
        "Sketchfab": "sketchfab.com", "Thingiverse": "thingiverse.com", "SVG Repo": "svgrepo.com",
        "Vecteezy": "vecteezy.com", "Freepik": "freepik.com", "TraceParts": "traceparts.com",
        "CADENAS": "cadenas.de", "Autodesk Community": "forums.autodesk.com",
        "Autodesk App Store": "apps.autodesk.com", "Autodesk Knowledge Network": "autodesk.com",
    }

    def __init__(self, config=None, logger=None):
        self.config = config or {}
        self.logger = logger

    def build_search_url(self, keyword, source=None):
        query = keyword
        if source:
            domain = self.SOURCE_DOMAINS.get(source, source)
            if domain and "." in domain:
                query += f" site:{domain}"
        return "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)

    @staticmethod
    def _extract_results(html):
        results = []
        pattern = r'<a[^>]+class=["\']result__a["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        for match in re.finditer(pattern, html, re.I | re.S):
            url = match.group(1)
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            if url.startswith("//"):
                url = "https:" + url
            if "duckduckgo.com/l/?" in url:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                url = parsed.get("uddg", [url])[0]
            results.append({"title": title, "url": url})
        return results

    def search(self, keyword, source=None):
        result = {
            "keyword": keyword, "source": source or "search",
            "search_url": self.build_search_url(keyword, source),
            "found_url": None, "results": [], "checked_at": datetime.now().isoformat(),
        }
        try:
            response = requests.get(result["search_url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            response.raise_for_status()
            results = self._extract_results(response.text)
            result["results"] = results[:5]
            if results:
                result["found_url"] = results[0]["url"]
            if self.logger:
                self.logger.info("Search executed", {"keyword": keyword, "source": source, "found_url": result["found_url"]})
        except Exception as error:
            if self.logger:
                self.logger.warning("Search failed", {"keyword": keyword, "source": source, "error": str(error)})
        return result

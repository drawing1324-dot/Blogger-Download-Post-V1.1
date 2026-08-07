"""Image provider for V1.1: source preview first, Wikimedia Commons fallback."""
from datetime import datetime
import html
import re
import urllib.parse
import requests


class ImageProvider:
    def __init__(self, config, logger=None):
        self.config = config or {}
        self.logger = logger

    @staticmethod
    def _meta_image(page):
        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, page, re.I | re.S)
            if match:
                return html.unescape(match.group(1))
        return None

    def _source_image(self, source_url):
        if not source_url:
            return None
        response = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        image = self._meta_image(response.text)
        return urllib.parse.urljoin(response.url, image) if image else None

    def _wikimedia_image(self, keyword):
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={"action": "query", "generator": "search", "gsrsearch": keyword,
                    "gsrnamespace": 6, "gsrlimit": 1, "prop": "imageinfo",
                    "iiprop": "url", "format": "json"},
            headers={"User-Agent": "BloggerDownloadPostV1.1/1.0"}, timeout=15,
        )
        response.raise_for_status()
        for page in response.json().get("query", {}).get("pages", {}).values():
            image_url = page.get("imageinfo", [{}])[0].get("url")
            if image_url:
                return image_url
        return None

    def find_image(self, keyword, source_url=None):
        result = {"keyword": keyword, "image_url": None, "provider": None,
                  "status": "not_found", "checked_at": datetime.now().isoformat()}
        try:
            image = self._source_image(source_url)
            if image:
                result.update(image_url=image, provider="download_preview", status="found")
                if self.logger: self.logger.info("Image found", result)
                return result
        except Exception as error:
            if self.logger:
                self.logger.warning("Source image failed", {"url": source_url, "error": str(error)})
        try:
            image = self._wikimedia_image(keyword)
            if image:
                result.update(image_url=image, provider="wikimedia", status="found")
        except Exception as error:
            if self.logger:
                self.logger.warning("Wikimedia image failed", {"keyword": keyword, "error": str(error)})
        if self.logger: self.logger.info("Image search completed", result)
        return result

"""Image provider for V1.1: source preview first, Wikimedia Commons fallback."""

from datetime import datetime
import html
import re
import urllib.parse

import requests


class ImageProvider:
    """Find a usable image URL for an article."""

    IMAGE_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".avif",
    )

    IMAGE_CONTENT_TYPES = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/avif",
    )

    def __init__(self, config=None, logger=None):
        self.config = config or {}
        self.logger = logger

    @staticmethod
    def _meta_image(page):
        """Extract an Open Graph/Twitter image URL from HTML."""
        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, page, re.I | re.S)
            if match:
                return html.unescape(match.group(1)).strip()

        return None

    @classmethod
    def _looks_like_image_url(cls, url):
        """Quick URL-level check before making a request."""
        if not url:
            return False

        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()

        # Explicitly reject document/page formats.
        rejected_extensions = (
            ".pdf",
            ".html",
            ".htm",
            ".txt",
            ".doc",
            ".docx",
            ".svg",
        )

        if path.endswith(rejected_extensions):
            return False

        return path.endswith(cls.IMAGE_EXTENSIONS)

    @classmethod
    def _is_image_response(cls, response):
        """Verify that the remote resource is actually an image."""
        content_type = response.headers.get("Content-Type", "").lower()

        if content_type.startswith("image/"):
            return True

        # Some servers do not provide a correct Content-Type.
        return cls._looks_like_image_url(response.url)

    def _validate_image_url(self, image_url):
        """
        Verify that a URL points to an actual usable image.

        Returns the final URL when valid, otherwise None.
        """
        if not image_url:
            return None

        image_url = html.unescape(image_url).strip()
        image_url = urllib.parse.unquote(image_url)

        # Never use a PDF/document as an <img>.
        if not self._looks_like_image_url(image_url):
            return None

        try:
            response = requests.head(
                image_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                allow_redirects=True,
            )

            if response.ok and self._is_image_response(response):
                return response.url

        except Exception:
            pass

        # Some servers reject HEAD. Try a small GET instead.
        try:
            response = requests.get(
                image_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Range": "bytes=0-1024",
                },
                timeout=10,
                allow_redirects=True,
                stream=True,
            )

            if response.ok and self._is_image_response(response):
                return response.url

        except Exception:
            pass

        return None

    def _source_image(self, source_url):
        """Try to extract a real preview image from the source page."""
        if not source_url:
            return None

        response = requests.get(
            source_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()

        image = self._meta_image(response.text)

        if not image:
            return None

        image = urllib.parse.urljoin(response.url, image)

        return self._validate_image_url(image)

    def _wikimedia_image(self, keyword):
        """
        Find a real image from Wikimedia Commons.

        PDF/document results are skipped instead of being returned as
        an <img> source.
        """
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": keyword,
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "iiurlwidth": 1200,
                "format": "json",
            },
            headers={"User-Agent": "BloggerDownloadPostV1.1/1.0"},
            timeout=15,
        )

        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", {})

        for page in pages.values():
            image_info = page.get("imageinfo", [{}])[0]

            mime_type = image_info.get("mime", "").lower()

            # Skip PDFs and other documents.
            if mime_type not in self.IMAGE_CONTENT_TYPES:
                continue

            # Prefer Wikimedia thumbnail when available.
            image_url = image_info.get("thumburl") or image_info.get("url")

            if not image_url:
                continue

            validated_url = self._validate_image_url(image_url)

            if validated_url:
                return validated_url

        return None

    def find_image(self, keyword, source_url=None):
        """
        Find a usable image.

        Priority:
        1. Source page preview image.
        2. Wikimedia Commons image.
        3. No image.
        """
        result = {
            "keyword": keyword,
            "image_url": None,
            "provider": None,
            "status": "not_found",
            "checked_at": datetime.now().isoformat(),
        }

        # ---------------------------------------------------------
        # 1. Try source page preview image
        # ---------------------------------------------------------
        try:
            image = self._source_image(source_url)

            if image:
                result.update(
                    image_url=image,
                    provider="download_preview",
                    status="found",
                )

                if self.logger:
                    self.logger.info("Image found", result)

                return result

        except Exception as error:
            if self.logger:
                self.logger.warning(
                    "Source image failed",
                    {
                        "url": source_url,
                        "error": str(error),
                    },
                )

        # ---------------------------------------------------------
        # 2. Wikimedia Commons fallback
        # ---------------------------------------------------------
        try:
            image = self._wikimedia_image(keyword)

            if image:
                result.update(
                    image_url=image,
                    provider="wikimedia",
                    status="found",
                )

        except Exception as error:
            if self.logger:
                self.logger.warning(
                    "Wikimedia image failed",
                    {
                        "keyword": keyword,
                        "error": str(error),
                    },
                )

        # ---------------------------------------------------------
        # 3. Final result
        # ---------------------------------------------------------
        if self.logger:
            self.logger.info(
                "Image search completed",
                result,
            )

        return result

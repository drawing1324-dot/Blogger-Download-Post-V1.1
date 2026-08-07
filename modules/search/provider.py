"""
Project : Blogger Download Auto Post V1.1
Module  : Image Provider

Version : 1.1.2

หน้าที่:

- ค้นหารูปภาพจาก source URL
- รองรับ fallback image search
- ตรวจสอบว่า URL เป็น image จริง
- ไม่ยอมรับ PDF / HTML / search page เป็น image
- ป้องกัน URL รูปเสียก่อนส่งให้ ArticleWriter
"""

import re
import urllib.parse
from datetime import datetime

import requests


class ImageProvider:

    IMAGE_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
        ".svg",
        ".avif",
    )

    IMAGE_CONTENT_TYPES = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/svg+xml",
        "image/avif",
    )

    BLOCKED_EXTENSIONS = (
        ".pdf",
        ".html",
        ".htm",
        ".txt",
        ".zip",
        ".rar",
        ".7z",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
    )

    SEARCH_ENDPOINTS = (
        "https://www.google.com/search",
        "https://www.bing.com/images/search",
    )

    def __init__(self, config=None, logger=None):

        self.config = config or {}
        self.logger = logger

        self.timeout = (
            self.config
            .get("image", {})
            .get("timeout", 15)
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,"
                    "image/webp,image/apng,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    def _log_info(self, message, data=None):

        if self.logger:
            self.logger.info(
                message,
                data
            )

    def _log_warning(self, message, data=None):

        if self.logger:
            self.logger.warning(
                message,
                data
            )

    # ---------------------------------------------------------
    # URL helpers
    # ---------------------------------------------------------

    @classmethod
    def _is_blocked_extension(cls, url):

        if not url:
            return True

        try:
            parsed = urllib.parse.urlparse(url)

            path = (
                parsed.path
                or ""
            ).lower()

            return path.endswith(
                cls.BLOCKED_EXTENSIONS
            )

        except Exception:

            return True

    @classmethod
    def _has_image_extension(cls, url):

        if not url:
            return False

        try:
            parsed = urllib.parse.urlparse(url)

            path = (
                parsed.path
                or ""
            ).lower()

            return path.endswith(
                cls.IMAGE_EXTENSIONS
            )

        except Exception:

            return False

    @classmethod
    def _is_valid_http_url(cls, url):

        if not url:
            return False

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            if parsed.scheme not in (
                "http",
                "https",
            ):
                return False

            if not parsed.netloc:
                return False

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Content type validation
    # ---------------------------------------------------------

    @classmethod
    def _is_image_content_type(cls, content_type):

        if not content_type:
            return False

        content_type = (
            content_type
            .split(";")[0]
            .strip()
            .lower()
        )

        return (
            content_type
            in cls.IMAGE_CONTENT_TYPES
        )

    # ---------------------------------------------------------
    # Direct image validation
    # ---------------------------------------------------------

    def validate_image_url(self, url):

        if not self._is_valid_http_url(
            url
        ):

            return {
                "valid": False,
                "reason": "invalid_url",
                "url": url,
            }

        if self._is_blocked_extension(
            url
        ):

            return {
                "valid": False,
                "reason": "blocked_extension",
                "url": url,
            }

        try:

            response = self.session.head(
                url,
                allow_redirects=True,
                timeout=self.timeout,
            )

            content_type = (
                response.headers
                .get(
                    "Content-Type",
                    ""
                )
            )

            if (
                response.status_code
                >= 400
            ):

                self._log_warning(
                    "Image URL rejected",
                    {
                        "url": url,
                        "status_code":
                            response.status_code,
                    }
                )

                return {
                    "valid": False,
                    "reason": "http_error",
                    "status_code":
                        response.status_code,
                    "url": url,
                }

            if self._is_image_content_type(
                content_type
            ):

                return {
                    "valid": True,
                    "reason": "image_content_type",
                    "url":
                        response.url or url,
                    "content_type":
                        content_type,
                }

            if self._has_image_extension(
                url
            ):

                return {
                    "valid": True,
                    "reason": "image_extension",
                    "url":
                        response.url or url,
                    "content_type":
                        content_type,
                }

            return {
                "valid": False,
                "reason": "not_an_image",
                "url": url,
                "content_type":
                    content_type,
            }

        except requests.RequestException as error:

            self._log_warning(
                "Image URL validation failed",
                {
                    "url": url,
                    "error": str(error),
                }
            )

            return {
                "valid": False,
                "reason": "request_failed",
                "url": url,
                "error": str(error),
            }

    # ---------------------------------------------------------
    # GET validation
    # ---------------------------------------------------------

    def _validate_image_with_get(
        self,
        url
    ):

        if not self._is_valid_http_url(
            url
        ):

            return None

        if self._is_blocked_extension(
            url
        ):

            return None

        try:

            response = self.session.get(
                url,
                allow_redirects=True,
                stream=True,
                timeout=self.timeout,
            )

            content_type = (
                response.headers
                .get(
                    "Content-Type",
                    ""
                )
            )

            final_url = (
                response.url
                or url
            )

            if (
                response.status_code
                >= 400
            ):

                return None

            if self._is_image_content_type(
                content_type
            ):

                return {
                    "url": final_url,
                    "content_type":
                        content_type,
                    "status_code":
                        response.status_code,
                }

            return None

        except requests.RequestException:

            return None

    # ---------------------------------------------------------
    # Wikimedia
    # ---------------------------------------------------------

    def _extract_wikimedia_image(
        self,
        url
    ):

        if not url:
            return None

        if (
            "wikimedia.org"
            not in url
            and
            "wikipedia.org"
            not in url
        ):

            return None

        if self._is_blocked_extension(
            url
        ):

            self._log_warning(
                "Wikimedia source is not a direct image",
                {
                    "url": url,
                }
            )

            return None

        validation = (
            self._validate_image_with_get(
                url
            )
        )

        if validation:

            return validation["url"]

        return None

    # ---------------------------------------------------------
    # Source image
    # ---------------------------------------------------------

    def _find_source_image(
        self,
        source_url
    ):

        if not source_url:
            return None

        self._log_info(
            "Checking source image",
            {
                "url": source_url,
            }
        )

        if self._is_blocked_extension(
            source_url
        ):

            self._log_warning(
                "Source is not an image",
                {
                    "url": source_url,
                }
            )

            return None

        validation = (
            self.validate_image_url(
                source_url
            )
        )

        if validation.get(
            "valid"
        ):

            return validation.get(
                "url"
            )

        direct = (
            self._validate_image_with_get(
                source_url
            )
        )

        if direct:

            return direct.get(
                "url"
            )

        return self._extract_wikimedia_image(
            source_url
        )

    # ---------------------------------------------------------
    # Search query
    # ---------------------------------------------------------

    @staticmethod
    def _build_query(keyword):

        keyword = (
            keyword
            or ""
        ).strip()

        if not keyword:
            return ""

        return (
            keyword
            + " free image"
        )

    # ---------------------------------------------------------
    # Google image result extraction
    # ---------------------------------------------------------

    @staticmethod
    def _extract_google_images(
        html
    ):

        results = []

        if not html:
            return results

        patterns = [
            r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp|gif))"',
            r'"ou":"(https?://[^"]+)"',
        ]

        for pattern in patterns:

            for match in re.finditer(
                pattern,
                html,
                re.I
            ):

                url = match.group(1)

                url = (
                    url
                    .replace(
                        "\\/",
                        "/"
                    )
                    .replace(
                        "\\u003d",
                        "="
                    )
                    .replace(
                        "\\u0026",
                        "&"
                    )
                )

                if (
                    url
                    and
                    url not in results
                ):

                    results.append(
                        url
                    )

        return results

    # ---------------------------------------------------------
    # Bing image result extraction
    # ---------------------------------------------------------

    @staticmethod
    def _extract_bing_images(
        html
    ):

        results = []

        if not html:
            return results

        patterns = [
            r'"murl":"(https?://[^"]+)"',
            r'"turl":"(https?://[^"]+)"',
        ]

        for pattern in patterns:

            for match in re.finditer(
                pattern,
                html,
                re.I
            ):

                url = match.group(1)

                url = (
                    url
                    .replace(
                        "\\/",
                        "/"
                    )
                    .replace(
                        "\\u0026",
                        "&"
                    )
                )

                if (
                    url
                    and
                    url not in results
                ):

                    results.append(
                        url
                    )

        return results

    # ---------------------------------------------------------
    # Search provider
    # ---------------------------------------------------------

    def _search_engine(
        self,
        endpoint,
        keyword
    ):

        query = self._build_query(
            keyword
        )

        if not query:
            return []

        try:

            response = self.session.get(
                endpoint,
                params={
                    "q": query,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

            html = response.text

            if "google.com" in endpoint:

                return self._extract_google_images(
                    html
                )

            return self._extract_bing_images(
                html
            )

        except requests.RequestException as error:

            self._log_warning(
                "Image search engine failed",
                {
                    "endpoint":
                        endpoint,
                    "keyword":
                        keyword,
                    "error":
                        str(error),
                }
            )

            return []

    # ---------------------------------------------------------
    # Search images
    # ---------------------------------------------------------

    def _search_images(
        self,
        keyword
    ):

        candidates = []

        for endpoint in self.SEARCH_ENDPOINTS:

            results = (
                self._search_engine(
                    endpoint,
                    keyword
                )
            )

            for url in results:

                if url not in candidates:

                    candidates.append(
                        url
                    )

                if len(candidates) >= 20:

                    break

            if len(candidates) >= 20:

                break

        return candidates

    # ---------------------------------------------------------
    # Validate candidates
    # ---------------------------------------------------------

    def _find_valid_candidate(
        self,
        candidates
    ):

        for url in candidates:

            if not self._is_valid_http_url(
                url
            ):

                continue

            if self._is_blocked_extension(
                url
            ):

                continue

            result = (
                self._validate_image_with_get(
                    url
                )
            )

            if result:

                return result.get(
                    "url"
                )

        return None

    # ---------------------------------------------------------
    # Public method
    # ---------------------------------------------------------

    def find_image(
        self,
        keyword,
        source_url=None
    ):

        checked_at = (
            datetime.now()
            .isoformat()
        )

        self._log_info(
            "Starting image search",
            {
                "keyword": keyword,
                "source_url": source_url,
            }
        )

        # -----------------------------------------------------
        # 1. Try source URL
        # -----------------------------------------------------

        if source_url:

            source_image = (
                self._find_source_image(
                    source_url
                )
            )

            if source_image:

                self._log_info(
                    "Source image accepted",
                    {
                        "url":
                            source_image,
                    }
                )

                return {
                    "image_url":
                        source_image,
                    "provider":
                        "source",
                    "status":
                        "found",
                    "checked_at":
                        checked_at,
                }

            self._log_warning(
                "Source image unavailable",
                {
                    "url":
                        source_url,
                }
            )

        # -----------------------------------------------------
        # 2. Fallback image search
        # -----------------------------------------------------

        candidates = (
            self._search_images(
                keyword
            )
        )

        self._log_info(
            "Image search candidates collected",
            {
                "keyword":
                    keyword,
                "candidate_count":
                    len(candidates),
            }
        )

        image_url = (
            self._find_valid_candidate(
                candidates
            )
        )

        if image_url:

            self._log_info(
                "Image search completed",
                {
                    "keyword":
                        keyword,
                    "image_url":
                        image_url,
                    "provider":
                        "image_search",
                    "status":
                        "found",
                }
            )

            return {
                "image_url":
                    image_url,
                "provider":
                    "image_search",
                "status":
                    "found",
                "checked_at":
                    checked_at,
            }

        # -----------------------------------------------------
        # 3. No image
        # -----------------------------------------------------

        self._log_warning(
            "No valid image found",
            {
                "keyword":
                    keyword,
                "source_url":
                    source_url,
            }
        )

        return {
            "image_url":
                None,
            "provider":
                None,
            "status":
                "not_found",
            "checked_at":
                checked_at,
        }

"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.2

หน้าที่:

- ค้นหาแหล่งดาวน์โหลดผ่าน DuckDuckGo HTML
- รองรับการค้นหาแบบระบุ source/domain
- รองรับ fallback endpoint
- ตรวจสอบผลลัพธ์ให้ตรงกับ source
- คืนค่า found_url และ results
- เขียน Log การทำงาน
"""

import re
import urllib.parse
from datetime import datetime

import requests


class SearchProvider:
    """
    Search provider สำหรับระบบ Blogger Download Auto Post V1.1

    ใช้ DuckDuckGo HTML/Lite โดยไม่ต้องใช้ API key
    """

    SOURCE_DOMAINS = {
        "Behance": "behance.net",
        "Dribbble": "dribbble.com",
        "Openclipart": "openclipart.org",
        "Pixabay": "pixabay.com",
        "GrabCAD": "grabcad.com",
        "3D ContentCentral": "3dcontentcentral.com",
        "Sketchfab": "sketchfab.com",
        "Thingiverse": "thingiverse.com",
        "SVG Repo": "svgrepo.com",
        "Vecteezy": "vecteezy.com",
        "Freepik": "freepik.com",
        "TraceParts": "traceparts.com",
        "CADENAS": "cadenas.de",
        "Autodesk Community": "forums.autodesk.com",
        "Autodesk App Store": "apps.autodesk.com",
        "Autodesk Knowledge Network": "autodesk.com",
    }

    ENDPOINTS = (
        "https://html.duckduckgo.com/html/",
        "https://lite.duckduckgo.com/lite/",
    )

    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self, config=None, logger=None):
        self.config = config or {}
        self.logger = logger

        self.timeout = (
            self.config
            .get("search", {})
            .get("timeout", 15)
        )

        self.max_results = (
            self.config
            .get("search", {})
            .get("max_results", 5)
        )

    # =========================================================
    # Logging
    # =========================================================

    def _log_info(self, message, data=None):
        if self.logger:
            self.logger.info(message, data)

    def _log_warning(self, message, data=None):
        if self.logger:
            self.logger.warning(message, data)

    def _log_error(self, message, data=None):
        if self.logger:
            self.logger.error(message, data)

    # =========================================================
    # Search URL
    # =========================================================

    def build_search_url(self, keyword, source=None, endpoint=None):
        """
        สร้าง URL สำหรับ DuckDuckGo
        """

        query = str(keyword or "").strip()

        if source:
            domain = self.SOURCE_DOMAINS.get(
                source,
                source
            )

            if domain and "." in domain:
                query += f" site:{domain}"

        base_url = endpoint or self.ENDPOINTS[0]

        return (
            base_url
            + "?q="
            + urllib.parse.quote_plus(query)
        )

    # =========================================================
    # Domain helpers
    # =========================================================

    @staticmethod
    def _normalize_domain(value):
        """
        แปลง URL/domain ให้เหลือ hostname
        """

        if not value:
            return ""

        value = str(value).strip()

        if not value.startswith(
            ("http://", "https://")
        ):
            value = "https://" + value

        try:
            parsed = urllib.parse.urlparse(value)

            hostname = (
                parsed.hostname
                or ""
            ).lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            return hostname

        except Exception:
            return ""

    @classmethod
    def _url_matches_source(
        cls,
        url,
        source
    ):
        """
        ตรวจสอบว่า URL มาจาก source ที่ร้องขอหรือไม่
        """

        if not url or not source:
            return False

        expected_domain = cls.SOURCE_DOMAINS.get(
            source,
            source
        )

        expected_domain = cls._normalize_domain(
            expected_domain
        )

        actual_domain = cls._normalize_domain(
            url
        )

        if not expected_domain:
            return False

        if not actual_domain:
            return False

        return (
            actual_domain == expected_domain
            or actual_domain.endswith(
                "." + expected_domain
            )
        )

    # =========================================================
    # HTML cleanup
    # =========================================================

    @staticmethod
    def _clean_text(value):
        """
        ล้าง HTML และ whitespace จาก title
        """

        if not value:
            return ""

        value = re.sub(
            r"<[^>]+>",
            "",
            value
        )

        value = (
            value
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    # =========================================================
    # URL extraction
    # =========================================================

    @staticmethod
    def _unwrap_url(url):
        """
        แกะ URL redirect ของ DuckDuckGo
        """

        if not url:
            return None

        url = url.strip()

        if url.startswith("//"):
            url = "https:" + url

        try:
            parsed = urllib.parse.urlparse(url)

            query = urllib.parse.parse_qs(
                parsed.query
            )

            for key in (
                "uddg",
                "url",
                "target"
            ):
                if key in query and query[key]:
                    decoded = urllib.parse.unquote(
                        query[key][0]
                    )

                    if decoded:
                        return decoded

        except Exception:
            pass

        return url

    # =========================================================
    # Result parser
    # =========================================================

    @classmethod
    def _extract_results(cls, html):
        """
        ดึงผลลัพธ์จาก DuckDuckGo HTML

        รองรับทั้งรูปแบบ result__a
        และรูปแบบที่พบใน DuckDuckGo Lite
        """

        results = []

        if not html:
            return results

        # -----------------------------------------------------
        # DuckDuckGo HTML
        # -----------------------------------------------------

        patterns = [
            r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',

            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*result__a[^"\']*["\'][^>]*>(.*?)</a>',
        ]

        for pattern in patterns:

            for match in re.finditer(
                pattern,
                html,
                re.I | re.S
            ):

                url = cls._unwrap_url(
                    match.group(1)
                )

                title = cls._clean_text(
                    match.group(2)
                )

                if not url:
                    continue

                if not title:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        # -----------------------------------------------------
        # DuckDuckGo Lite
        # -----------------------------------------------------

        if not results:

            lite_pattern = (
                r'<a[^>]+href=["\']'
                r'([^"\']+)'
                r'["\'][^>]*>'
                r'(.*?)'
                r'</a>'
            )

            for match in re.finditer(
                lite_pattern,
                html,
                re.I | re.S
            ):

                url = cls._unwrap_url(
                    match.group(1)
                )

                title = cls._clean_text(
                    match.group(2)
                )

                if not url:
                    continue

                if not title:
                    continue

                # ไม่เอา navigation link
                if (
                    "duckduckgo.com"
                    in (
                        cls._normalize_domain(url)
                        or ""
                    )
                ):
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        # -----------------------------------------------------
        # Remove duplicates
        # -----------------------------------------------------

        unique = []
        seen = set()

        for item in results:

            url = item.get("url")

            if not url:
                continue

            key = url.lower()

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    # =========================================================
    # Filter source
    # =========================================================

    @classmethod
    def _filter_source_results(
        cls,
        results,
        source
    ):
        """
        คัดเฉพาะ URL ที่ตรงกับ source
        """

        if not source:
            return results

        matched = []

        for item in results:

            url = item.get("url")

            if cls._url_matches_source(
                url,
                source
            ):
                matched.append(item)

        return matched

    # =========================================================
    # Single request
    # =========================================================

    def _request(
        self,
        keyword,
        source,
        endpoint
    ):
        """
        ยิง request ไปยัง endpoint เดียว
        """

        url = self.build_search_url(
            keyword,
            source,
            endpoint
        )

        self._log_info(
            "Search request started",
            {
                "keyword": keyword,
                "source": source,
                "endpoint": endpoint,
                "url": url
            }
        )

        response = requests.get(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
                "Referer": (
                    "https://duckduckgo.com/"
                ),
            },
            timeout=self.timeout
        )

        content = response.text or ""

        self._log_info(
            "Search HTTP response",
            {
                "status_code": response.status_code,
                "final_url": response.url,
                "content_length": len(content),
                "source": source
            }
        )

        response.raise_for_status()

        return content, response

    # =========================================================
    # Main search
    # =========================================================

    def search(
        self,
        keyword,
        source=None
    ):
        """
        ค้นหา source

        คืนค่า:

        {
            keyword,
            source,
            search_url,
            found_url,
            results,
            checked_at
        }
        """

        result = {
            "keyword": keyword,
            "source": source or "search",
            "search_url": self.build_search_url(
                keyword,
                source
            ),
            "found_url": None,
            "results": [],
            "checked_at": datetime.now().isoformat(),
        }

        diagnosis = {
            "attempts": []
        }

        # -----------------------------------------------------
        # Validate keyword
        # -----------------------------------------------------

        if not keyword:
            self._log_warning(
                "Search skipped - empty keyword",
                {
                    "source": source
                }
            )

            return result

        # -----------------------------------------------------
        # Try endpoints
        # -----------------------------------------------------

        for endpoint in self.ENDPOINTS:

            attempt = {
                "endpoint": endpoint,
                "status_code": None,
                "content_length": 0,
                "error": None,
            }

            try:

                html, response = self._request(
                    keyword,
                    source,
                    endpoint
                )

                attempt["status_code"] = (
                    response.status_code
                )

                attempt["content_length"] = len(
                    html or ""
                )

                all_results = (
                    self._extract_results(html)
                )

                matched_results = (
                    self._filter_source_results(
                        all_results,
                        source
                    )
                )

                attempt["result_count"] = len(
                    all_results
                )

                attempt["matched_count"] = len(
                    matched_results
                )

                diagnosis["attempts"].append(
                    attempt
                )

                # -------------------------------------------------
                # Source matched
                # -------------------------------------------------

                if matched_results:

                    result["results"] = (
                        matched_results[
                            :self.max_results
                        ]
                    )

                    result["found_url"] = (
                        result["results"][0]["url"]
                    )

                    result["search_url"] = (
                        self.build_search_url(
                            keyword,
                            source,
                            endpoint
                        )
                    )

                    self._log_info(
                        "Search source matched",
                        {
                            "keyword": keyword,
                            "source": source,
                            "result_count": len(
                                all_results
                            ),
                            "found_url": (
                                result["found_url"]
                            )
                        }
                    )

                    return result

                # -------------------------------------------------
                # Results exist but wrong source
                # -------------------------------------------------

                if all_results:

                    self._log_warning(
                        "Search results found but source did not match",
                        {
                            "keyword": keyword,
                            "source": source,
                            "result_count": len(
                                all_results
                            ),
                            "results": all_results[
                                :self.max_results
                            ]
                        }
                    )

                else:

                    self._log_warning(
                        "Search returned no results",
                        {
                            "keyword": keyword,
                            "source": source
                        }
                    )

            except requests.RequestException as error:

                attempt["error"] = str(error)

                diagnosis["attempts"].append(
                    attempt
                )

                self._log_warning(
                    "Search request failed",
                    {
                        "keyword": keyword,
                        "source": source,
                        "endpoint": endpoint,
                        "error": str(error)
                    }
                )

            except Exception as error:

                attempt["error"] = str(error)

                diagnosis["attempts"].append(
                    attempt
                )

                self._log_error(
                    "Search parsing failed",
                    {
                        "keyword": keyword,
                        "source": source,
                        "endpoint": endpoint,
                        "error": str(error)
                    }
                )

        # -----------------------------------------------------
        # Nothing matched
        # -----------------------------------------------------

        self._log_warning(
            "Search completed without matching source",
            {
                "keyword": keyword,
                "source": source,
                "result_count": len(
                    result["results"]
                ),
                "found_url": result["found_url"],
                "diagnosis": diagnosis
            }
        )

        return result


__all__ = [
    "SearchProvider"
]

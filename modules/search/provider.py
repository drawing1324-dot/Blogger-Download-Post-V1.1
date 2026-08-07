"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.3

หน้าที่:
- ค้นหาแหล่งดาวน์โหลดจาก Search Engine
- รองรับการจำกัด source ด้วย domain
- รองรับ DuckDuckGo HTML / Lite
- ตรวจสอบผลลัพธ์ให้ตรงกับ source จริง
- ป้องกัน placeholder / redirect ของ DuckDuckGo
- รองรับ HTTP 202
- ส่งผลลัพธ์กลับในรูปแบบเดียวกับระบบเดิม
"""

import re
import urllib.parse
from datetime import datetime
from html import unescape

import requests


class SearchProvider:

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

    SEARCH_ENDPOINTS = (
        "https://html.duckduckgo.com/html/",
        "https://lite.duckduckgo.com/lite/",
    )

    USER_AGENTS = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",

        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36",
    )

    def __init__(self, config=None, logger=None):

        self.config = config or {}
        self.logger = logger

        search_config = self.config.get(
            "search",
            {}
        )

        self.timeout = int(
            search_config.get(
                "timeout",
                15
            )
        )

        self.max_results = int(
            search_config.get(
                "max_results",
                5
            )
        )

    # =========================================================
    # LOGGING
    # =========================================================

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

    def _log_error(self, message, data=None):

        if self.logger:
            self.logger.error(
                message,
                data
            )

    # =========================================================
    # DOMAIN
    # =========================================================

    @classmethod
    def _source_domain(cls, source):

        if not source:
            return None

        return cls.SOURCE_DOMAINS.get(
            source,
            source
        )

    @classmethod
    def _url_matches_source(
        cls,
        url,
        source
    ):

        if not url or not source:
            return False

        domain = cls._source_domain(
            source
        )

        if not domain:
            return False

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            hostname = (
                parsed.hostname
                or ""
            ).lower().strip()

            domain = (
                domain.lower()
                .strip()
            )

            if hostname == domain:
                return True

            if hostname.endswith(
                "." + domain
            ):
                return True

        except Exception:
            return False

        return False

    # =========================================================
    # BUILD SEARCH URL
    # =========================================================

    def build_search_url(
        self,
        keyword,
        source=None,
        endpoint=None
    ):

        query = str(
            keyword or ""
        ).strip()

        if source:

            domain = self.SOURCE_DOMAINS.get(
                source,
                source
            )

            if domain and "." in domain:

                query += (
                    f" site:{domain}"
                )

        endpoint = (
            endpoint
            or self.SEARCH_ENDPOINTS[0]
        )

        return (
            endpoint
            + "?q="
            + urllib.parse.quote_plus(
                query
            )
        )

    # =========================================================
    # DUCKDUCKGO URL
    # =========================================================

    @staticmethod
    def _unwrap_duckduckgo_url(url):

        if not url:
            return None

        url = unescape(
            str(url).strip()
        )

        if url.startswith("//"):
            url = "https:" + url

        # Relative URLs such as /html/ or /lite/
        # are not actual search results.
        if url.startswith("/"):
            return None

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            hostname = (
                parsed.hostname
                or ""
            ).lower()

            if hostname in {
                "duckduckgo.com",
                "www.duckduckgo.com",
            }:

                params = urllib.parse.parse_qs(
                    parsed.query
                )

                target = (
                    params.get(
                        "uddg",
                        [None]
                    )[0]
                    or params.get(
                        "rut",
                        [None]
                    )[0]
                )

                if target:

                    return urllib.parse.unquote(
                        target
                    )

                return None

        except Exception:
            return None

        return url

    # =========================================================
    # CLEAN TITLE
    # =========================================================

    @staticmethod
    def _clean_title(value):

        if not value:
            return ""

        value = re.sub(
            r"<[^>]+>",
            "",
            value
        )

        value = unescape(
            value
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    # =========================================================
    # EXTRACT RESULTS
    # =========================================================

    @classmethod
    def _extract_results(
        cls,
        html
    ):

        if not html:
            return []

        results = []

        # -----------------------------------------------------
        # Standard DDG HTML
        # -----------------------------------------------------

        patterns = [

            r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',

            r'<a[^>]+href=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]*>(.*?)</a>',

        ]

        matches = []

        for pattern in patterns:

            found = re.findall(
                pattern,
                html,
                re.I | re.S
            )

            if found:
                matches.extend(
                    found
                )

        for raw_url, raw_title in matches:

            url = cls._unwrap_duckduckgo_url(
                raw_url
            )

            if not url:
                continue

            title = cls._clean_title(
                raw_title
            )

            if not title:
                continue

            try:

                hostname = (
                    urllib.parse.urlparse(
                        url
                    ).hostname
                    or ""
                ).lower()

                # Never return DDG itself.
                if hostname in {
                    "duckduckgo.com",
                    "www.duckduckgo.com",
                }:
                    continue

            except Exception:
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

            url = item.get(
                "url"
            )

            if not url:
                continue

            if url in seen:
                continue

            seen.add(url)

            unique.append(
                item
            )

        return unique

    # =========================================================
    # FIND MATCHING RESULT
    # =========================================================

    @classmethod
    def _find_matching_result(
        cls,
        results,
        source
    ):

        if not results:
            return None

        for item in results:

            if cls._url_matches_source(
                item.get("url"),
                source
            ):
                return item

        return None

    # =========================================================
    # HTTP REQUEST
    # =========================================================

    def _request(
        self,
        endpoint,
        url
    ):

        headers = {

            "User-Agent":
                self.USER_AGENTS[0],

            "Accept":
                (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),

            "Accept-Language":
                "en-US,en;q=0.9",

            "Referer":
                "https://duckduckgo.com/",

            "Connection":
                "keep-alive",
        }

        self._log_info(
            "Search request started",
            {
                "endpoint": endpoint,
                "url": url
            }
        )

        response = requests.get(
            url,
            headers=headers,
            timeout=self.timeout,
            allow_redirects=True
        )

        content = (
            response.text
            or ""
        )

        self._log_info(
            "Search HTTP response",
            {
                "status_code":
                    response.status_code,

                "final_url":
                    response.url,

                "content_length":
                    len(content)
            }
        )

        return response

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        keyword,
        source=None
    ):

        keyword = str(
            keyword or ""
        ).strip()

        result = {

            "keyword":
                keyword,

            "source":
                source or "search",

            "search_url":
                self.build_search_url(
                    keyword,
                    source
                ),

            "found_url":
                None,

            "results":
                [],

            "checked_at":
                datetime.now().isoformat(),
        }

        if not keyword:

            self._log_warning(
                "Search skipped: empty keyword"
            )

            return result

        attempts = []

        # =====================================================
        # TRY DDG ENDPOINTS
        # =====================================================

        for endpoint in self.SEARCH_ENDPOINTS:

            search_url = self.build_search_url(
                keyword,
                source,
                endpoint
            )

            try:

                response = self._request(
                    endpoint,
                    search_url
                )

                content = (
                    response.text
                    or ""
                )

                attempt = {

                    "endpoint":
                        endpoint,

                    "status_code":
                        response.status_code,

                    "content_length":
                        len(content),

                    "error":
                        None,

                }

                # -------------------------------------------------
                # 202 is not automatically failure.
                # -------------------------------------------------

                results = self._extract_results(
                    content
                )

                attempt[
                    "result_count"
                ] = len(results)

                attempts.append(
                    attempt
                )

                # -------------------------------------------------
                # Only accept source-matching URL.
                # -------------------------------------------------

                matching = self._find_matching_result(
                    results,
                    source
                )

                if matching:

                    result[
                        "results"
                    ] = results[
                        :self.max_results
                    ]

                    result[
                        "found_url"
                    ] = matching[
                        "url"
                    ]

                    self._log_info(
                        "Search source matched",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,

                            "result_count":
                                len(results),

                            "found_url":
                                matching["url"]
                        }
                    )

                    result[
                        "diagnosis"
                    ] = {
                        "attempts":
                            attempts
                    }

                    return result

                self._log_warning(
                    "Search results found but source did not match",
                    {
                        "keyword":
                            keyword,

                        "source":
                            source,

                        "result_count":
                            len(results),

                        "results":
                            results[
                                :self.max_results
                            ]
                    }
                )

            except Exception as error:

                attempt = {

                    "endpoint":
                        endpoint,

                    "status_code":
                        None,

                    "content_length":
                        0,

                    "error":
                        str(error),

                }

                attempts.append(
                    attempt
                )

                self._log_warning(
                    "Search request failed",
                    {
                        "keyword":
                            keyword,

                        "source":
                            source,

                        "endpoint":
                            endpoint,

                        "error":
                            str(error)
                    }
                )

        # =====================================================
        # NOTHING MATCHED
        # =====================================================

        result[
            "diagnosis"
        ] = {
            "attempts":
                attempts
        }

        self._log_warning(
            "Search completed without matching source",
            {
                "keyword":
                    keyword,

                "source":
                    source,

                "result_count":
                    0,

                "found_url":
                    None,

                "diagnosis":
                    result[
                        "diagnosis"
                    ]
            }
        )

        return result

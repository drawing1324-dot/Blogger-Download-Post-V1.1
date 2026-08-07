"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.2

หน้าที่:

- ค้นหาแหล่งดาวน์โหลดจาก Search Engine
- รองรับการจำกัด source ด้วย domain
- รองรับ DuckDuckGo HTML / Lite
- ตรวจสอบผลลัพธ์ให้ตรงกับ source จริง
- ป้องกัน placeholder / redirect ของ DuckDuckGo
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

        self.timeout = int(
            self.config.get(
                "search",
                {}
            ).get(
                "timeout",
                15
            )
        )

        self.max_results = int(
            self.config.get(
                "search",
                {}
            ).get(
                "max_results",
                5
            )
        )

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    def _log_info(self, message, data=None):

        if self.logger:
            self.logger.info(message, data)

    def _log_warning(self, message, data=None):

        if self.logger:
            self.logger.warning(message, data)

    def _log_error(self, message, data=None):

        if self.logger:
            self.logger.error(message, data)

    # ---------------------------------------------------------
    # URL
    # ---------------------------------------------------------

    def build_search_url(
        self,
        keyword,
        source=None,
        endpoint=None
    ):

        query = str(keyword or "").strip()

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
            + urllib.parse.quote_plus(query)
        )

    # ---------------------------------------------------------
    # Domain
    # ---------------------------------------------------------

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
            ).lower()

            domain = domain.lower().strip()

            if hostname == domain:
                return True

            if hostname.endswith(
                "." + domain
            ):
                return True

        except Exception:
            return False

        return False

    # ---------------------------------------------------------
    # DuckDuckGo redirect
    # ---------------------------------------------------------

    @staticmethod
    def _unwrap_duckduckgo_url(url):

        if not url:
            return None

        url = unescape(
            url.strip()
        )

        if url.startswith("//"):
            url = "https:" + url

        # Relative DDG URLs are not actual results.
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

            # DuckDuckGo redirect
            if hostname in {
                "duckduckgo.com",
                "www.duckduckgo.com",
            }:

                params = urllib.parse.parse_qs(
                    parsed.query
                )

                target = (
                    params.get("uddg", [None])[0]
                    or params.get("rut", [None])[0]
                )

                if target:
                    return urllib.parse.unquote(
                        target
                    )

                return None

        except Exception:
            return None

        return url

    # ---------------------------------------------------------
    # HTML cleaning
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # HTML parser
    # ---------------------------------------------------------

    @classmethod
    def _extract_results(
        cls,
        html
    ):

        results = []

        if not html:
            return results

        # -----------------------------------------------------
        # Standard DDG HTML
        # -----------------------------------------------------

        pattern = re.compile(
            r"""
            <a
                [^>]*?
                class\s*=\s*["'][^"']*result__a[^"']*["']
                [^>]*?
                href\s*=\s*["']([^"']+)["']
                [^>]*>
                (.*?)
            </a>
            """,
            re.IGNORECASE
            | re.DOTALL
            | re.VERBOSE
        )

        for match in pattern.finditer(
            html
        ):

            raw_url = match.group(1)
            raw_title = match.group(2)

            url = cls._unwrap_duckduckgo_url(
                raw_url
            )

            title = cls._clean_title(
                raw_title
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
        # Lite / alternate anchor format
        # -----------------------------------------------------

        if not results:

            pattern = re.compile(
                r"""
                <a
                    [^>]*?
                    href\s*=\s*["']([^"']+)["']
                    [^>]*>
                    (.*?)
                </a>
                """,
                re.IGNORECASE
                | re.DOTALL
                | re.VERBOSE
            )

            for match in pattern.finditer(
                html
            ):

                raw_url = match.group(1)
                raw_title = match.group(2)

                url = cls._unwrap_duckduckgo_url(
                    raw_url
                )

                title = cls._clean_title(
                    raw_title
                )

                if not url:
                    continue

                if not title:
                    continue

                # Ignore navigation / DDG pages.
                try:

                    hostname = (
                        urllib.parse.urlparse(
                            url
                        ).hostname
                        or ""
                    ).lower()

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

            url = item["url"]

            if url in seen:
                continue

            seen.add(url)
            unique.append(item)

        return unique

    # ---------------------------------------------------------
    # Search HTTP request
    # ---------------------------------------------------------

    def _request(
        self,
        endpoint,
        url
    ):

        headers = {
            "User-Agent": self.USER_AGENTS[0],
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
            "Connection": "keep-alive",
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

        content = response.text or ""

        self._log_info(
            "Search HTTP response",
            {
                "status_code": response.status_code,
                "final_url": response.url,
                "content_length": len(content)
            }
        )

        return response

    # ---------------------------------------------------------
    # Find matching source
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        keyword,
        source=None
    ):

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

        attempts = []

        keyword = str(
            keyword or ""
        ).strip()

        if not keyword:

            self._log_warning(
                "Search skipped: empty keyword"
            )

            return result

        # -----------------------------------------------------
        # Try all DDG endpoints
        # -----------------------------------------------------

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

                attempt = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "content_length": len(
                        response.text or ""
                    ),
                    "error": None,
                }

                # DDG may return 202 while still giving
                # a usable response. Do not reject solely
                # because of 202.
                if response.status_code >= 400:

                    attempt["error"] = (
                        f"HTTP {response.status_code}"
                    )

                    attempts.append(
                        attempt
                    )

                    self._log_warning(
                        "Search HTTP request failed",
                        {
                            "keyword": keyword,
                            "source": source,
                            "status_code": (
                                response.status_code
                            )
                        }
                    )

                    continue

                results = self._extract_results(
                    response.text
                )

                attempt["result_count"] = len(
                    results
                )

                attempts.append(
                    attempt
                )

                # -------------------------------------------------
                # Source matching
                # -------------------------------------------------

                matching = self._find_matching_result(
                    results,
                    source
                )

                if matching:

                    # Keep a limited list for downstream code.
                    result["results"] = results[
                        :self.max_results
                    ]

                    result["found_url"] = (
                        matching["url"]
                    )

                    result["search_url"] = (
                        search_url
                    )

                    self._log_info(
                        "Search source matched",
                        {
                            "keyword": keyword,
                            "source": source,
                            "result_count": len(
                                results
                            ),
                            "found_url": (
                                matching["url"]
                            )
                        }
                    )

                    return result

                # -------------------------------------------------
                # No matching source
                # -------------------------------------------------

                self._log_warning(
                    "Search results found but source did not match",
                    {
                        "keyword": keyword,
                        "source": source,
                        "result_count": len(
                            results
                        ),
                        "results": results[
                            :self.max_results
                        ]
                    }
                )

            except requests.RequestException as error:

                attempt = {
                    "endpoint": endpoint,
                    "status_code": None,
                    "content_length": 0,
                    "result_count": 0,
                    "error": str(error),
                }

                attempts.append(
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

                attempt = {
                    "endpoint": endpoint,
                    "status_code": None,
                    "content_length": 0,
                    "result_count": 0,
                    "error": str(error),
                }

                attempts.append(
                    attempt
                )

                self._log_error(
                    "Search parser failed",
                    {
                        "keyword": keyword,
                        "source": source,
                        "endpoint": endpoint,
                        "error": str(error)
                    }
                )

        # ---------------------------------------------------------
        # Failed after all endpoints
        # ---------------------------------------------------------

        self._log_warning(
            "Search completed without matching source",
            {
                "keyword": keyword,
                "source": source,
                "result_count": len(
                    result["results"]
                ),
                "found_url": result["found_url"],
                "diagnosis": {
                    "attempts": attempts
                }
            }
        )

        return result

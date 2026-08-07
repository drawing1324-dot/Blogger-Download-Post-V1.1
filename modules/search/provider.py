"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.2.0

หน้าที่:
- ค้นหาแหล่งดาวน์โหลดตาม source/domain
- รองรับ DuckDuckGo HTML
- รองรับ DuckDuckGo Lite fallback
- ตรวจสอบ HTTP response
- ตรวจสอบ URL ที่ได้จริง
- ป้องกันการส่ง URL ปลอมเข้าสู่ Article Writer
"""

import html
import re
import urllib.parse
from datetime import datetime

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

    def __init__(
        self,
        config=None,
        logger=None
    ):

        self.config = config or {}

        self.logger = logger

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language":
                    "en-US,en;q=0.9",
                "Cache-Control":
                    "no-cache",
            }
        )

    def _log_info(
        self,
        message,
        data=None
    ):

        if self.logger:

            self.logger.info(
                message,
                data
            )

    def _log_warning(
        self,
        message,
        data=None
    ):

        if self.logger:

            self.logger.warning(
                message,
                data
            )

    def build_search_url(
        self,
        keyword,
        source=None,
        endpoint=None
    ):

        keyword = (
            keyword or ""
        ).strip()

        query = keyword

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
            + "?"
            + urllib.parse.urlencode(
                {
                    "q": query
                }
            )
        )

    @staticmethod
    def _clean_title(
        value
    ):

        if not value:

            return ""

        value = html.unescape(
            value
        )

        value = re.sub(
            r"<[^>]+>",
            "",
            value
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    @staticmethod
    def _clean_url(
        value
    ):

        if not value:

            return None

        value = html.unescape(
            value
        ).strip()

        if value.startswith("//"):

            value = (
                "https:"
                + value
            )

        try:

            parsed = urllib.parse.urlparse(
                value
            )

            query = urllib.parse.parse_qs(
                parsed.query
            )

            if (
                parsed.netloc
                and
                (
                    parsed.netloc.endswith(
                        "duckduckgo.com"
                    )
                    or
                    parsed.netloc.endswith(
                        "duck.com"
                    )
                )
            ):

                uddg = query.get(
                    "uddg"
                )

                if uddg:

                    value = uddg[0]

        except Exception:

            return None

        value = urllib.parse.unquote(
            value
        ).strip()

        if not re.match(
            r"^https?://",
            value,
            re.I
        ):

            return None

        try:

            parsed = urllib.parse.urlparse(
                value
            )

            if not parsed.netloc:

                return None

        except Exception:

            return None

        return value

    @classmethod
    def _extract_html_results(
        cls,
        page_html
    ):

        results = []

        seen = set()

        if not page_html:

            return results

        patterns = [

            re.compile(
                r'<a[^>]*'
                r'class=["\'][^"\']*result__a[^"\']*["\']'
                r'[^>]*'
                r'href=["\']([^"\']+)["\']'
                r'[^>]*>'
                r'(.*?)'
                r'</a>',
                re.I | re.S
            ),

            re.compile(
                r'<a[^>]*'
                r'href=["\']([^"\']+)["\']'
                r'[^>]*'
                r'class=["\'][^"\']*result__a[^"\']*["\']'
                r'[^>]*>'
                r'(.*?)'
                r'</a>',
                re.I | re.S
            ),

            re.compile(
                r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
                r'(.*?)'
                r'</a>',
                re.I | re.S
            ),
        ]

        for pattern in patterns:

            for match in pattern.finditer(
                page_html
            ):

                url = cls._clean_url(
                    match.group(1)
                )

                title = cls._clean_title(
                    match.group(2)
                )

                if not url:

                    continue

                if not title:

                    continue

                if url in seen:

                    continue

                seen.add(
                    url
                )

                results.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        return results

    @classmethod
    def _extract_lite_results(
        cls,
        page_html
    ):

        results = []

        seen = set()

        if not page_html:

            return results

        pattern = re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
            r'(.*?)'
            r'</a>',
            re.I | re.S
        )

        for match in pattern.finditer(
            page_html
        ):

            url = cls._clean_url(
                match.group(1)
            )

            title = cls._clean_title(
                match.group(2)
            )

            if not url:

                continue

            if not title:

                continue

            if url in seen:

                continue

            seen.add(
                url
            )

            results.append(
                {
                    "title": title,
                    "url": url
                }
            )

        return results

    def _extract_results(
        self,
        page_html
    ):

        results = (
            self._extract_html_results(
                page_html
            )
        )

        if results:

            return results

        return (
            self._extract_lite_results(
                page_html
            )
        )

    def _source_domain(
        self,
        source
    ):

        if not source:

            return None

        return (
            self.SOURCE_DOMAINS.get(
                source,
                source
            )
            or ""
        ).lower().strip()

    def _source_matches(
        self,
        url,
        source
    ):

        if not url:

            return False

        domain = self._source_domain(
            source
        )

        if not domain:

            return True

        try:

            hostname = (
                urllib.parse
                .urlparse(url)
                .hostname
                or ""
            ).lower()

        except Exception:

            return False

        return (
            hostname == domain
            or
            hostname.endswith(
                "." + domain
            )
        )

    def _diagnose_response(
        self,
        response
    ):

        text = (
            response.text
            or ""
        )

        lowered = text.lower()

        blocked = False

        reasons = []

        if response.status_code in (
            403,
            429
        ):

            blocked = True

            reasons.append(
                f"http_{response.status_code}"
            )

        block_markers = (
            "captcha",
            "unusual traffic",
            "automated",
            "robot check",
            "access denied",
            "rate limit",
            "too many requests",
        )

        for marker in block_markers:

            if marker in lowered:

                blocked = True

                reasons.append(
                    marker
                )

        return {
            "status_code":
                response.status_code,

            "final_url":
                response.url,

            "content_length":
                len(text),

            "blocked":
                blocked,

            "reasons":
                reasons,
        }

    def _request(
        self,
        keyword,
        source,
        endpoint
    ):

        url = self.build_search_url(
            keyword,
            source,
            endpoint
        )

        self._log_info(
            "Search request started",
            {
                "keyword":
                    keyword,

                "source":
                    source,

                "endpoint":
                    endpoint,

                "url":
                    url
            }
        )

        response = self.session.get(
            url,
            timeout=20,
            allow_redirects=True
        )

        diagnosis = (
            self._diagnose_response(
                response
            )
        )

        self._log_info(
            "Search HTTP response",
            {
                **diagnosis,
                "source":
                    source
            }
        )

        response.raise_for_status()

        return response

    def search(
        self,
        keyword,
        source=None
    ):

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

            "endpoint":
                None,

            "diagnosis":
                None,
        }

        last_error = None

        for endpoint in self.SEARCH_ENDPOINTS:

            try:

                response = self._request(
                    keyword,
                    source,
                    endpoint
                )

                result["endpoint"] = (
                    endpoint
                )

                result["search_url"] = (
                    response.url
                )

                result["diagnosis"] = (
                    self._diagnose_response(
                        response
                    )
                )

                results = (
                    self._extract_results(
                        response.text
                    )
                )

                if not results:

                    self._log_warning(
                        "Search parser found no results",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,

                            "endpoint":
                                endpoint,

                            "diagnosis":
                                result[
                                    "diagnosis"
                                ]
                        }
                    )

                    continue

                result["results"] = (
                    results[:10]
                )

                matching = []

                for candidate in results:

                    if self._source_matches(
                        candidate["url"],
                        source
                    ):

                        matching.append(
                            candidate
                        )

                if matching:

                    result["found_url"] = (
                        matching[0]["url"]
                    )

                    self._log_info(
                        "Search source matched",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,

                            "found_url":
                                result[
                                    "found_url"
                                ],

                            "result_count":
                                len(results),

                            "matching_count":
                                len(matching),

                            "endpoint":
                                endpoint
                        }
                    )

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
                            results[:5]
                    }
                )

            except Exception as error:

                last_error = str(
                    error
                )

                self._log_warning(
                    "Search endpoint failed",
                    {
                        "keyword":
                            keyword,

                        "source":
                            source,

                        "endpoint":
                            endpoint,

                        "error":
                            last_error
                    }
                )

        if last_error:

            result["error"] = (
                last_error
            )

        self._log_warning(
            "Search completed without matching source",
            {
                "keyword":
                    keyword,

                "source":
                    source,

                "result_count":
                    len(
                        result["results"]
                    ),

                "found_url":
                    result["found_url"],

                "diagnosis":
                    result["diagnosis"]
            }
        )

        return result

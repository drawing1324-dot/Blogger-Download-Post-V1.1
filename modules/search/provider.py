"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider

Version : 1.1.2

หน้าที่:

- ค้นหา source ตาม keyword
- รองรับ source domain
- ใช้ DuckDuckGo HTML / Lite
- ตรวจสอบ domain ของผลลัพธ์
- กรองผลลัพธ์ปลอมของ DuckDuckGo
- รองรับ retry
- ส่งผลลัพธ์กลับในรูปแบบมาตรฐาน
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

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )

    REQUEST_TIMEOUT = 15

    def __init__(self, config=None, logger=None):

        self.config = config or {}
        self.logger = logger

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    def _log_info(self, message, data=None):

        if self.logger:
            self.logger.info(message, data)

    def _log_warning(self, message, data=None):

        if self.logger:
            self.logger.warning(message, data)

    # ---------------------------------------------------------
    # Source domain
    # ---------------------------------------------------------

    def get_source_domain(self, source):

        if not source:
            return None

        return self.SOURCE_DOMAINS.get(
            source,
            source
        )

    # ---------------------------------------------------------
    # Search URL
    # ---------------------------------------------------------

    def build_search_url(
        self,
        keyword,
        source=None,
        endpoint=None
    ):

        endpoint = (
            endpoint
            or self.SEARCH_ENDPOINTS[0]
        )

        query = str(keyword or "").strip()

        domain = self.get_source_domain(
            source
        )

        if domain and "." in domain:

            query += f" site:{domain}"

        return (
            endpoint
            + "?q="
            + urllib.parse.quote_plus(query)
        )

    # ---------------------------------------------------------
    # URL normalization
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_url(url):

        if not url:
            return None

        url = unescape(
            str(url).strip()
        )

        if url.startswith("//"):

            url = "https:" + url

        if not url.startswith(
            ("http://", "https://")
        ):

            return None

        # DuckDuckGo redirect URL
        try:

            parsed = urllib.parse.urlparse(
                url
            )

            query = urllib.parse.parse_qs(
                parsed.query
            )

            if "uddg" in query:

                redirected = query["uddg"][0]

                if redirected:

                    url = urllib.parse.unquote(
                        redirected
                    )

        except Exception:
            pass

        return url

    # ---------------------------------------------------------
    # Domain extraction
    # ---------------------------------------------------------

    @staticmethod
    def _get_hostname(url):

        if not url:
            return ""

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            hostname = (
                parsed.hostname
                or ""
            ).lower()

            if hostname.startswith(
                "www."
            ):

                hostname = hostname[4:]

            return hostname

        except Exception:

            return ""

    # ---------------------------------------------------------
    # Domain validation
    # ---------------------------------------------------------

    @classmethod
    def _domain_matches(
        cls,
        url,
        source
    ):

        if not url:
            return False

        expected_domain = (
            cls.SOURCE_DOMAINS.get(
                source,
                source
            )
        )

        if not expected_domain:
            return True

        expected_domain = (
            expected_domain
            .lower()
            .strip()
        )

        if expected_domain.startswith(
            "www."
        ):

            expected_domain = (
                expected_domain[4:]
            )

        hostname = cls._get_hostname(
            url
        )

        if not hostname:
            return False

        if hostname == expected_domain:
            return True

        return hostname.endswith(
            "." + expected_domain
        )

    # ---------------------------------------------------------
    # Invalid DuckDuckGo URLs
    # ---------------------------------------------------------

    @staticmethod
    def _is_invalid_result_url(url):

        if not url:
            return True

        normalized = url.lower().strip()

        invalid_hosts = (
            "duckduckgo.com",
            "www.duckduckgo.com",
        )

        hostname = ""

        try:

            parsed = urllib.parse.urlparse(
                normalized
            )

            hostname = (
                parsed.hostname
                or ""
            ).lower()

        except Exception:
            pass

        if hostname in invalid_hosts:
            return True

        invalid_urls = (
            "duckduckgo.com/l/",
            "duckduckgo.com/",
            "duckduckgo.com/about",
            "duckduckgo.com/settings",
        )

        for invalid in invalid_urls:

            if normalized.startswith(
                "https://" + invalid
            ):

                return True

            if normalized.startswith(
                "http://" + invalid
            ):

                return True

        return False

    # ---------------------------------------------------------
    # HTML text cleanup
    # ---------------------------------------------------------

    @staticmethod
    def _clean_text(value):

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
    # HTML result parser
    # ---------------------------------------------------------

    @classmethod
    def _extract_results(cls, html):

        results = []

        if not html:
            return results

        # -----------------------------------------------------
        # Parser สำหรับ DuckDuckGo HTML
        # -----------------------------------------------------

        patterns = [

            # Standard DuckDuckGo result
            r"""
            <a
                [^>]*?
                class=["'][^"']*result__a[^"']*["']
                [^>]*?
                href=["']([^"']+)["']
                [^>]*>
                (.*?)
                </a>
            """,

            # Generic result link
            r"""
            <a
                [^>]*?
                href=["']([^"']+)["']
                [^>]*?
                class=["'][^"']*result__a[^"']*["']
                [^>]*>
                (.*?)
                </a>
            """,

        ]

        seen = set()

        for pattern in patterns:

            matches = re.finditer(
                pattern,
                html,
                re.I | re.S | re.X
            )

            for match in matches:

                try:

                    url = cls._normalize_url(
                        match.group(1)
                    )

                    title = cls._clean_text(
                        match.group(2)
                    )

                except Exception:
                    continue

                if not url:
                    continue

                if cls._is_invalid_result_url(
                    url
                ):
                    continue

                key = url.lower()

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    {
                        "title": title,
                        "url": url,
                    }
                )

        # -----------------------------------------------------
        # Lite DuckDuckGo parser
        # -----------------------------------------------------

        if not results:

            lite_pattern = r"""
                <a
                    [^>]*?
                    href=["']([^"']+)["']
                    [^>]*>
                    (.*?)
                    </a>
            """

            matches = re.finditer(
                lite_pattern,
                html,
                re.I | re.S | re.X
            )

            for match in matches:

                try:

                    url = cls._normalize_url(
                        match.group(1)
                    )

                    title = cls._clean_text(
                        match.group(2)
                    )

                except Exception:
                    continue

                if not url:
                    continue

                if cls._is_invalid_result_url(
                    url
                ):
                    continue

                # Lite page มี link อื่นจำนวนมาก
                # จึงรับเฉพาะ URL ที่ดูเหมือน external result
                hostname = cls._get_hostname(
                    url
                )

                if not hostname:
                    continue

                key = url.lower()

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    {
                        "title": title,
                        "url": url,
                    }
                )

        return results

    # ---------------------------------------------------------
    # Filter source results
    # ---------------------------------------------------------

    @classmethod
    def _filter_source_results(
        cls,
        results,
        source
    ):

        filtered = []

        for result in results:

            url = result.get(
                "url"
            )

            if not url:
                continue

            if cls._is_invalid_result_url(
                url
            ):
                continue

            if not cls._domain_matches(
                url,
                source
            ):
                continue

            filtered.append(
                result
            )

        return filtered

    # ---------------------------------------------------------
    # Request
    # ---------------------------------------------------------

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
                "keyword": keyword,
                "source": source,
                "endpoint": endpoint,
                "url": url,
            }
        )

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    self.USER_AGENT,
                "Accept":
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8",
                "Accept-Language":
                    "en-US,en;q=0.9",
                "Referer":
                    "https://duckduckgo.com/",
            },
            timeout=self.REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        html = response.text or ""

        self._log_info(
            "Search HTTP response",
            {
                "status_code":
                    response.status_code,

                "final_url":
                    response.url,

                "content_length":
                    len(html),

                "source":
                    source,
            }
        )

        return response

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        keyword,
        source=None
    ):

        checked_at = (
            datetime.now()
            .isoformat()
        )

        search_url = self.build_search_url(
            keyword,
            source
        )

        result = {

            "keyword":
                keyword,

            "source":
                source or "search",

            "search_url":
                search_url,

            "found_url":
                None,

            "results":
                [],

            "checked_at":
                checked_at,

            "result_count":
                0,

            "success":
                False,
        }

        last_diagnosis = {}

        # -----------------------------------------------------
        # Search endpoints
        # -----------------------------------------------------

        for endpoint in self.SEARCH_ENDPOINTS:

            try:

                response = self._request(
                    keyword,
                    source,
                    endpoint
                )

                html = response.text or ""

                raw_results = (
                    self._extract_results(
                        html
                    )
                )

                source_results = (
                    self._filter_source_results(
                        raw_results,
                        source
                    )
                )

                last_diagnosis = {

                    "status_code":
                        response.status_code,

                    "final_url":
                        response.url,

                    "content_length":
                        len(html),

                    "raw_result_count":
                        len(raw_results),

                    "source_result_count":
                        len(source_results),
                }

                # -------------------------------------------------
                # Found matching source
                # -------------------------------------------------

                if source_results:

                    result["results"] = (
                        source_results[:5]
                    )

                    result["result_count"] = (
                        len(source_results)
                    )

                    result["found_url"] = (
                        source_results[0]["url"]
                    )

                    result["success"] = True

                    self._log_info(
                        "Search source matched",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,

                            "result_count":
                                len(
                                    source_results
                                ),

                            "found_url":
                                result[
                                    "found_url"
                                ],
                        }
                    )

                    return result

                # -------------------------------------------------
                # Raw result exists but wrong domain
                # -------------------------------------------------

                if raw_results:

                    self._log_warning(
                        "Search results found "
                        "but source did not match",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,

                            "raw_result_count":
                                len(
                                    raw_results
                                ),

                            "results":
                                raw_results[:5],
                        }
                    )

                else:

                    self._log_warning(
                        "Search returned no "
                        "usable results",
                        {
                            "keyword":
                                keyword,

                            "source":
                                source,
                        }
                    )

            except Exception as error:

                last_diagnosis = {

                    "endpoint":
                        endpoint,

                    "error":
                        str(error),
                }

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
                            str(error),
                    }
                )

        # -----------------------------------------------------
        # Nothing found
        # -----------------------------------------------------

        result["diagnosis"] = (
            last_diagnosis
        )

        self._log_warning(
            "Search completed without "
            "matching source",
            {
                "keyword":
                    keyword,

                "source":
                    source,

                "result_count":
                    result["result_count"],

                "found_url":
                    None,

                "diagnosis":
                    last_diagnosis,
            }
        )

        return result

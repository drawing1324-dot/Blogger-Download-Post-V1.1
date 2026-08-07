"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.2

หน้าที่:

- ค้นหาแหล่งข้อมูลจาก Search Engine
- รองรับการค้นหาแบบกำหนด Source Domain
- รองรับ DuckDuckGo HTML
- แกะ Redirect URL
- ตรวจสอบ Domain ของผลลัพธ์
- ส่งผลลัพธ์กลับให้ process_blog()
- ไม่ทำให้ระบบล้มเมื่อ Search Engine หรือ Source ใดมีปัญหา
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

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(
        self,
        config=None,
        logger=None
    ):

        self.config = config or {}

        self.logger = logger

        self.timeout = (
            self.config
            .get("search", {})
            .get("timeout", 15)
        )

    # ---------------------------------------------------------
    # Logging helpers
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Domain helpers
    # ---------------------------------------------------------

    def get_source_domain(
        self,
        source=None
    ):

        if not source:

            return None

        domain = self.SOURCE_DOMAINS.get(
            source,
            source
        )

        if not domain:

            return None

        domain = domain.strip()

        domain = re.sub(
            r"^https?://",
            "",
            domain,
            flags=re.IGNORECASE
        )

        domain = domain.split("/")[0]

        return domain.lower()

    @staticmethod
    def _normalize_url(
        url
    ):

        if not url:

            return None

        url = html.unescape(
            url.strip()
        )

        if url.startswith("//"):

            url = "https:" + url

        if url.startswith("/"):

            return None

        return url

    @staticmethod
    def _is_valid_http_url(
        url
    ):

        if not url:

            return False

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            return parsed.scheme in (
                "http",
                "https"
            ) and bool(
                parsed.netloc
            )

        except Exception:

            return False

    @staticmethod
    def _domain_matches(
        url,
        domain
    ):

        if not url or not domain:

            return True

        try:

            hostname = (
                urllib.parse
                .urlparse(url)
                .hostname
            )

            if not hostname:

                return False

            hostname = hostname.lower()

            domain = domain.lower()

            return (
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
            )

        except Exception:

            return False

    # ---------------------------------------------------------
    # Search URL
    # ---------------------------------------------------------

    def build_search_url(
        self,
        keyword,
        source=None
    ):

        query = (
            str(keyword or "")
            .strip()
        )

        domain = self.get_source_domain(
            source
        )

        if domain:

            query += (
                f" site:{domain}"
            )

        return (
            "https://html.duckduckgo.com/html/?q="
            + urllib.parse.quote_plus(query)
        )

    # ---------------------------------------------------------
    # Redirect handling
    # ---------------------------------------------------------

    @staticmethod
    def _unwrap_duckduckgo_url(
        url
    ):

        if not url:

            return None

        url = html.unescape(
            url
        )

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            query = urllib.parse.parse_qs(
                parsed.query
            )

            for key in (
                "uddg",
                "url",
                "target"
            ):

                values = query.get(
                    key
                )

                if values:

                    decoded = urllib.parse.unquote(
                        values[0]
                    )

                    if decoded:

                        return decoded

        except Exception:

            pass

        return url

    # ---------------------------------------------------------
    # HTML extraction
    # ---------------------------------------------------------

    @classmethod
    def _extract_results(
        cls,
        html_text
    ):

        results = []

        if not html_text:

            return results

        # -----------------------------------------------------
        # Method 1
        # Standard DuckDuckGo result links
        # -----------------------------------------------------

        pattern_1 = re.compile(
            r"""
            <a
            [^>]*?
            class\s*=\s*["'][^"']*
            result__a
            [^"']*["']
            [^>]*?
            href\s*=\s*["']
            ([^"']+)
            ["']
            [^>]*>
            (.*?)
            </a>
            """,
            re.IGNORECASE
            | re.DOTALL
            | re.VERBOSE
        )

        for match in pattern_1.finditer(
            html_text
        ):

            url = match.group(1)

            title_html = match.group(2)

            url = cls._unwrap_duckduckgo_url(
                url
            )

            url = cls._normalize_url(
                url
            )

            title = re.sub(
                r"<[^>]+>",
                "",
                title_html or ""
            )

            title = html.unescape(
                title
            ).strip()

            if (
                url
                and cls._is_valid_http_url(url)
            ):

                results.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        # -----------------------------------------------------
        # Method 2
        # Fallback: result__url
        # -----------------------------------------------------

        if not results:

            pattern_2 = re.compile(
                r"""
                <a
                [^>]*?
                class\s*=\s*["'][^"']*
                result__url
                [^"']*["']
                [^>]*?
                href\s*=\s*["']
                ([^"']+)
                ["']
                """,
                re.IGNORECASE
                | re.DOTALL
                | re.VERBOSE
            )

            for match in pattern_2.finditer(
                html_text
            ):

                url = cls._unwrap_duckduckgo_url(
                    match.group(1)
                )

                url = cls._normalize_url(
                    url
                )

                if (
                    url
                    and cls._is_valid_http_url(url)
                ):

                    results.append(
                        {
                            "title": "",
                            "url": url
                        }
                    )

        # -----------------------------------------------------
        # Method 3
        # Generic href fallback
        #
        # ใช้เมื่อ DuckDuckGo เปลี่ยน HTML
        # -----------------------------------------------------

        if not results:

            pattern_3 = re.compile(
                r'href\s*=\s*["\']([^"\']+)["\']',
                re.IGNORECASE
            )

            for match in pattern_3.finditer(
                html_text
            ):

                url = cls._unwrap_duckduckgo_url(
                    match.group(1)
                )

                url = cls._normalize_url(
                    url
                )

                if not url:

                    continue

                if not cls._is_valid_http_url(
                    url
                ):

                    continue

                hostname = (
                    urllib.parse
                    .urlparse(url)
                    .hostname
                    or ""
                ).lower()

                # ไม่เอา URL ของ DuckDuckGo เอง
                if (
                    "duckduckgo.com"
                    in hostname
                ):

                    continue

                results.append(
                    {
                        "title": "",
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

            normalized = url.rstrip(
                "/"
            )

            if normalized in seen:

                continue

            seen.add(
                normalized
            )

            unique.append(
                item
            )

        return unique

    # ---------------------------------------------------------
    # Filter source domain
    # ---------------------------------------------------------

    def _filter_source_results(
        self,
        results,
        source=None
    ):

        domain = self.get_source_domain(
            source
        )

        if not domain:

            return results

        valid = []

        for item in results:

            url = item.get(
                "url"
            )

            if self._domain_matches(
                url,
                domain
            ):

                valid.append(
                    item
                )

        return valid

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        keyword,
        source=None
    ):

        checked_at = datetime.now().isoformat()

        search_url = self.build_search_url(
            keyword,
            source
        )

        result = {
            "keyword": keyword,
            "source": source or "search",
            "search_url": search_url,
            "found_url": None,
            "results": [],
            "checked_at": checked_at,
        }

        self._log_info(
            "Search started",
            {
                "keyword": keyword,
                "source": source,
                "search_url": search_url
            }
        )

        try:

            response = requests.get(
                search_url,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                allow_redirects=True
            )

            response.raise_for_status()

            raw_results = (
                self._extract_results(
                    response.text
                )
            )

            result["raw_result_count"] = len(
                raw_results
            )

            filtered_results = (
                self._filter_source_results(
                    raw_results,
                    source
                )
            )

            result["results"] = (
                filtered_results[:5]
            )

            if filtered_results:

                result["found_url"] = (
                    filtered_results[0]["url"]
                )

            self._log_info(
                "Search executed",
                {
                    "keyword": keyword,
                    "source": source,
                    "raw_result_count": len(
                        raw_results
                    ),
                    "valid_result_count": len(
                        filtered_results
                    ),
                    "found_url": result[
                        "found_url"
                    ]
                }
            )

            return result

        except requests.RequestException as error:

            self._log_warning(
                "Search request failed",
                {
                    "keyword": keyword,
                    "source": source,
                    "error": str(error)
                }
            )

            result["error"] = str(
                error
            )

            return result

        except Exception as error:

            self._log_warning(
                "Search failed",
                {
                    "keyword": keyword,
                    "source": source,
                    "error": str(error)
                }
            )

            result["error"] = str(
                error
            )

            return result

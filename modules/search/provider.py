"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.2

หน้าที่:
- ค้นหาแหล่งดาวน์โหลดตาม source/domain
- รองรับผลลัพธ์จาก DuckDuckGo HTML หลายรูปแบบ
- ตรวจสอบ URL ก่อนส่งกลับ
- ไม่ถือว่าหน้า search สำเร็จ = พบ source
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

    def __init__(self, config=None, logger=None):
        self.config = config or {}
        self.logger = logger

    def build_search_url(self, keyword, source=None):

        query = (keyword or "").strip()

        if source:

            domain = self.SOURCE_DOMAINS.get(
                source,
                source
            )

            if domain and "." in domain:
                query += f" site:{domain}"

        return (
            "https://html.duckduckgo.com/html/?q="
            + urllib.parse.quote_plus(query)
        )

    @staticmethod
    def _clean_url(url):

        if not url:
            return None

        url = html.unescape(url).strip()

        if url.startswith("//"):
            url = "https:" + url

        try:

            parsed = urllib.parse.urlparse(url)

            if parsed.netloc.endswith(
                "duckduckgo.com"
            ):

                query = urllib.parse.parse_qs(
                    parsed.query
                )

                if query.get("uddg"):
                    url = query["uddg"][0]

        except Exception:

            return None

        url = urllib.parse.unquote(
            url
        ).strip()

        if not re.match(
            r"^https?://",
            url,
            re.I
        ):
            return None

        return url

    @staticmethod
    def _clean_title(value):

        if not value:
            return ""

        value = html.unescape(value)

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

    @classmethod
    def _extract_results(cls, page_html):

        results = []

        seen = set()

        if not page_html:
            return results

        patterns = [

            re.compile(
                r'<a[^>]*class=["\'][^"\']*result__a[^"\']*["\'][^>]*'
                r'href=["\']([^"\']+)["\'][^>]*>'
                r'(.*?)</a>',
                re.I | re.S
            ),

            re.compile(
                r'<a[^>]*href=["\']([^"\']+)["\'][^>]*'
                r'class=["\'][^"\']*result__a[^"\']*["\'][^>]*>'
                r'(.*?)</a>',
                re.I | re.S
            ),
        ]

        for pattern in patterns:

            for match in pattern.finditer(
                page_html
            ):

                raw_url = match.group(1)

                raw_title = match.group(2)

                url = cls._clean_url(
                    raw_url
                )

                title = cls._clean_title(
                    raw_title
                )

                if not url or not title:
                    continue

                if url in seen:
                    continue

                seen.add(url)

                results.append(
                    {
                        "title": title,
                        "url": url
                    }
                )

        return results

    def _source_matches(
        self,
        url,
        source
    ):

        if not url or not source:
            return False

        domain = self.SOURCE_DOMAINS.get(
            source,
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

            domain = domain.lower().strip()

            return (
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
            )

        except Exception:

            return False

    def search(
        self,
        keyword,
        source=None
    ):

        result = {

            "keyword": keyword,

            "source": (
                source
                or "search"
            ),

            "search_url":
                self.build_search_url(
                    keyword,
                    source
                ),

            "found_url": None,

            "results": [],

            "checked_at":
                datetime.now().isoformat(),
        }

        try:

            headers = {

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
            }

            response = requests.get(

                result["search_url"],

                headers=headers,

                timeout=20,

                allow_redirects=True
            )

            response.raise_for_status()

            results = self._extract_results(
                response.text
            )

            result["results"] = results[:5]

            selected = None

            for candidate in results:

                if self._source_matches(
                    candidate["url"],
                    source
                ):

                    selected = candidate["url"]

                    break

            result["found_url"] = selected

            if self.logger:

                self.logger.info(

                    "Search executed",

                    {
                        "keyword":
                            keyword,

                        "source":
                            source,

                        "result_count":
                            len(results),

                        "found_url":
                            selected
                    }
                )

                if not selected:

                    self.logger.warning(

                        "Search returned no matching source",

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

            if self.logger:

                self.logger.warning(

                    "Search failed",

                    {
                        "keyword":
                            keyword,

                        "source":
                            source,

                        "error":
                            str(error)
                    }
                )

        return result

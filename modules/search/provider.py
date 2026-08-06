"""
Project : Blogger Download Auto Post V1.1
Module  : Search Provider
Version : 1.1.0

หน้าที่:
- ค้นหาแหล่งดาวน์โหลด
- จัดรูปแบบข้อมูล Source
- เตรียมข้อมูลให้ Article System
"""

import urllib.parse
from datetime import datetime


class SearchProvider:


    def __init__(
        self,
        config=None,
        logger=None
    ):

        self.config = config

        self.logger = logger



    def build_search_url(
        self,
        keyword
    ):

        query = urllib.parse.quote(
            keyword
        )

        return (
            "https://www.google.com/search?q="
            + query
        )



    def search(
        self,
        keyword
    ):


        result = {

            "keyword": keyword,

            "search_url":
            self.build_search_url(
                keyword
            ),

            "source":
            "search",

            "found_url":
            None,

            "checked_at":
            datetime.now()
            .isoformat()

        }


        if self.logger:

            self.logger.info(
                "Search executed",
                {
                    "keyword": keyword
                }
            )


        return result

"""
Project : Blogger Download Auto Post V1.1
Module  : Limit Manager

หน้าที่:
- ควบคุมจำนวนโพสต์ต่อวัน
"""

import json
from pathlib import Path
from datetime import datetime



class LimitManager:


    def __init__(
        self,
        file="storage/post_limit.json"
    ):

        self.file = Path(
            file
        )

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )



    def load(self):

        if not self.file.exists():

            return {

                "date":
                datetime.now()
                .strftime(
                    "%Y-%m-%d"
                ),

                "count":0

            }


        with open(
            self.file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)



    def can_post(
        self,
        limit
    ):

        data = self.load()


        today = (
            datetime.now()
            .strftime(
                "%Y-%m-%d"
            )
        )


        if data["date"] != today:

            return True



        return (
            data["count"]
            <
            limit
        )



    def increase(self):

        data = self.load()


        today = (
            datetime.now()
            .strftime(
                "%Y-%m-%d"
            )
        )


        if data["date"] != today:

            data = {

                "date":today,

                "count":0

            }


        data["count"] += 1



        with open(
            self.file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

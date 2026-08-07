"""
Project : Blogger Download Auto Post V1.1
Module  : Blogger Publisher
Version : 1.1.0

หน้าที่:
- เชื่อมต่อ Blogger API
- สร้างบทความ
- Publish หรือ Save Draft
"""

import os
from datetime import datetime


class BloggerPublisher:


    def __init__(
        self,
        profile="main",
        logger=None
    ):

        self.profile = profile

        self.logger = logger

        self.service = None



    def connect(self):

        try:

            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build


            refresh_token = os.getenv(
                f"{self.profile.upper()}_REFRESH_TOKEN"
            )


            client_id = os.getenv(
                f"{self.profile.upper()}_CLIENT_ID"
            )


            client_secret = os.getenv(
                f"{self.profile.upper()}_CLIENT_SECRET"
            )


            if not refresh_token:

                raise Exception(
                    "Missing Blogger Refresh Token"
                )


            credentials = Credentials(
                None,

                refresh_token=refresh_token,

                token_uri=
                "https://oauth2.googleapis.com/token",

                client_id=client_id,

                client_secret=client_secret,

                scopes=[
                    "https://www.googleapis.com/auth/blogger"
                ]
            )


            self.service = build(
                "blogger",
                "v3",
                credentials=credentials
            )


            if self.logger:

                self.logger.info(
                    "Blogger connected"
                )


            return True


        except Exception as error:


            if self.logger:

                self.logger.error(
                    "Blogger connection failed",
                    {
                        "error": str(error)
                    }
                )


            raise error



    def publish(
        self,
        blog_id,
        title,
        content,
        publish=True
    ):


        if not self.service:

            self.connect()



        body = {

            "title": title,

            "content": content

        }


        if publish:

            body["status"] = "LIVE"

        else:

            body["status"] = "DRAFT"



        result = (
            self.service
            .posts()
            .insert(
                blogId=blog_id,
                body=body,
                isDraft=not publish
            )
            .execute()
        )


        if self.logger:

            self.logger.info(
                "Blogger post created",
                {
                    "title": title,

                    "blog_id": blog_id
                }
            )


        return result

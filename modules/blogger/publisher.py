"""
Project : Blogger Download Auto Post V1.1
Module  : Blogger Publisher
Version : 1.2.0

หน้าที่:

- เชื่อมต่อ Blogger API
- สร้างบทความ
- สร้าง Draft
- กำหนดเวลาการเผยแพร่
- หาเวลาของโพสต์ล่าสุด
- ตั้งเวลาโพสต์ใหม่หลังโพสต์ล่าสุด 1 ชั่วโมง
- ป้องกันการ Publish ทันทีโดยไม่ตั้งเวลา
"""

import os
from datetime import datetime, timedelta, timezone


class BloggerPublisher:

    def __init__(
        self,
        profile="main",
        logger=None
    ):

        self.profile = profile
        self.logger = logger
        self.service = None


    # =========================================================
    # Logger
    # =========================================================

    def _log(
        self,
        level,
        message,
        data=None
    ):

        if not self.logger:
            return

        method = getattr(
            self.logger,
            level,
            None
        )

        if method:

            method(
                message,
                data
            )


    # =========================================================
    # Connect Blogger
    # =========================================================

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


            if not client_id:

                raise Exception(
                    "Missing Blogger Client ID"
                )


            if not client_secret:

                raise Exception(
                    "Missing Blogger Client Secret"
                )


            credentials = Credentials(
                None,

                refresh_token=refresh_token,

                token_uri=(
                    "https://oauth2.googleapis.com/token"
                ),

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


            self._log(
                "info",
                "Blogger connected"
            )


            return True


        except Exception as error:

            self._log(
                "error",
                "Blogger connection failed",
                {
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise


    # =========================================================
    # Get Latest Post
    # =========================================================

    def get_latest_post(
        self,
        blog_id
    ):

        if not self.service:

            self.connect()


        try:

            request = (
                self.service
                .posts()
                .list(
                    blogId=blog_id,

                    maxResults=50,

                    fetchBodies=False,

                    orderBy="UPDATED"
                )
            )


            response = request.execute()


            posts = response.get(
                "items",
                []
            )


            if not posts:

                self._log(
                    "info",
                    "No existing Blogger posts found",
                    {
                        "blog_id": blog_id
                    }
                )

                return None


            valid_posts = []


            for post in posts:

                published = post.get(
                    "published"
                )


                if not published:

                    continue


                try:

                    published_dt = (
                        self._parse_datetime(
                            published
                        )
                    )


                    valid_posts.append(
                        (
                            published_dt,
                            post
                        )
                    )


                except Exception as error:

                    self._log(
                        "warning",
                        "Unable to parse Blogger post date",
                        {
                            "post_id": post.get("id"),
                            "published": published,
                            "error": str(error)
                        }
                    )


            if not valid_posts:

                self._log(
                    "info",
                    "No valid published dates found",
                    {
                        "blog_id": blog_id
                    }
                )

                return None


            valid_posts.sort(
                key=lambda item: item[0],
                reverse=True
            )


            latest_datetime, latest_post = (
                valid_posts[0]
            )


            result = {
                "id": latest_post.get("id"),
                "title": latest_post.get("title"),
                "published": latest_post.get("published"),
                "datetime": latest_datetime
            }


            self._log(
                "info",
                "Latest Blogger post found",
                {
                    "blog_id": blog_id,
                    "post_id": result["id"],
                    "title": result["title"],
                    "published": result["published"]
                }
            )


            return result


        except Exception as error:

            self._log(
                "error",
                "Failed to get latest Blogger post",
                {
                    "blog_id": blog_id,
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise


    # =========================================================
    # Parse Blogger Date
    # =========================================================

    @staticmethod
    def _parse_datetime(
        value
    ):

        if not value:

            raise ValueError(
                "Empty datetime value"
            )


        normalized = value.strip()


        if normalized.endswith(
            "Z"
        ):

            normalized = (
                normalized[:-1]
                + "+00:00"
            )


        result = datetime.fromisoformat(
            normalized
        )


        if result.tzinfo is None:

            result = result.replace(
                tzinfo=timezone.utc
            )


        return result


    # =========================================================
    # Calculate Next Schedule
    # =========================================================

    def get_next_schedule_time(
        self,
        blog_id
    ):

        now = datetime.now(
            timezone.utc
        )


        latest = self.get_latest_post(
            blog_id
        )


        if latest:

            latest_datetime = latest[
                "datetime"
            ]


            next_datetime = (
                latest_datetime
                + timedelta(hours=1)
            )


            # ถ้าเวลาของโพสต์ล่าสุดอยู่ในอดีต
            # และ +1 ชั่วโมงยังอยู่ในอดีต
            # ต้องเลื่อนไปข้างหน้าเพื่อไม่ให้
            # Blogger รับเวลาที่ผ่านมาแล้ว

            minimum_time = (
                now
                + timedelta(minutes=1)
            )


            if next_datetime <= minimum_time:

                next_datetime = (
                    minimum_time
                )


            self._log(
                "info",
                "Next schedule calculated from latest post",
                {
                    "latest_post": latest.get("title"),
                    "latest_time": (
                        latest_datetime.isoformat()
                    ),
                    "scheduled_time": (
                        next_datetime.isoformat()
                    )
                }
            )


            return next_datetime


        next_datetime = (
            now
            + timedelta(hours=1)
        )


        self._log(
            "info",
            "No previous post found; schedule one hour from now",
            {
                "scheduled_time": (
                    next_datetime.isoformat()
                )
            }
        )


        return next_datetime


    # =========================================================
    # Create Scheduled Post
    # =========================================================

    def publish(
        self,
        blog_id,
        title,
        content,
        publish=True
    ):

        if not self.service:

            self.connect()


        # -----------------------------------------------------
        # Safety:
        #
        # publish=False = Draft เท่านั้น
        #
        # publish=True = สร้างและ Schedule
        #
        # จะไม่มีการส่ง LIVE ทันทีจาก insert()
        # -----------------------------------------------------

        if not publish:

            body = {
                "title": title,
                "content": content
            }


            result = (
                self.service
                .posts()
                .insert(
                    blogId=blog_id,
                    body=body,
                    isDraft=True
                )
                .execute()
            )


            self._log(
                "info",
                "Blogger draft created",
                {
                    "blog_id": blog_id,
                    "post_id": result.get("id"),
                    "title": title
                }
            )


            return result


        # -----------------------------------------------------
        # Calculate schedule
        # -----------------------------------------------------

        scheduled_datetime = (
            self.get_next_schedule_time(
                blog_id
            )
        )


        scheduled_iso = (
            scheduled_datetime
            .astimezone(timezone.utc)
            .isoformat()
            .replace(
                "+00:00",
                "Z"
            )
        )


        # -----------------------------------------------------
        # Step 1:
        # Create as Draft first
        # -----------------------------------------------------

        body = {
            "title": title,
            "content": content
        }


        try:

            draft = (
                self.service
                .posts()
                .insert(
                    blogId=blog_id,
                    body=body,
                    isDraft=True
                )
                .execute()
            )


        except Exception as error:

            self._log(
                "error",
                "Failed to create Blogger draft",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise


        post_id = draft.get(
            "id"
        )


        if not post_id:

            raise Exception(
                "Blogger draft created without post ID"
            )


        self._log(
            "info",
            "Blogger draft created for scheduling",
            {
                "blog_id": blog_id,
                "post_id": post_id,
                "title": title,
                "scheduled_time": scheduled_iso
            }
        )


        # -----------------------------------------------------
        # Step 2:
        # Publish with future publishDate
        # -----------------------------------------------------

        try:

            result = (
                self.service
                .posts()
                .publish(
                    blogId=blog_id,
                    postId=post_id,
                    publishDate=scheduled_iso
                )
                .execute()
            )


        except Exception as error:

            self._log(
                "error",
                "Failed to schedule Blogger post",
                {
                    "blog_id": blog_id,
                    "post_id": post_id,
                    "title": title,
                    "scheduled_time": scheduled_iso,
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise


        # -----------------------------------------------------
        # Safety verification
        # -----------------------------------------------------

        result_published = result.get(
            "published"
        )


        result_status = result.get(
            "status"
        )


        self._log(
            "info",
            "Blogger post scheduled",
            {
                "blog_id": blog_id,
                "post_id": post_id,
                "title": title,
                "scheduled_time": scheduled_iso,
                "published": result_published,
                "status": result_status,
                "url": result.get("url")
            }
        )


        return result

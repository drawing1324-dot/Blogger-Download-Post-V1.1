"""
Project : Blogger Download Auto Post V1.1
Module  : Blogger Publisher
Version : 1.2.0

หน้าที่:

- เชื่อมต่อ Blogger API
- สร้างบทความ
- ตั้งเวลาโพสต์
- Publish หรือ Save Draft
- ตรวจหาเวลาของโพสต์ล่าสุด
- ตั้งโพสต์ใหม่ต่อจากเวลาล่าสุด 1 ชั่วโมง
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
    # Logger helper
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
    # Blogger Connection
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
    # Ensure Connection
    # =========================================================

    def _ensure_connection(self):

        if not self.service:

            self.connect()


    # =========================================================
    # Get All Existing Posts
    # =========================================================

    def _get_existing_posts(
        self,
        blog_id
    ):

        self._ensure_connection()


        posts = []

        page_token = None


        try:

            while True:

                request = (
                    self.service
                    .posts()
                    .list(
                        blogId=blog_id,
                        maxResults=100,
                        pageToken=page_token,
                        fetchBodies=False
                    )
                )


                response = request.execute()


                items = response.get(
                    "items",
                    []
                )


                posts.extend(
                    items
                )


                page_token = response.get(
                    "nextPageToken"
                )


                if not page_token:

                    break


            self._log(
                "info",
                "Existing Blogger posts loaded",
                {
                    "blog_id": blog_id,
                    "post_count": len(posts)
                }
            )


            return posts


        except Exception as error:

            self._log(
                "error",
                "Failed to load existing Blogger posts",
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
    def _parse_blogger_datetime(
        value
    ):

        if not value:

            return None


        try:

            normalized = value.replace(
                "Z",
                "+00:00"
            )


            parsed = datetime.fromisoformat(
                normalized
            )


            if parsed.tzinfo is None:

                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )


            return parsed.astimezone(
                timezone.utc
            )


        except Exception:

            return None


    # =========================================================
    # Find Latest Scheduled / Published Time
    # =========================================================

    def get_latest_post_time(
        self,
        blog_id
    ):

        posts = self._get_existing_posts(
            blog_id
        )


        latest_time = None

        latest_post = None


        for post in posts:

            status = str(
                post.get(
                    "status",
                    ""
                )
            ).upper()


            # สนใจทั้งโพสต์ที่ตั้งเวลาไว้แล้ว
            # และโพสต์ที่เผยแพร่แล้ว
            if status not in (
                "SCHEDULED",
                "LIVE"
            ):

                continue


            candidate_values = [

                post.get(
                    "published"
                ),

                post.get(
                    "updated"
                )

            ]


            candidate_time = None


            for value in candidate_values:

                parsed = (
                    self._parse_blogger_datetime(
                        value
                    )
                )


                if parsed:

                    candidate_time = parsed

                    break


            if not candidate_time:

                continue


            if (
                latest_time is None
                or candidate_time > latest_time
            ):

                latest_time = candidate_time

                latest_post = post


        if latest_time:

            self._log(
                "info",
                "Latest Blogger post time found",
                {
                    "blog_id": blog_id,
                    "latest_time": latest_time.isoformat(),
                    "latest_post_id": (
                        latest_post or {}
                    ).get("id"),
                    "latest_post_status": (
                        latest_post or {}
                    ).get("status"),
                    "latest_post_title": (
                        latest_post or {}
                    ).get("title")
                }
            )

        else:

            self._log(
                "info",
                "No existing published or scheduled post time found",
                {
                    "blog_id": blog_id
                }
            )


        return latest_time


    # =========================================================
    # Calculate Next Schedule Time
    # =========================================================

    def get_next_schedule_time(
        self,
        blog_id
    ):

        now = datetime.now(
            timezone.utc
        )


        latest_time = (
            self.get_latest_post_time(
                blog_id
            )
        )


        if latest_time:

            next_time = (
                latest_time
                + timedelta(hours=1)
            )

        else:

            next_time = (
                now
                + timedelta(hours=1)
            )


        # ป้องกันกรณีโพสต์ล่าสุดอยู่ในอดีตมาก
        # และเวลาที่คำนวณได้ยังน้อยกว่าปัจจุบัน
        minimum_time = (
            now
            + timedelta(minutes=1)
        )


        if next_time < minimum_time:

            next_time = minimum_time


        self._log(
            "info",
            "Next Blogger schedule time calculated",
            {
                "blog_id": blog_id,
                "latest_time": (
                    latest_time.isoformat()
                    if latest_time
                    else None
                ),
                "next_schedule_time": (
                    next_time.isoformat()
                )
            }
        )


        return next_time


    # =========================================================
    # Publish / Schedule
    # =========================================================

    def publish(
        self,
        blog_id,
        title,
        content,
        publish=True
    ):

        self._ensure_connection()


        if not blog_id:

            raise ValueError(
                "Missing Blogger Blog ID"
            )


        if not title:

            raise ValueError(
                "Missing Blogger post title"
            )


        if not content:

            raise ValueError(
                "Missing Blogger post content"
            )


        body = {

            "title": title,

            "content": content

        }


        # -----------------------------------------------------
        # Scheduled Post
        # -----------------------------------------------------

        if publish:

            schedule_time = (
                self.get_next_schedule_time(
                    blog_id
                )
            )


            body["published"] = (
                schedule_time.isoformat()
                .replace(
                    "+00:00",
                    "Z"
                )
            )


            body["status"] = "SCHEDULED"


            self._log(
                "info",
                "Creating scheduled Blogger post",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "scheduled_time": body["published"]
                }
            )


        # -----------------------------------------------------
        # Draft
        # -----------------------------------------------------

        else:

            body["status"] = "DRAFT"


            self._log(
                "info",
                "Creating Blogger draft",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )


        # -----------------------------------------------------
        # Insert
        # -----------------------------------------------------

        try:

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


        except Exception as error:

            self._log(
                "error",
                "Blogger post creation failed",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "requested_schedule": body.get(
                        "published"
                    )
                }
            )

            raise


        # -----------------------------------------------------
        # Success Log
        # -----------------------------------------------------

        self._log(
            "info",
            "Blogger post created",
            {
                "blog_id": blog_id,
                "title": title,
                "post_id": result.get("id"),
                "status": result.get("status"),
                "url": result.get("url"),
                "published": result.get("published")
            }
        )


        return result

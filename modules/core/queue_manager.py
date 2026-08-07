"""
Project : Blogger Download Auto Post V1.1
Module  : Queue Manager
Version : 1.1.0

หน้าที่:
- จัดการ Queue ของแต่ละ Blog
- เพิ่มหัวข้อ
- อ่านหัวข้อ
- เปลี่ยนสถานะ
- ย้ายรายการที่โพสต์แล้ว
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


class QueueManager:


    def __init__(
        self,
        storage_path="storage"
    ):

        self.storage = Path(storage_path)

        self.queue_path = (
            self.storage / "queue"
        )

        self.posted_path = (
            self.storage / "posted"
        )


        self.queue_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.posted_path.mkdir(
            parents=True,
            exist_ok=True
        )


    def get_queue_file(
        self,
        blog_id
    ):

        return (
            self.queue_path /
            f"{blog_id}.json"
        )


    def get_posted_file(
        self,
        blog_id
    ):

        return (
            self.posted_path /
            f"{blog_id}.json"
        )


    def load_queue(
        self,
        blog_id
    ):

        file = self.get_queue_file(
            blog_id
        )


        if not file.exists():

            return []


        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)


    def save_queue(
        self,
        blog_id,
        data
    ):

        file = self.get_queue_file(
            blog_id
        )


        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )


    def add_topic(
        self,
        blog_id,
        topic
    ):

        queue = self.load_queue(
            blog_id
        )


        exists = any(
            item["title"] == topic["title"]
            for item in queue
        )


        if exists:

            return False


        topic["status"] = "pending"

        topic["created_at"] = (
            datetime.now()
            .isoformat()
        )


        queue.append(topic)


        self.save_queue(
            blog_id,
            queue
        )


        return True



    def get_next(
        self,
        blog_id
    ):

        queue = self.load_queue(
            blog_id
        )


        for item in queue:

            if item["status"] == "pending":

                return item


        return None



    def update_status(
        self,
        blog_id,
        title,
        status
    ):

        queue = self.load_queue(
            blog_id
        )


        for item in queue:

            if item["title"] == title:

                item["status"] = status


        self.save_queue(
            blog_id,
            queue
        )



    def archive_post(
        self,
        blog_id,
        title
    ):

        queue = self.load_queue(
            blog_id
        )


        remaining = []

        archived = None


        for item in queue:

            if item["title"] == title:

                archived = item

            else:

                remaining.append(item)



        self.save_queue(
            blog_id,
            remaining
        )


        if archived:

            posted_file = (
                self.get_posted_file(
                    blog_id
                )
            )


            posted = []


            if posted_file.exists():

                with open(
                    posted_file,
                    "r",
                    encoding="utf-8"
                ) as f:

                    posted = json.load(f)


            archived["status"] = "posted"

            archived["posted_at"] = (
                datetime.now()
                .isoformat()
            )


            posted.append(
                archived
            )


            with open(
                posted_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    posted,
                    f,
                    indent=2,
                    ensure_ascii=False
                )


            return True


        return False

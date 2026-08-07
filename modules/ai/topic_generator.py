"""
Project : Blogger Download Auto Post V1.1
Module  : Topic Generator
Version : 1.1.0

หน้าที่:
- สร้างหัวข้อดาวน์โหลดจาก AI
- ใช้ Prompt จาก config
- เตรียมข้อมูลสำหรับ Queue
"""

import json
import re
from datetime import datetime


class TopicGenerator:


    def __init__(
        self,
        ai_provider,
        config,
        logger=None
    ):

        self.ai = ai_provider

        self.config = config

        self.logger = logger



    def get_prompt(
        self,
        blog_type
    ):

        prompts = (
            self.config
            .get("prompts", {})
        )


        data = prompts.get(
            blog_type
        )


        if not data:

            raise Exception(
                f"Prompt not found: {blog_type}"
            )


        return data.get(
            "topic",
            ""
        )



    def clean_topic(
        self,
        text
    ):

        text = text.strip()


        text = re.sub(r"^[0-9]+[\.\-\)]\s*", "", text)
        text = re.sub(r"^[-*•]\s*", "", text)


        return text



    def parse_topics(
        self,
        response
    ):

        lines = (
            response
            .split("\n")
        )


        topics = []


        for line in lines:

            line = self.clean_topic(
                line
            )


            if len(line) < 5:

                continue


            topics.append(
                {
                    "title": line,

                    "status": "pending",

                    "created_at":
                    datetime.now()
                    .isoformat()
                }
            )


        return topics



    def generate(
        self,
        blog
    ):


        blog_type = blog.get(
            "type"
        )


        prompt = self.get_prompt(
            blog_type
        )


        response = (
            self.ai.generate(
                prompt
            )
        )


        topics = self.parse_topics(
            response
        )


        if self.logger:

            self.logger.info(
                "Topics generated",
                {
                    "blog":
                    blog.get("name"),

                    "count":
                    len(topics)
                }
            )


        return topics

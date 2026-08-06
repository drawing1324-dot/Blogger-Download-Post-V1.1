"""
Project : Blogger Download Auto Post V1.1
Module  : Article Writer
Version : 1.1.0

หน้าที่:
- สร้างบทความจากหัวข้อ
- ใช้ Prompt ตามประเภท Blog
- ส่งผลลัพธ์กลับเป็นบทความ
"""

from datetime import datetime


class ArticleWriter:


    def __init__(
        self,
        ai_provider,
        config,
        logger=None
    ):

        self.ai = ai_provider

        self.config = config

        self.logger = logger



    def get_article_prompt(
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
                f"Article prompt not found: {blog_type}"
            )


        return data.get(
            "article",
            ""
        )



    def build_prompt(
        self,
        blog,
        topic
    ):

        base_prompt = (
            self.get_article_prompt(
                blog.get("type")
            )
        )


        prompt = f"""
{base_prompt}


Topic:
{topic}


Requirements:

- Write in natural English.
- Explain the downloadable file.
- Include SEO friendly title.
- Include description.
- Include download information.
- Include useful details for users.
- Avoid duplicate content.
"""


        return prompt



    def generate(
        self,
        blog,
        topic
    ):


        prompt = self.build_prompt(
            blog,
            topic
        )


        content = (
            self.ai.generate(
                prompt
            )
        )


        result = {

            "title": topic,

            "content": content,

            "blog_id":
            blog.get("blog_id"),

            "type":
            blog.get("type"),

            "created_at":
            datetime.now()
            .isoformat(),

            "status":
            "draft"

        }


        if self.logger:

            self.logger.info(
                "Article generated",
                {
                    "title": topic
                }
            )


        return result

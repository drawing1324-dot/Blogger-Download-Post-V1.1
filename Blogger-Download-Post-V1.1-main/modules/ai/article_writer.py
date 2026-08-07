"""AI article writer for V1.1."""
from datetime import datetime


class ArticleWriter:
    def __init__(self, ai_provider, config, logger=None):
        self.ai = ai_provider
        self.config = config
        self.logger = logger

    def get_article_prompt(self, blog_type):
        data = self.config.get("prompts", {}).get(blog_type)
        if not data:
            raise Exception(f"Article prompt not found: {blog_type}")
        return data.get("article", "")

    def build_prompt(self, blog, topic, source=None, image=None):
        source = source or {}
        image = image or {}
        return f'''{self.get_article_prompt(blog.get("type"))}

Topic: {topic}
Download source URL: {source.get("found_url") or "Not found"}
Image URL: {image.get("image_url") or "Not found"}

Requirements:
- Write natural English HTML suitable for Blogger.
- Return only article HTML. Do not use Markdown or code fences.
- Explain the downloadable file/resource, format, uses and benefits.
- Include a clear Download section. If a source URL is supplied, link to it exactly; never invent a URL.
- If an image URL is supplied, include one HTML image using that exact URL with useful alt text.
- If no source URL exists, do not invent a download link.
- Do not claim licenses, versions, compatibility, prices, or file contents that were not supplied.
'''

    def generate(self, blog, topic, source=None, image=None):
        content = self.ai.generate(self.build_prompt(blog, topic, source, image)).strip()
        if content.startswith("```"):
            content = content.replace("```html", "", 1).replace("```", "").strip()
        source_url = (source or {}).get("found_url")
        image_url = (image or {}).get("image_url")
        if image_url and "<img" not in content.lower():
            content = f'<p><img src="{image_url}" alt="{topic}" style="max-width:100%;height:auto;"></p>\n' + content
        if source_url and "href=" not in content.lower():
            content += f'\n<h2>Download</h2><p><a href="{source_url}" target="_blank" rel="noopener">Download or view the file</a></p>'
        if len(content) < 500:
            raise ValueError("Generated article is too short")
        result = {"title": topic, "content": content, "blog_id": blog.get("blog_id"),
                  "type": blog.get("type"), "created_at": datetime.now().isoformat(), "status": "draft"}
        if self.logger:
            self.logger.info("Article generated", {"title": topic})
        return result

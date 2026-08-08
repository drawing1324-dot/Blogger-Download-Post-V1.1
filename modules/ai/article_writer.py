"""AI article writer for V1.1."""

from datetime import datetime
import html
import re
from urllib.parse import urlparse


class ArticleWriter:

    def __init__(self, ai_provider, config, logger=None):
        self.ai = ai_provider
        self.config = config or {}
        self.logger = logger

    def get_article_prompt(self, blog_type):
        data = self.config.get("prompts", {}).get(blog_type)

        if not data:
            raise Exception(
                f"Article prompt not found: {blog_type}"
            )

        return data.get("article", "")

    @staticmethod
    def _valid_url(url):
        """Return True only for normal HTTP/HTTPS URLs."""
        if not url:
            return False

        try:
            parsed = urlparse(str(url).strip())

            return parsed.scheme.lower() in (
                "http",
                "https",
            ) and bool(parsed.netloc)

        except Exception:
            return False

    @staticmethod
    def _valid_image_url(url):
        """
        Return True only for URLs that are suitable for <img>.

        PDF/document URLs are explicitly rejected.
        """
        if not url:
            return False

        try:
            parsed = urlparse(str(url).strip())
            path = parsed.path.lower()

            if parsed.scheme.lower() not in (
                "http",
                "https",
            ):
                return False

            if not parsed.netloc:
                return False

            rejected_extensions = (
                ".pdf",
                ".html",
                ".htm",
                ".txt",
                ".doc",
                ".docx",
            )

            if path.endswith(rejected_extensions):
                return False

            allowed_extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".gif",
                ".avif",
            )

            # If the URL clearly has an image extension, accept it.
            if path.endswith(allowed_extensions):
                return True

            # Some image services use URLs without extensions.
            # The ImageProvider has already validated those URLs.
            return True

        except Exception:
            return False

    @staticmethod
    def _clean_ai_output(content):
        """
        Remove accidental Markdown/code fences from Gemini output.
        """
        if not content:
            return ""

        content = content.strip()

        # Remove ```html / ```HTML / ```.
        content = re.sub(
            r"^\s*```(?:html)?\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"\s*```\s*$",
            "",
            content,
            flags=re.IGNORECASE,
        )

        return content.strip()

    @staticmethod
    def _remove_invalid_images(content):
        """
        Remove <img> elements that point to PDFs or obvious documents.

        Valid images are left untouched.
        """
        if not content:
            return content

        image_pattern = re.compile(
            r"<img\b[^>]*>",
            re.IGNORECASE | re.DOTALL,
        )

        def replace_image(match):
            tag = match.group(0)

            src_match = re.search(
                r'\bsrc\s*=\s*["\']([^"\']+)["\']',
                tag,
                re.IGNORECASE,
            )

            if not src_match:
                return ""

            src = html.unescape(
                src_match.group(1)
            ).strip()

            if ArticleWriter._valid_image_url(src):
                return tag

            return ""

        return image_pattern.sub(
            replace_image,
            content,
        )

    @staticmethod
    def _ensure_image(content, image_url, title):
        """
        Add one image when a valid image URL exists and the AI
        did not already include one.
        """
        if not image_url:
            return content

        if not ArticleWriter._valid_image_url(
            image_url
        ):
            return content

        if "<img" in content.lower():
            return content

        safe_url = html.escape(
            image_url,
            quote=True,
        )

        safe_alt = html.escape(
            f"{title} preview",
            quote=True,
        )

        image_html = (
            '<p>'
            f'<img src="{safe_url}" '
            f'alt="{safe_alt}" '
            'style="height:auto;max-width:100%;'
            'margin:15px 0;" />'
            '</p>'
        )

        return (
            image_html
            + "\n"
            + content
        )

    @staticmethod
    def _contains_download_link(content):
        """
        Check whether the generated HTML already contains
        a real href attribute.
        """
        return bool(
            re.search(
                r"<a\b[^>]*\bhref\s*=",
                content,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _remove_markdown_links(content):
        """
        Convert simple Markdown links into HTML links.

        Example:
        [Download](https://example.com)
        ->
        <a href="https://example.com">Download</a>
        """
        if not content:
            return content

        pattern = re.compile(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            re.IGNORECASE,
        )

        def replace_link(match):
            text = html.escape(
                match.group(1).strip()
            )

            url = html.escape(
                match.group(2).strip(),
                quote=True,
            )

            return (
                f'<a href="{url}" '
                'target="_blank" '
                'rel="noopener">'
                f"{text}"
                "</a>"
            )

        return pattern.sub(
            replace_link,
            content,
        )

    @staticmethod
    def _append_download_section(
        content,
        source_url,
    ):
        """
        Add a proper Download section only when a valid
        source URL exists and the article does not already
        contain a link.
        """
        if not source_url:
            return content

        if not ArticleWriter._valid_url(
            source_url
        ):
            return content

        if ArticleWriter._contains_download_link(
            content
        ):
            return content

        safe_url = html.escape(
            source_url,
            quote=True,
        )

        section = f"""
<h2>Download</h2>
<p>
<a href="{safe_url}"
   target="_blank"
   rel="noopener">
   Download or view the resource
</a>
</p>
"""

        return (
            content.rstrip()
            + "\n"
            + section.strip()
        )

    def build_prompt(
        self,
        blog,
        topic,
        source=None,
        image=None,
    ):
        source = source or {}
        image = image or {}

        source_url = source.get(
            "found_url"
        )

        image_url = image.get(
            "image_url"
        )

        return f"""
{self.get_article_prompt(blog.get("type"))}

Topic: {topic}

Download source URL:
{source_url or "Not found"}

Image URL:
{image_url or "Not found"}

Requirements:

- Write natural English HTML suitable for Blogger.
- Return only article HTML.
- Do not use Markdown.
- Do not use code fences.
- Do not return ```html or ``` anywhere.
- Explain the downloadable file/resource, format, uses and benefits.
- Include a clear Download section.
- If a source URL is supplied, link to that exact URL.
- Never invent a URL.
- If an image URL is supplied, include one HTML <img> using that exact URL.
- The image must use a useful alt attribute.
- Never use a PDF URL, document URL, or webpage URL as an image source.
- If no valid image URL exists, do not invent an image URL.
- If no source URL exists, do not invent a download link.
- Do not claim licenses, versions, compatibility, prices, or file contents that were not supplied.
"""

    def generate(
        self,
        blog,
        topic,
        source=None,
        image=None,
    ):
        source = source or {}
        image = image or {}

        source_url = source.get(
            "found_url"
        )

        image_url = image.get(
            "image_url"
        )

        # ---------------------------------------------------------
        # Generate article with AI
        # ---------------------------------------------------------
        content = self.ai.generate(
            self.build_prompt(
                blog,
                topic,
                source,
                image,
            )
        )

        content = self._clean_ai_output(
            content
        )

        # ---------------------------------------------------------
        # Remove accidental Markdown links
        # ---------------------------------------------------------
        content = self._remove_markdown_links(
            content
        )

        # ---------------------------------------------------------
        # Remove invalid <img> tags
        # ---------------------------------------------------------
        content = self._remove_invalid_images(
            content
        )

        # ---------------------------------------------------------
        # Add valid image if AI did not include one
        # ---------------------------------------------------------
        content = self._ensure_image(
            content,
            image_url,
            topic,
        )

        # ---------------------------------------------------------
        # Add Download section if necessary
        # ---------------------------------------------------------
        content = self._append_download_section(
            content,
            source_url,
        )

        content = content.strip()

        # ---------------------------------------------------------
        # Safety check
        # ---------------------------------------------------------
        if len(content) < 500:
            raise ValueError(
                "Generated article is too short"
            )

        result = {
            "title": topic,
            "content": content,
            "blog_id": blog.get("blog_id"),
            "type": blog.get("type"),
            "created_at": datetime.now().isoformat(),
            "status": "draft",
        }

        if self.logger:
            self.logger.info(
                "Article generated",
                {
                    "title": topic,
                },
            )

        return result

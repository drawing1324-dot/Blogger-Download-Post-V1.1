"""
Project : Blogger Download Auto Post V1.1
Module  : AI Article Writer
Version : 1.3.0

หน้าที่:

- สร้างบทความด้วย AI
- สร้าง Dynamic Labels ตามหัวข้อและเนื้อหาของบทความ
- ตรวจสอบและทำความสะอาด HTML
- ตรวจสอบ Image URL
- ป้องกัน PDF / Document URL ถูกใช้เป็นรูปภาพ
- เพิ่ม Image อัตโนมัติเมื่อ AI ไม่ได้ใส่รูป
- เพิ่ม Download Section เมื่อมี Source URL
- แปลง Markdown Link เป็น HTML
- ส่งผลลัพธ์กลับในรูปแบบที่ Blogger Publisher ใช้งานได้
"""

from datetime import datetime
import html
import json
import re
from urllib.parse import urlparse


class ArticleWriter:

    def __init__(
        self,
        ai_provider,
        config,
        logger=None
    ):
        self.ai = ai_provider
        self.config = config or {}
        self.logger = logger

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
    # Article Prompt
    # =========================================================

    def get_article_prompt(
        self,
        blog_type
    ):

        data = (
            self.config
            .get("prompts", {})
            .get(blog_type)
        )

        if not data:
            raise Exception(
                f"Article prompt not found: {blog_type}"
            )

        return data.get(
            "article",
            ""
        )

    # =========================================================
    # URL Validation
    # =========================================================

    @staticmethod
    def _valid_url(
        url
    ):
        """
        Return True only for normal HTTP/HTTPS URLs.
        """

        if not url:
            return False

        try:

            parsed = urlparse(
                str(url).strip()
            )

            return (
                parsed.scheme.lower()
                in (
                    "http",
                    "https",
                )
                and bool(
                    parsed.netloc
                )
            )

        except Exception:

            return False

    # =========================================================
    # Image URL Validation
    # =========================================================

    @staticmethod
    def _valid_image_url(
        url
    ):
        """
        Return True only for URLs suitable for <img>.

        PDF/document URLs are explicitly rejected.
        """

        if not url:
            return False

        try:

            parsed = urlparse(
                str(url).strip()
            )

            path = (
                parsed.path
                .lower()
            )

            if (
                parsed.scheme.lower()
                not in (
                    "http",
                    "https",
                )
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
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".zip",
                ".rar",
                ".7z",
            )

            if path.endswith(
                rejected_extensions
            ):
                return False

            allowed_extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".gif",
                ".avif",
            )

            # ถ้า URL มีนามสกุลรูปภาพชัดเจน
            # ให้ยอมรับทันที
            if path.endswith(
                allowed_extensions
            ):
                return True

            # Image service บางแห่งไม่มี extension
            # ImageProvider เป็นผู้ตรวจสอบ URL มาแล้ว
            return True

        except Exception:

            return False

    # =========================================================
    # Clean AI Output
    # =========================================================

    @staticmethod
    def _clean_ai_output(
        content
    ):
        """
        Remove accidental Markdown/code fences
        from AI output.
        """

        if not content:
            return ""

        content = str(
            content
        ).strip()

        # Remove opening code fence
        content = re.sub(
            r"^\s*```(?:html)?\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        # Remove closing code fence
        content = re.sub(
            r"\s*```\s*$",
            "",
            content,
            flags=re.IGNORECASE,
        )

        return content.strip()

    # =========================================================
    # Parse Structured AI Response
    # =========================================================

    @staticmethod
    def _extract_json(
        content
    ):
        """
        Extract JSON object from AI response.

        รองรับกรณี AI ส่ง:
        {
            "content": "...",
            "labels": [...]
        }

        หรือส่ง JSON ครอบด้วย ```json ... ```
        """

        if not content:
            return None

        text = str(
            content
        ).strip()

        # -----------------------------------------------------
        # Remove code fences
        # -----------------------------------------------------

        text = re.sub(
            r"^\s*```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.strip()

        # -----------------------------------------------------
        # Direct JSON
        # -----------------------------------------------------

        try:

            parsed = json.loads(
                text
            )

            if isinstance(
                parsed,
                dict
            ):
                return parsed

        except Exception:
            pass

        # -----------------------------------------------------
        # Try extracting first JSON object
        # -----------------------------------------------------

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )

        if (
            start >= 0
            and end > start
        ):

            candidate = text[
                start:end + 1
            ]

            try:

                parsed = json.loads(
                    candidate
                )

                if isinstance(
                    parsed,
                    dict
                ):
                    return parsed

            except Exception:
                pass

        return None

    # =========================================================
    # Clean Labels
    # =========================================================

    @staticmethod
    def _clean_labels(
        labels,
        topic=""
    ):
        """
        Clean and normalize AI-generated labels.

        Labels are dynamic and are never hard-coded.

        Rules:
        - string เท่านั้น
        - ไม่เอา #hashtag
        - ตัดช่องว่างส่วนเกิน
        - ตัดเครื่องหมายที่ไม่จำเป็น
        - ไม่ซ้ำกัน
        - จำกัดสูงสุด 10 labels
        """

        if not isinstance(
            labels,
            list
        ):
            labels = []

        cleaned = []

        for label in labels:

            if label is None:
                continue

            label = str(
                label
            ).strip()

            if not label:
                continue

            # Remove leading hashtag
            label = re.sub(
                r"^#+",
                "",
                label
            ).strip()

            # Replace line breaks / tabs
            label = re.sub(
                r"[\r\n\t]+",
                " ",
                label
            )

            # Collapse spaces
            label = re.sub(
                r"\s+",
                " ",
                label
            ).strip()

            # Remove wrapping quotes
            label = label.strip(
                "\"'"
            ).strip()

            # Remove leading/trailing punctuation
            label = re.sub(
                r"^[,\.;:|]+",
                "",
                label
            )

            label = re.sub(
                r"[,\.;:|]+$",
                "",
                label
            )

            label = label.strip()

            if not label:
                continue

            # Avoid excessively long labels
            if len(label) > 80:
                label = label[:80].rstrip()

            # Case-insensitive duplicate detection
            duplicate_key = (
                label.casefold()
            )

            if any(
                existing.casefold()
                == duplicate_key
                for existing in cleaned
            ):
                continue

            cleaned.append(
                label
            )

            # Blogger labels should remain manageable.
            if len(cleaned) >= 10:
                break

        return cleaned

    # =========================================================
    # Fallback Labels
    # =========================================================

    @staticmethod
    def _fallback_labels(
        topic
    ):
        """
        Fallback only when AI completely fails to return labels.

        ไม่ใช้รายการ Label แบบฟิกซ์

        จะนำคำสำคัญจาก Topic มาใช้แทน
        เพื่อให้โพสต์ยังมี Label ที่สัมพันธ์กับหัวข้อ
        """

        if not topic:
            return []

        text = str(
            topic
        ).strip()

        if not text:
            return []

        # Remove punctuation
        text = re.sub(
            r"[^\w\s\-&]+",
            " ",
            text,
            flags=re.UNICODE,
        )

        words = [
            word.strip()
            for word in text.split()
            if word.strip()
        ]

        if not words:
            return []

        labels = []

        # Full topic as first dynamic label
        labels.append(
            " ".join(words[:8])
        )

        # Add meaningful multi-word chunks
        if len(words) >= 2:

            for index in range(
                len(words) - 1
            ):

                phrase = (
                    f"{words[index]} "
                    f"{words[index + 1]}"
                )

                if len(
                    phrase
                ) >= 3:

                    labels.append(
                        phrase
                    )

                if len(
                    labels
                ) >= 5:
                    break

        return ArticleWriter._clean_labels(
            labels,
            topic
        )

    # =========================================================
    # Remove Invalid Images
    # =========================================================

    @staticmethod
    def _remove_invalid_images(
        content
    ):
        """
        Remove <img> elements pointing to PDFs
        or obvious document URLs.

        Valid images are left untouched.
        """

        if not content:
            return content

        image_pattern = re.compile(
            r"<img\b[^>]*>",
            re.IGNORECASE | re.DOTALL,
        )

        def replace_image(
            match
        ):

            tag = match.group(
                0
            )

            src_match = re.search(
                r'\bsrc\s*=\s*["\']([^"\']+)["\']',
                tag,
                re.IGNORECASE,
            )

            if not src_match:
                return ""

            src = html.unescape(
                src_match.group(
                    1
                )
            ).strip()

            if ArticleWriter._valid_image_url(
                src
            ):
                return tag

            return ""

        return image_pattern.sub(
            replace_image,
            content,
        )

    # =========================================================
    # Ensure Image
    # =========================================================

    @staticmethod
    def _ensure_image(
        content,
        image_url,
        title
    ):
        """
        Add one image when a valid image URL exists
        and the AI did not already include one.
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
            str(image_url),
            quote=True,
        )

        safe_alt = html.escape(
            f"{title} preview",
            quote=True,
        )

        image_html = (
            "<p>"
            f'<img src="{safe_url}" '
            f'alt="{safe_alt}" '
            'style="height:auto;max-width:100%;'
            'margin:15px 0;" />'
            "</p>"
        )

        return (
            image_html
            + "\n"
            + content
        )

    # =========================================================
    # Contains Download Link
    # =========================================================

    @staticmethod
    def _contains_download_link(
        content
    ):
        """
        Check whether generated HTML already contains
        a real href attribute.
        """

        return bool(
            re.search(
                r"<a\b[^>]*\bhref\s*=",
                content,
                re.IGNORECASE,
            )
        )

    # =========================================================
    # Remove Markdown Links
    # =========================================================

    @staticmethod
    def _remove_markdown_links(
        content
    ):
        """
        Convert simple Markdown links into HTML links.

        Example:

        [Download](https://example.com)

        becomes:

        <a href="https://example.com">
            Download
        </a>
        """

        if not content:
            return content

        pattern = re.compile(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            re.IGNORECASE,
        )

        def replace_link(
            match
        ):

            text = html.escape(
                match.group(
                    1
                ).strip()
            )

            url = html.escape(
                match.group(
                    2
                ).strip(),
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

    # =========================================================
    # Append Download Section
    # =========================================================

    @staticmethod
    def _append_download_section(
        content,
        source_url
    ):
        """
        Add a proper Download section only when:

        - source URL exists
        - URL is valid
        - article does not already contain a link
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
            str(source_url),
            quote=True,
        )

        section = f"""
<section>
<h2>Download</h2>
<p>
<a href="{safe_url}"
   target="_blank"
   rel="noopener">
   Download or view the file
</a>
</p>
</section>
"""

        return (
            content.rstrip()
            + "\n"
            + section.strip()
        )

    # =========================================================
    # Build Prompt
    # =========================================================

    def build_prompt(
        self,
        blog,
        topic,
        source=None,
        image=None,
    ):
        """
        Build structured AI prompt.

        AI ต้องส่งกลับเป็น JSON เพื่อแยก:
        - content
        - labels

        Labels ต้องสร้างจากบทความจริง
        ไม่ใช่ Label แบบฟิกซ์
        """

        source = source or {}
        image = image or {}

        source_url = source.get(
            "found_url"
        )

        image_url = image.get(
            "image_url"
        )

        article_prompt = (
            self.get_article_prompt(
                blog.get("type")
            )
        )

        return f"""
{article_prompt}

Topic:
{topic}

Blog type:
{blog.get("type") or "Not specified"}

Download source URL:
{source_url or "Not found"}

Image URL:
{image_url or "Not found"}

IMPORTANT OUTPUT RULES:

Return ONLY one valid JSON object.

Do NOT return Markdown.
Do NOT return code fences.
Do NOT return ```json.
Do NOT add explanations before or after the JSON.

The JSON object MUST have exactly these two main fields:

{{
  "content": "ARTICLE HTML HERE",
  "labels": [
    "Dynamic Label 1",
    "Dynamic Label 2",
    "Dynamic Label 3"
  ]
}}

CONTENT REQUIREMENTS:

- Write natural English HTML suitable for Blogger.
- The content must be a complete useful article.
- Explain the downloadable file/resource, format, uses and benefits.
- Include a clear Download section when a valid source URL is supplied.
- If a source URL is supplied, link to that exact URL.
- Never invent a URL.
- If an image URL is supplied, include one HTML <img> using that exact URL.
- The image must have a useful alt attribute.
- Never use a PDF URL, document URL, or webpage URL as an image source.
- If no valid image URL exists, do not invent an image URL.
- If no source URL exists, do not invent a download link.
- Do not claim licenses, versions, compatibility, prices, or file contents that were not supplied.
- Do not use Markdown.
- Do not use code fences.

LABEL REQUIREMENTS:

- Generate Labels specifically for THIS article.
- Labels must be based on the actual topic and the actual article content.
- Labels must NOT be a fixed list.
- Do NOT always use the blog type as a label.
- Do NOT use generic labels such as "Free Download" unless they are genuinely useful for this specific article.
- Choose the most relevant search/category concepts from this article.
- Prefer specific subjects, software, file/resource types, design categories, technical concepts, or meaningful topics mentioned in the article.
- Do not invent facts that are not supported by the article.
- Return between 3 and 8 labels.
- Each label should normally be short and readable.
- Do not prefix labels with #.
- Do not include duplicate labels.
- Labels should be suitable for Blogger's Labels field.
"""

    # =========================================================
    # Generate
    # =========================================================

    def generate(
        self,
        blog,
        topic,
        source=None,
        image=None,
    ):
        """
        Generate article + dynamic labels.
        """

        source = source or {}
        image = image or {}

        source_url = source.get(
            "found_url"
        )

        image_url = image.get(
            "image_url"
        )

        # -----------------------------------------------------
        # Generate article with AI
        # -----------------------------------------------------

        raw_response = self.ai.generate(
            self.build_prompt(
                blog,
                topic,
                source,
                image,
            )
        )

        if not raw_response:
            raise ValueError(
                "AI returned empty article response"
            )

        raw_response = str(
            raw_response
        ).strip()

        # -----------------------------------------------------
        # Parse structured AI response
        # -----------------------------------------------------

        parsed = self._extract_json(
            raw_response
        )

        content = ""
        labels = []

        if parsed:

            content = parsed.get(
                "content",
                ""
            )

            labels = parsed.get(
                "labels",
                []
            )

        else:

            # -------------------------------------------------
            # Fallback:
            # If AI returned plain HTML instead of JSON,
            # keep the article and generate fallback labels.
            # -------------------------------------------------

            self._log(
                "warning",
                "AI returned non-JSON article response",
                {
                    "title": topic
                }
            )

            content = raw_response

            labels = []

        # -----------------------------------------------------
        # Normalize content
        # -----------------------------------------------------

        content = self._clean_ai_output(
            content
        )

        # -----------------------------------------------------
        # Remove accidental Markdown links
        # -----------------------------------------------------

        content = self._remove_markdown_links(
            content
        )

        # -----------------------------------------------------
        # Remove invalid <img> tags
        # -----------------------------------------------------

        content = self._remove_invalid_images(
            content
        )

        # -----------------------------------------------------
        # Add valid image if AI did not include one
        # -----------------------------------------------------

        content = self._ensure_image(
            content,
            image_url,
            topic,
        )

        # -----------------------------------------------------
        # Add Download section if necessary
        # -----------------------------------------------------

        content = self._append_download_section(
            content,
            source_url,
        )

        content = content.strip()

        # -----------------------------------------------------
        # Clean AI-generated Labels
        # -----------------------------------------------------

        labels = self._clean_labels(
            labels,
            topic
        )

        # -----------------------------------------------------
        # Dynamic fallback
        #
        # Only used when AI failed to provide labels.
        # It is generated from the current topic,
        # so it is NOT a fixed Label list.
        # -----------------------------------------------------

        if not labels:

            labels = self._fallback_labels(
                topic
            )

            self._log(
                "warning",
                "AI labels unavailable; fallback labels generated",
                {
                    "title": topic,
                    "labels": labels
                }
            )

        # -----------------------------------------------------
        # Safety check
        # -----------------------------------------------------

        if len(content) < 500:

            raise ValueError(
                "Generated article is too short"
            )

        # -----------------------------------------------------
        # Build result
        # -----------------------------------------------------

        result = {
            "title": topic,
            "content": content,
            "labels": labels,
            "blog_id": blog.get(
                "blog_id"
            ),
            "type": blog.get(
                "type"
            ),
            "created_at": (
                datetime.now().isoformat()
            ),
            "status": "draft",
        }

        # -----------------------------------------------------
        # Logging
        # -----------------------------------------------------

        if self.logger:

            self.logger.info(
                "Article generated",
                {
                    "title": topic,
                    "label_count": len(
                        labels
                    ),
                    "labels": labels,
                    "content_length": len(
                        content
                    )
                },
            )

        return result

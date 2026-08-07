```python
"""
Project : Blogger Download Auto Post V1.1
Module  : Gemini AI Provider
Version : 1.1.1

หน้าที่:
- เชื่อมต่อ Gemini API
- ส่ง Prompt
- รับผลลัพธ์จาก AI
- รองรับ Google Gen AI SDK รุ่นใหม่
"""

import os
import time


class GeminiAI:

    def __init__(
        self,
        api_key=None,
        logger=None
    ):

        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        self.logger = logger

        self.client = None

    def connect(self):

        if not self.api_key:
            raise Exception(
                "Missing GEMINI_API_KEY"
            )

        try:

            from google import genai

            self.client = genai.Client(
                api_key=self.api_key
            )

            if self.logger:
                self.logger.info(
                    "Gemini connected"
                )

            return True

        except Exception as error:

            if self.logger:
                self.logger.error(
                    "Gemini connection failed",
                    {
                        "error": str(error)
                    }
                )

            raise error

    def generate(
        self,
        prompt,
        retry=3
    ):

        if not self.client:
            self.connect()

        last_error = None

        for attempt in range(retry):

            try:

                response = (
                    self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                )

                text = getattr(
                    response,
                    "text",
                    None
                )

                if not text:
                    raise Exception(
                        "Gemini returned empty response"
                    )

                return text

            except Exception as error:

                last_error = error

                if self.logger:
                    self.logger.warning(
                        "Gemini request failed",
                        {
                            "attempt": attempt + 1,
                            "error": str(error)
                        }
                    )

                if attempt < retry - 1:
                    time.sleep(5)

        raise Exception(
            f"Gemini generation failed: {last_error}"
        )
```

"""
Project : Blogger Download Auto Post V1.1
Module  : Gemini AI Provider
Version : 1.1.2
"""

import os
import time


class GeminiAI:

    def __init__(self, api_key=None, logger=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.logger = logger
        self.client = None
        self.model_name = None

    def connect(self):

        if not self.api_key:
            raise Exception("Missing GEMINI_API_KEY")

        try:
            from google import genai

            self.client = genai.Client(
                api_key=self.api_key
            )

            # Find an available text-generation model automatically.
            try:
                models = list(self.client.models.list())

                preferred = [
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                    "gemini-1.5-flash",
                ]

                available = []

                for model in models:
                    name = getattr(model, "name", "")

                    if name:
                        name = name.replace("models/", "")
                        available.append(name)

                for preferred_model in preferred:
                    if preferred_model in available:
                        self.model_name = preferred_model
                        break

                # Fallback: choose a Gemini model that supports generation.
                if not self.model_name:
                    for name in available:
                        if name.startswith("gemini"):
                            self.model_name = name
                            break

            except Exception:
                self.model_name = None

            if not self.model_name:
                self.model_name = "gemini-2.0-flash"

            if self.logger:
                self.logger.info(
                    f"Gemini connected: {self.model_name}"
                )

            return True

        except Exception as error:

            if self.logger:
                self.logger.error(
                    "Gemini connection failed",
                    {"error": str(error)}
                )

            raise error

    def generate(self, prompt, retry=3):

        if not self.client:
            self.connect()

        last_error = None

        for attempt in range(retry):

            try:

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )

                text = getattr(response, "text", None)

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
                            "model": self.model_name,
                            "error": str(error)
                        }
                    )

                if attempt < retry - 1:
                    time.sleep(5)

        raise Exception(
            f"Gemini generation failed: {last_error}"
        )

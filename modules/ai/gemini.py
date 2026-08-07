import os
import time


class GeminiAI:

    MODELS = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
    ]

    def __init__(self, api_key=None, logger=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.logger = logger
        self.client = None
        self.model_name = None

    def _log_info(self, message):
        if self.logger:
            try:
                self.logger.info(message)
            except Exception:
                pass

    def _log_warning(self, message, data=None):
        if self.logger:
            try:
                self.logger.warning(message, data or {})
            except Exception:
                pass

    def _log_error(self, message, data=None):
        if self.logger:
            try:
                self.logger.error(message, data or {})
            except Exception:
                pass

    def connect(self):

        if not self.api_key:
            raise Exception("Missing GEMINI_API_KEY")

        try:
            from google import genai

            self.client = genai.Client(
                api_key=self.api_key
            )

            self._log_info("Gemini API client connected")

            return True

        except Exception as error:

            self._log_error(
                "Gemini connection failed",
                {"error": str(error)}
            )

            raise Exception(
                f"Gemini connection failed: {error}"
            )

    def generate(self, prompt, retry=3):

        if not prompt:
            raise Exception("Gemini prompt is empty")

        if not self.client:
            self.connect()

        last_error = None

        models_to_try = []

        if self.model_name:
            models_to_try.append(self.model_name)

        for model in self.MODELS:
            if model not in models_to_try:
                models_to_try.append(model)

        for model_name in models_to_try:

            for attempt in range(retry):

                try:

                    response = (
                        self.client.models.generate_content(
                            model=model_name,
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

                    self.model_name = model_name

                    self._log_info(
                        f"Gemini generation successful: {model_name}"
                    )

                    return text.strip()

                except Exception as error:

                    last_error = error

                    self._log_warning(
                        "Gemini generation attempt failed",
                        {
                            "model": model_name,
                            "attempt": attempt + 1,
                            "error": str(error)
                        }
                    )

                    if attempt < retry - 1:
                        time.sleep(5)

            self._log_warning(
                "Switching Gemini model",
                {"failed_model": model_name}
            )

        raise Exception(
            f"Gemini generation failed: {last_error}"
        )

    def get_model(self):
        return self.model_name

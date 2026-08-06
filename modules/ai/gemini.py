"""
Project : Blogger Download Auto Post V1.1
Module  : Gemini AI Provider
Version : 1.1.0

หน้าที่:
- เชื่อมต่อ Gemini API
- ส่ง Prompt
- รับผลลัพธ์จาก AI
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
            or os.getenv(
                "GEMINI_API_KEY"
            )
        )

        self.logger = logger

        self.client = None


    def connect(self):

        if not self.api_key:

            raise Exception(
                "Missing GEMINI_API_KEY"
            )


        try:

            import google.generativeai as genai


            genai.configure(
                api_key=self.api_key
            )


            self.client = (
                genai.GenerativeModel(
                    "gemini-2.5-flash"
                )
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



        for attempt in range(retry):

            try:


                response = (
                    self.client
                    .generate_content(
                        prompt
                    )
                )


                return response.text



            except Exception as error:


                if self.logger:

                    self.logger.warning(
                        "Gemini request failed",
                        {
                            "attempt": attempt + 1,
                            "error": str(error)
                        }
                    )


                time.sleep(5)



        raise Exception(
            "Gemini generation failed"
        )

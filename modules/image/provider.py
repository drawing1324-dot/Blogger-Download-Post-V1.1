"""
Project : Blogger Download Auto Post V1.1
Module  : Image Provider
Version : 1.1.0

หน้าที่:
- จัดการแหล่งรูปภาพ
- เลือกลำดับ Provider
- เตรียมข้อมูลรูปสำหรับบทความ
"""

from datetime import datetime


class ImageProvider:


    def __init__(
        self,
        config,
        logger=None
    ):

        self.config = config

        self.logger = logger


        self.providers = (
            config
            .get("image_sources", {})
            .get("providers", [])
        )



    def get_enabled_providers(self):

        result = []


        providers = sorted(
            self.providers,
            key=lambda x:
            x.get(
                "priority",
                99
            )
        )


        for provider in providers:

            if provider.get(
                "enabled",
                False
            ):

                result.append(
                    provider
                )


        return result



    def find_image(
        self,
        keyword
    ):


        providers = (
            self.get_enabled_providers()
        )


        result = {

            "keyword": keyword,

            "image_url": None,

            "provider": None,

            "status": "not_found",

            "checked_at":
            datetime.now()
            .isoformat()

        }


        for provider in providers:


            name = provider.get(
                "name"
            )


            # V1.1
            # เตรียม Adapter
            # ยังไม่เรียก API จริง


            if name == "download_preview":

                continue


            if self.logger:

                self.logger.info(
                    "Image provider checked",
                    {
                        "provider": name,
                        "keyword": keyword
                    }
                )



        return result

"""
Project : Blogger Download Auto Post V1.1
Module  : Config Loader
Version : 1.1.0

หน้าที่:
- โหลดไฟล์ Config ทั้งหมดจากโฟลเดอร์ config
- ตรวจสอบว่าไฟล์ Config มีอยู่จริง
- ส่งค่า Config ให้ Module อื่นใช้งาน
"""

import json
from pathlib import Path


class ConfigLoader:

    def __init__(self, config_path="config"):
        self.config_path = Path(config_path)

        self.config = {}


    def load_file(self, filename):

        file_path = self.config_path / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {file_path}"
            )

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)


    def load_all(self):

        files = {
            "blogs": "blogs.json",
            "settings": "settings.json",
            "profiles": "profiles.json",
            "prompts": "prompts.json",
            "sources": "sources.json",
            "image_sources": "image_sources.json",
            "workflow": "workflow.json"
        }


        for key, filename in files.items():

            self.config[key] = self.load_file(filename)


        return self.config



def load_config():

    loader = ConfigLoader()

    return loader.load_all()

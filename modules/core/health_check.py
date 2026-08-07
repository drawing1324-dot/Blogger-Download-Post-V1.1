"""
Project : Blogger Download Auto Post V1.1
Module  : Health Check
Version : 1.1.0

หน้าที่:
- ตรวจสอบระบบก่อนเริ่มทำงาน
- ตรวจสอบ Config
- ตรวจสอบ Storage
"""

from pathlib import Path


class HealthCheck:


    def __init__(self):

        self.errors = []


    def check_storage(self):

        folders = [
            "storage",
            "storage/queue",
            "storage/posted",
            "storage/logs",
            "storage/cache"
        ]


        for folder in folders:

            path = Path(folder)

            if not path.exists():

                path.mkdir(
                    parents=True,
                    exist_ok=True
                )


    def check_config(self, config):

        required = [
            "blogs",
            "settings",
            "profiles",
            "workflow"
        ]


        for item in required:

            if item not in config:

                self.errors.append(
                    f"Missing config: {item}"
                )


    def run(self, config):

        self.check_storage()

        self.check_config(config)


        return {
            "status": len(self.errors) == 0,
            "errors": self.errors
        }

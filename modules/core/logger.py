"""
Project : Blogger Download Auto Post V1.1
Module  : Logger
Version : 1.1.1

หน้าที่:
- สร้าง Log การทำงาน
- แสดง Log บน Console (GitHub Actions)
- เก็บ Log แบบ JSONL
"""

import json
from datetime import datetime
from pathlib import Path


class Logger:

    def __init__(self, log_path="storage/logs"):

        self.log_path = Path(log_path)

        self.log_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def write(
        self,
        level,
        message,
        data=None
    ):

        now = datetime.now()

        filename = now.strftime("%Y-%m-%d") + ".jsonl"

        file_path = self.log_path / filename

        record = {
            "time": now.isoformat(),
            "level": level,
            "message": message,
            "data": data
        }

        # แสดงบน GitHub Actions
        print(
            json.dumps(
                record,
                ensure_ascii=False
            ),
            flush=True
        )

        # บันทึกลงไฟล์
        with open(
            file_path,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    def info(
        self,
        message,
        data=None
    ):

        self.write(
            "INFO",
            message,
            data
        )

    def warning(
        self,
        message,
        data=None
    ):

        self.write(
            "WARNING",
            message,
            data
        )

    def error(
        self,
        message,
        data=None
    ):

        self.write(
            "ERROR",
            message,
            data
        )

"""
Project : Blogger Download Auto Post V1.1
Module  : Backup Manager

หน้าที่:
- Backup Queue ก่อนประมวลผล
- ป้องกันข้อมูลหาย
"""

import json
import shutil
from pathlib import Path
from datetime import datetime



class BackupManager:


    def __init__(
        self,
        storage="storage"
    ):

        self.storage = Path(
            storage
        )

        self.backup = (
            self.storage /
            "backup"
        )


        self.backup.mkdir(
            parents=True,
            exist_ok=True
        )



    def backup_file(
        self,
        file_path
    ):


        source = Path(
            file_path
        )


        if not source.exists():

            return False



        filename = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S_"
            )
            +
            source.name
        )


        destination = (
            self.backup /
            filename
        )


        shutil.copy(
            source,
            destination
        )


        return True



    def list_backup(self):

        return list(
            self.backup.glob(
                "*.json"
            )
        )

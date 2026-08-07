"""
Project : Blogger Download Auto Post V1.1

System Audit Tool

หน้าที่:
- ตรวจสอบไฟล์ระบบ
- ตรวจสอบ Folder
- ตรวจสอบ Config
"""


from pathlib import Path
import json



FILES = [

    "main.py",

    "test_system.py",

    "requirements.txt",

    "README.md",


    "config/blogs.json",

    "config/settings.json",

    "config/profiles.json",

    "config/prompts.json",

    "config/sources.json",

    "config/workflow.json",


    "modules/core/config_loader.py",

    "modules/core/logger.py",

    "modules/core/health_check.py",

    "modules/core/workflow.py",

    "modules/core/queue_manager.py",

    "modules/core/backup_manager.py",

    "modules/core/limit_manager.py",


    "modules/ai/gemini.py",

    "modules/ai/topic_generator.py",

    "modules/ai/article_writer.py",


    "modules/search/provider.py",

    "modules/search/source_adapter.py",


    "modules/image/provider.py",


    "modules/blogger/publisher.py"

]



FOLDERS = [

    "config",

    "modules",

    "storage",

    "storage/queue",

    "storage/backup",

    "storage/logs",

    "storage/cache"

]



def check_files():


    print("\nChecking Files\n")


    missing = []


    for file in FILES:


        if Path(file).exists():


            print(
                "[OK]",
                file
            )


        else:


            print(
                "[MISSING]",
                file
            )


            missing.append(
                file
            )


    return missing



def check_folders():


    print("\nChecking Folders\n")


    for folder in FOLDERS:


        if Path(folder).exists():


            print(
                "[OK]",
                folder
            )


        else:


            Path(folder).mkdir(
                parents=True,
                exist_ok=True
            )


            print(
                "[CREATE]",
                folder
            )



def check_json():


    print("\nChecking JSON\n")


    configs = [

        "config/blogs.json",

        "config/settings.json",

        "config/profiles.json",

        "config/prompts.json",

        "config/sources.json",

        "config/workflow.json"

    ]


    for file in configs:


        try:


            with open(
                file,
                encoding="utf-8"
            ) as f:

                json.load(f)


            print(
                "[OK]",
                file
            )


        except Exception as error:


            print(
                "[ERROR]",
                file,
                error
            )



def main():


    print(
        "=== SYSTEM AUDIT START ==="
    )


    check_files()


    check_folders()


    check_json()


    print(
        "\n=== AUDIT COMPLETE ==="
    )



if __name__ == "__main__":

    main()

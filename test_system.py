"""
Project : Blogger Download Auto Post V1.1

System Test

หน้าที่:
- ตรวจสอบความพร้อมระบบ
- ทดสอบ Config
- ทดสอบ Queue
- ทดสอบ Module หลัก
"""

import os

from modules.core.config_loader import load_config
from modules.core.health_check import HealthCheck
from modules.core.logger import Logger
from modules.core.queue_manager import QueueManager



def test_config():

    print(
        "[TEST] Loading Config..."
    )


    config = load_config()


    print(
        "[OK] Config Loaded"
    )


    return config



def test_health(config):


    print(
        "[TEST] Health Check..."
    )


    health = HealthCheck()


    result = health.run(
        config
    )


    if result["status"]:

        print(
            "[OK] System Ready"
        )

    else:

        print(
            "[ERROR]",
            result["errors"]
        )



def test_queue(config):


    print(
        "[TEST] Queue System..."
    )


    queue = QueueManager()


    blog = config["blogs"][0]


    queue.add_topic(

        blog["blog_id"],

        {
            "title":
            "Free Test 3D Graphic Download"
        }

    )


    item = queue.get_next(

        blog["blog_id"]

    )


    if item:

        print(
            "[OK] Queue Working"
        )

        print(
            item
        )

    else:

        print(
            "[ERROR] Queue Failed"
        )



def test_secret():


    print(
        "[TEST] Checking Secrets..."
    )


    keys = [

        "GEMINI_API_KEY",

        "MAIN_REFRESH_TOKEN",

        "MAIN_CLIENT_ID",

        "MAIN_CLIENT_SECRET"

    ]


    for key in keys:


        if os.getenv(key):

            print(
                "[OK]",
                key
            )

        else:

            print(
                "[WARN] Missing",
                key
            )



def main():


    logger = Logger()


    logger.info(
        "System Test Started"
    )


    config = test_config()


    test_health(
        config
    )


    test_queue(
        config
    )


    test_secret()



    print(
        "\nTEST COMPLETE"
    )



if __name__ == "__main__":

    main()

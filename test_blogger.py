"""
Project : Blogger Download Auto Post V1.1

Blogger API Test

หน้าที่:
- ตรวจการเชื่อมต่อ Blogger
- สร้าง Draft ทดสอบ
"""

import json

from modules.blogger.publisher import BloggerPublisher



def load_first_blog():


    with open(

        "config/blogs.json",

        encoding="utf-8"

    ) as file:


        blogs = json.load(file)


    return blogs[0]



def main():


    print(
        "=== BLOGGER TEST START ==="
    )



    blog = load_first_blog()



    print(
        "Testing:",
        blog["name"]
    )



    publisher = BloggerPublisher()



    result = publisher.publish(

        blog_id=blog["blog_id"],

        title=
        "Blogger API Test Draft",

        content=

        """
        This is a test draft.

        Blogger API connection test.

        Do not publish.

        """,

        publish=False

    )



    print(
        "API Response:"
    )


    print(
        result
    )


    print(
        "=== BLOGGER TEST END ==="
    )



if __name__ == "__main__":

    main()

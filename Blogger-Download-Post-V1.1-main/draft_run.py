"""
Project : Blogger Download Auto Post V1.1

Draft Pipeline Runner

หน้าที่:
- ทดสอบ Pipeline จริง
- สร้าง Draft Blogger
- ไม่ Publish
"""


from modules.core.config_loader import load_config
from modules.core.logger import Logger
from modules.core.queue_manager import QueueManager

from modules.ai.gemini import GeminiAI
from modules.ai.article_writer import ArticleWriter
from modules.ai.topic_generator import TopicGenerator

from modules.image.provider import ImageProvider

from modules.blogger.publisher import BloggerPublisher



def main():


    logger = Logger()


    print(
        "=== DRAFT PIPELINE START ==="
    )


    config = load_config()



    # ใช้ Blog แรกก่อน

    blog = (
        config["blogs"][0]
    )



    logger.info(

        "Testing Blog",

        {
            "name":
            blog["name"]
        }

    )



    queue = QueueManager()



    ai = GeminiAI(
        logger
    )



    topic_generator = TopicGenerator(

        ai,

        config,

        logger

    )


    writer = ArticleWriter(

        ai,

        config,

        logger

    )



    image = ImageProvider(

        config,

        logger

    )



    publisher = BloggerPublisher(

        logger=logger

    )



    # Generate Topic


    topics = (
        topic_generator
        .generate(
            blog
        )
    )



    if not topics:

        print(
            "No Topic"
        )

        return



    topic = topics[0]



    print(

        "Topic:",

        topic

    )



    # Write Article


    article = (

        writer
        .generate(

            blog,

            topic

        )

    )



    if not article:


        print(

            "Article Failed"

        )

        return



    # Image


    image_result = (

        image
        .find_image(

            topic

        )

    )



    # Blogger Draft


    result = (

        publisher
        .publish(

            blog["blog_id"],

            article["title"],

            article["content"],

            False

        )

    )



    print(
        "Draft Created"
    )


    print(
        result.get(
            "url",
            ""
        )
    )


    print(
        "=== COMPLETE ==="
    )



if __name__ == "__main__":

    main()

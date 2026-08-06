"""
Project : Blogger Download Auto Post V1.1
Main Controller

Version : 1.1.1

หน้าที่:
- ควบคุมระบบทั้งหมด
- รองรับ Backup
- รองรับ Limit
- ทำงานแบบปลอดภัย
"""


from modules.core.config_loader import load_config
from modules.core.logger import Logger
from modules.core.health_check import HealthCheck
from modules.core.workflow import WorkflowController
from modules.core.queue_manager import QueueManager
from modules.core.backup_manager import BackupManager
from modules.core.limit_manager import LimitManager


from modules.ai.gemini import GeminiAI
from modules.ai.topic_generator import TopicGenerator
from modules.ai.article_writer import ArticleWriter


from modules.search.source_adapter import SourceAdapter
from modules.search.provider import SearchProvider


from modules.image.provider import ImageProvider


from modules.blogger.publisher import BloggerPublisher



def process_blog(
    blog,
    config,
    logger,
    workflow,
    queue,
    backup,
    limit,
    topic_generator,
    article_writer,
    source_adapter,
    search,
    image,
    publisher
):


    blog_id = blog["blog_id"]


    logger.info(
        "Start Blog Process",
        {
            "blog":
            blog["name"]
        }
    )



    # ตรวจจำนวนโพสต์

    max_post = (
        config["settings"]
        .get("schedule", {})
        .get("posts_per_run", 1)
    )


    if not limit.can_post(
        max_post
    ):

        logger.warning(
            "Daily limit reached"
        )

        return



    # Backup Queue


    queue_file = (
        queue.get_queue_file(
            blog_id
        )
    )


    backup.backup_file(
        queue_file
    )



    # Generate Topic


    current_queue = (
        queue.load_queue(
            blog_id
        )
    )


    minimum_queue = (
        config["settings"]
        ["queue"]
        ["minimum_topics"]
    )


    if len(current_queue) < minimum_queue:


        if workflow.is_enabled(
            "generate_topics"
        ):


            topics = (
                topic_generator
                .generate(
                    blog
                )
            )


            for topic in topics:


                queue.add_topic(
                    blog_id,
                    topic
                )



    # Get Topic


    item = queue.get_next(
        blog_id
    )


    if not item:


        logger.warning(
            "No topic available"
        )

        return



    title = item["title"]



    try:



        # Search


        if workflow.is_enabled(
            "search_download"
        ):


            targets = (
                source_adapter
                .build_search_targets(
                    blog["type"],
                    title
                )
            )


            search.search(
                title
            )



        # Article


        article = (
            article_writer
            .generate(
                blog,
                title
            )
        )



        # Image


        if workflow.is_enabled(
            "find_images"
        ):


            image.find_image(
                title
            )



        # Publish


        if workflow.allow_publish():


            publisher.publish(

                blog_id,

                article["title"],

                article["content"],

                True

            )


            queue.archive_post(
                blog_id,
                title
            )


            limit.increase()


            logger.info(
                "Post completed",
                {
                    "title": title
                }
            )


        else:


            logger.info(
                "Draft mode",
                {
                    "title": title
                }
            )



    except Exception as error:


        logger.error(

            "Process failed",

            {
                "title": title,

                "error":
                str(error)
            }

        )





def main():


    logger = Logger()


    logger.info(
        "System Starting"
    )



    config = load_config()



    health = HealthCheck()


    check = health.run(
        config
    )


    if not check["status"]:

        logger.error(
            "Health Check Failed",
            check
        )

        return



    workflow = WorkflowController(
        config["workflow"],
        logger
    )


    queue = QueueManager()


    backup = BackupManager()


    limit = LimitManager()



    ai = GeminiAI(
        logger=logger
    )



    topic_generator = TopicGenerator(

        ai,

        config,

        logger

    )



    article_writer = ArticleWriter(

        ai,

        config,

        logger

    )



    source_adapter = SourceAdapter(

        config,

        logger

    )



    search = SearchProvider(

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



    for blog in config["blogs"]:


        if not blog.get(
            "enabled",
            False
        ):

            continue



        process_blog(

            blog,

            config,

            logger,

            workflow,

            queue,

            backup,

            limit,

            topic_generator,

            article_writer,

            source_adapter,

            search,

            image,

            publisher

        )



    logger.info(
        "System Finished"
    )




if __name__ == "__main__":

    main()

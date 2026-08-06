"""
Project : Blogger Download Auto Post V1.1
Main Controller

Version : 1.1.0

หน้าที่:
- ควบคุมการทำงานทั้งหมด
"""

from modules.core.config_loader import load_config
from modules.core.logger import Logger
from modules.core.health_check import HealthCheck
from modules.core.workflow import WorkflowController
from modules.core.queue_manager import QueueManager

from modules.ai.gemini import GeminiAI
from modules.ai.topic_generator import TopicGenerator
from modules.ai.article_writer import ArticleWriter

from modules.search.source_adapter import SourceAdapter
from modules.search.provider import SearchProvider

from modules.image.provider import ImageProvider

from modules.blogger.publisher import BloggerPublisher



def main():


    logger = Logger()


    logger.info(
        "System starting"
    )


    try:


        # Load Config

        config = load_config()


        logger.info(
            "Config loaded"
        )


        # Health Check

        health = HealthCheck()


        result = health.run(
            config
        )


        if not result["status"]:

            logger.error(
                "Health check failed",
                result
            )

            return



        workflow = WorkflowController(
            config["workflow"],
            logger
        )


        queue = QueueManager()



        # AI

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



        # Search

        source_adapter = SourceAdapter(
            config,
            logger
        )


        search = SearchProvider(
            config,
            logger
        )



        # Image

        image = ImageProvider(
            config,
            logger
        )



        # Blogger

        publisher = BloggerPublisher(
            logger=logger
        )



        for blog in config["blogs"]:


            if not blog.get(
                "enabled",
                False
            ):

                continue



            blog_id = blog["blog_id"]



            logger.info(
                "Processing blog",
                {
                    "blog":
                    blog["name"]
                }
            )



            # Generate Topic

            current_queue = (
                queue.load_queue(
                    blog_id
                )
            )


            if len(current_queue) < 10:


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



            # Get Next Topic


            item = queue.get_next(
                blog_id
            )


            if not item:

                continue



            title = item["title"]



            # Search


            if workflow.is_enabled(
                "search_download"
            ):


                source = (
                    source_adapter
                    .build_search_targets(
                        blog["type"],
                        title
                    )
                )


                search.search(
                    title
                )



            # Write Article


            article = None


            if workflow.is_enabled(
                "write_article"
            ):


                article = (
                    article_writer
                    .generate(
                        blog,
                        title
                    )
                )



            if not article:

                continue



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



        logger.info(
            "System completed"
        )



    except Exception as error:


        logger.error(
            "System crashed",
            {
                "error": str(error)
            }
        )


        raise



if __name__ == "__main__":

    main()

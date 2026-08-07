"""
Project : Blogger Download Auto Post V1.1
Main Controller

Version : 1.2.0

หน้าที่:

- ควบคุมระบบทั้งหมด
- รองรับ Backup
- รองรับ Limit
- ทำงานแบบปลอดภัย
- แสดง Log ทุกขั้นตอน
- แสดงรายละเอียด Exception
"""

import traceback


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


def log_exception(
    logger,
    message,
    error,
    data=None
):
    """
    บันทึก Exception พร้อม Traceback เต็ม
    """

    payload = {}

    if data:
        payload.update(data)

    payload["error_type"] = type(error).__name__
    payload["error"] = str(error)
    payload["traceback"] = traceback.format_exc()

    logger.error(
        message,
        payload
    )


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
    blog_name = blog.get("name", blog_id)

    logger.info(
        "Start Blog Process",
        {
            "blog": blog_name,
            "blog_id": blog_id,
            "blog_type": blog.get("type"),
            "language": blog.get("language")
        }
    )


    # ---------------------------------------------------------
    # ตรวจจำนวนโพสต์
    # ---------------------------------------------------------

    max_post = (
        config.get("settings", {})
        .get("schedule", {})
        .get("posts_per_run", 1)
    )

    logger.info(
        "Checking posting limit",
        {
            "blog_id": blog_id,
            "posts_per_run": max_post
        }
    )


    try:

        allowed = limit.can_post(
            max_post,
            blog_id
        )

    except Exception as error:

        log_exception(
            logger,
            "Posting limit check failed",
            error,
            {
                "blog_id": blog_id,
                "blog": blog_name
            }
        )

        return


    if not allowed:

        logger.warning(
            "Daily limit reached",
            {
                "blog_id": blog_id,
                "blog": blog_name,
                "posts_per_run": max_post
            }
        )

        return


    logger.info(
        "Posting limit available",
        {
            "blog_id": blog_id,
            "posts_per_run": max_post
        }
    )


    # ---------------------------------------------------------
    # Backup Queue
    # ---------------------------------------------------------

    logger.info(
        "Preparing queue backup",
        {
            "blog_id": blog_id
        }
    )


    try:

        queue_file = (
            queue.get_queue_file(
                blog_id
            )
        )

        logger.info(
            "Queue file located",
            {
                "blog_id": blog_id,
                "queue_file": str(queue_file)
            }
        )


        backup.backup_file(
            queue_file
        )

        logger.info(
            "Queue backup completed",
            {
                "blog_id": blog_id
            }
        )

    except Exception as error:

        log_exception(
            logger,
            "Queue backup failed",
            error,
            {
                "blog_id": blog_id,
                "blog": blog_name
            }
        )

        return


    # ---------------------------------------------------------
    # Load Queue
    # ---------------------------------------------------------

    logger.info(
        "Loading topic queue",
        {
            "blog_id": blog_id
        }
    )


    try:

        current_queue = (
            queue.load_queue(
                blog_id
            )
        )

    except Exception as error:

        log_exception(
            logger,
            "Queue loading failed",
            error,
            {
                "blog_id": blog_id
            }
        )

        return


    queue_count = len(current_queue)

    logger.info(
        "Topic queue loaded",
        {
            "blog_id": blog_id,
            "queue_count": queue_count
        }
    )


    # ---------------------------------------------------------
    # Generate Topic
    # ---------------------------------------------------------

    minimum_queue = (
        config.get("settings", {})
        .get("queue", {})
        .get("minimum_topics", 10)
    )


    logger.info(
        "Checking topic queue minimum",
        {
            "blog_id": blog_id,
            "current_queue": queue_count,
            "minimum_queue": minimum_queue
        }
    )


    if queue_count < minimum_queue:

        logger.info(
            "Topic queue below minimum",
            {
                "blog_id": blog_id,
                "current_queue": queue_count,
                "minimum_queue": minimum_queue
            }
        )


        if workflow.is_enabled(
            "generate_topics"
        ):

            logger.info(
                "Starting topic generation",
                {
                    "blog_id": blog_id,
                    "blog": blog_name
                }
            )


            try:

                topics = (
                    topic_generator
                    .generate(
                        blog
                    )
                )

                logger.info(
                    "Topic generation completed",
                    {
                        "blog_id": blog_id,
                        "topics_generated": len(topics)
                    }
                )


                added_topics = 0

                for topic in topics:

                    try:

                        queue.add_topic(
                            blog_id,
                            topic
                        )

                        added_topics += 1

                    except Exception as error:

                        log_exception(
                            logger,
                            "Failed to add generated topic to queue",
                            error,
                            {
                                "blog_id": blog_id,
                                "topic": topic
                            }
                        )


                logger.info(
                    "Generated topics added to queue",
                    {
                        "blog_id": blog_id,
                        "topics_generated": len(topics),
                        "topics_added": added_topics
                    }
                )

            except Exception as error:

                log_exception(
                    logger,
                    "Topic generation failed",
                    error,
                    {
                        "blog_id": blog_id,
                        "blog": blog_name
                    }
                )

                return

        else:

            logger.info(
                "Topic generation workflow disabled",
                {
                    "blog_id": blog_id
                }
            )

    else:

        logger.info(
            "Topic queue is sufficient",
            {
                "blog_id": blog_id,
                "current_queue": queue_count,
                "minimum_queue": minimum_queue
            }
        )


    # ---------------------------------------------------------
    # Get Topic
    # ---------------------------------------------------------

    logger.info(
        "Getting next topic",
        {
            "blog_id": blog_id
        }
    )


    try:

        item = queue.get_next(
            blog_id
        )

    except Exception as error:

        log_exception(
            logger,
            "Failed to get next topic",
            error,
            {
                "blog_id": blog_id
            }
        )

        return


    if not item:

        logger.warning(
            "No topic available",
            {
                "blog_id": blog_id,
                "blog": blog_name
            }
        )

        return


    title = item.get(
        "title",
        ""
    )


    if not title:

        logger.warning(
            "Queue item has no title",
            {
                "blog_id": blog_id,
                "item": item
            }
        )

        return


    logger.info(
        "Topic selected",
        {
            "blog_id": blog_id,
            "title": title
        }
    )


    # ---------------------------------------------------------
    # Continue in Part 2
    # Search
    # Image
    # Article
    # Publish / Schedule
    # ---------------------------------------------------------


    # ---------------------------------------------------------
    # Search / Download Source
    # ---------------------------------------------------------

    logger.info(
        "Starting source search",
        {
            "blog_id": blog_id,
            "title": title,
            "blog_type": blog.get("type")
        }
    )


    try:

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


            logger.info(
                "Search targets created",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "target_count": len(targets),
                    "targets": targets
                }
            )


            source_result = None


            for index, target in enumerate(
                targets,
                start=1
            ):

                source_name = target.get(
                    "source"
                )


                logger.info(
                    "Searching source",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "source": source_name,
                        "target_number": index,
                        "target_count": len(targets)
                    }
                )


                try:

                    candidate = search.search(
                        title,
                        source_name
                    )

                except Exception as error:

                    log_exception(
                        logger,
                        "Search provider failed",
                        error,
                        {
                            "blog_id": blog_id,
                            "title": title,
                            "source": source_name
                        }
                    )

                    continue


                found_url = (
                    candidate.get("found_url")
                    if candidate
                    else None
                )


                logger.info(
                    "Search result received",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "source": source_name,
                        "found_url": found_url
                    }
                )


                if found_url:

                    source_result = candidate

                    logger.info(
                        "Download source found",
                        {
                            "blog_id": blog_id,
                            "title": title,
                            "source": source_name,
                            "found_url": found_url
                        }
                    )

                    break


            if source_result is None:

                logger.warning(
                    "No download source found",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "target_count": len(targets)
                    }
                )

                return

        else:

            logger.info(
                "Search workflow disabled",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            source_result = {
                "found_url": None
            }


    except Exception as error:

        log_exception(
            logger,
            "Source search stage failed",
            error,
            {
                "blog_id": blog_id,
                "title": title
            }
        )

        return


    # ---------------------------------------------------------
    # Image
    # ---------------------------------------------------------

    logger.info(
        "Starting image search",
        {
            "blog_id": blog_id,
            "title": title
        }
    )


    try:

        if workflow.is_enabled(
            "find_images"
        ):

            image_result = image.find_image(
                title,
                (source_result or {}).get(
                    "found_url"
                )
            )


            logger.info(
                "Image search completed",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "image_url": (
                        image_result or {}
                    ).get("image_url")
                }
            )

        else:

            logger.info(
                "Image workflow disabled",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            image_result = {
                "image_url": None
            }


    except Exception as error:

        log_exception(
            logger,
            "Image search failed",
            error,
            {
                "blog_id": blog_id,
                "title": title
            }
        )

        return


    # ---------------------------------------------------------
    # Article Generation
    # ---------------------------------------------------------

    logger.info(
        "Starting article generation",
        {
            "blog_id": blog_id,
            "title": title
        }
    )


    try:

        article = article_writer.generate(
            blog,
            title,
            source_result,
            image_result
        )


    except Exception as error:

        log_exception(
            logger,
            "Article generation failed",
            error,
            {
                "blog_id": blog_id,
                "title": title
            }
        )

        return


    if not article:

        logger.error(
            "Article generation returned empty result",
            {
                "blog_id": blog_id,
                "title": title
            }
        )

        return


    article_title = article.get(
        "title",
        title
    )


    article_content = article.get(
        "content",
        ""
    )


    logger.info(
        "Article generation completed",
        {
            "blog_id": blog_id,
            "queue_title": title,
            "article_title": article_title,
            "content_length": len(article_content)
        }
    )


    if not article_content:

        logger.error(
            "Generated article has empty content",
            {
                "blog_id": blog_id,
                "title": title,
                "article_title": article_title
            }
        )

        return


    # ---------------------------------------------------------
    # Publish workflow check
    # ---------------------------------------------------------

    logger.info(
        "Checking publish permission",
        {
            "blog_id": blog_id,
            "title": article_title
        }
    )


    try:

        publish_allowed = (
            workflow.allow_publish()
        )


    except Exception as error:

        log_exception(
            logger,
            "Publish permission check failed",
            error,
            {
                "blog_id": blog_id,
                "title": article_title
            }
        )

        return


    logger.info(
        "Publish permission result",
        {
            "blog_id": blog_id,
            "title": article_title,
            "allow_publish": publish_allowed
        }
    )


    # ---------------------------------------------------------
    # Continue in Part 3
    # Blogger Publish / Schedule
    # Queue Archive
    # Limit
    # Error handling
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Publish / Schedule
    # ---------------------------------------------------------

    if publish_allowed:

        logger.info(
            "Starting Blogger publish process",
            {
                "blog_id": blog_id,
                "title": article_title
            }
        )


        try:

            publish_result = publisher.publish(

                blog_id,

                article_title,

                article_content,

                True

            )


            if not publish_result:

                logger.error(
                    "Blogger publisher returned empty result",
                    {
                        "blog_id": blog_id,
                        "title": article_title
                    }
                )

                return


            logger.info(
                "Blogger publish process completed",
                {
                    "blog_id": blog_id,
                    "title": article_title,
                    "post_id": publish_result.get("id"),
                    "url": publish_result.get("url"),
                    "status": publish_result.get("status"),
                    "published": publish_result.get("published")
                }
            )


        except Exception as error:

            log_exception(
                logger,
                "Blogger publish failed",
                error,
                {
                    "blog_id": blog_id,
                    "title": article_title
                }
            )

            return


        # -----------------------------------------------------
        # Archive Queue Item
        # -----------------------------------------------------

        logger.info(
            "Archiving completed queue item",
            {
                "blog_id": blog_id,
                "title": title
            }
        )


        try:

            queue.archive_post(
                blog_id,
                title
            )


            logger.info(
                "Queue item archived",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )


        except Exception as error:

            log_exception(
                logger,
                "Queue archive failed after successful publish",
                error,
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            # ไม่ return เพราะ Blogger สร้างโพสต์สำเร็จแล้ว


        # -----------------------------------------------------
        # Increase Posting Limit
        # -----------------------------------------------------

        logger.info(
            "Updating posting limit",
            {
                "blog_id": blog_id,
                "title": article_title
            }
        )


        try:

            limit.increase(
                blog_id
            )


            logger.info(
                "Posting limit updated",
                {
                    "blog_id": blog_id,
                    "title": article_title
                }
            )


        except Exception as error:

            log_exception(
                logger,
                "Posting limit update failed",
                error,
                {
                    "blog_id": blog_id,
                    "title": article_title
                }
            )


        # -----------------------------------------------------
        # Completed
        # -----------------------------------------------------

        logger.info(
            "Post completed successfully",
            {
                "blog_id": blog_id,
                "title": article_title,
                "post_id": publish_result.get("id"),
                "status": publish_result.get("status"),
                "scheduled_time": publish_result.get("published")
            }
        )


    else:

        # -----------------------------------------------------
        # Draft Mode
        # -----------------------------------------------------

        logger.info(
            "Publish disabled - draft mode",
            {
                "blog_id": blog_id,
                "title": article_title
            }
        )


    # ---------------------------------------------------------
    # Blog Process Finished
    # ---------------------------------------------------------

    logger.info(
        "Blog Process Finished",
        {
            "blog": blog_name,
            "blog_id": blog_id,
            "title": title
        }
    )


# =============================================================
# MAIN
# =============================================================

def main():

    logger = Logger()


    logger.info(
        "System Starting"
    )


    # ---------------------------------------------------------
    # Load Configuration
    # ---------------------------------------------------------

    logger.info(
        "Loading configuration"
    )


    try:

        config = load_config()


        logger.info(
            "Configuration loaded successfully"
        )


    except Exception as error:

        log_exception(
            logger,
            "Configuration loading failed",
            error
        )

        return


    # ---------------------------------------------------------
    # Health Check
    # ---------------------------------------------------------

    logger.info(
        "Starting health check"
    )


    try:

        health = HealthCheck()


        check = health.run(
            config
        )


    except Exception as error:

        log_exception(
            logger,
            "Health check execution failed",
            error
        )

        return


    logger.info(
        "Health check completed",
        check
    )


    if not check.get(
        "status",
        False
    ):

        logger.error(
            "Health Check Failed",
            check
        )

        return


    logger.info(
        "Health Check Passed"
    )


    # ---------------------------------------------------------
    # Workflow
    # ---------------------------------------------------------

    logger.info(
        "Initializing workflow controller"
    )


    try:

        workflow = WorkflowController(
            config["workflow"],
            logger
        )


    except Exception as error:

        log_exception(
            logger,
            "Workflow controller initialization failed",
            error
        )

        return


    logger.info(
        "Workflow controller initialized"
    )


    # ---------------------------------------------------------
    # Core Managers
    # ---------------------------------------------------------

    logger.info(
        "Initializing queue manager"
    )

    try:

        queue = QueueManager()

    except Exception as error:

        log_exception(
            logger,
            "Queue manager initialization failed",
            error
        )

        return


    logger.info(
        "Queue manager initialized"
    )


    logger.info(
        "Initializing backup manager"
    )

    try:

        backup = BackupManager()

    except Exception as error:

        log_exception(
            logger,
            "Backup manager initialization failed",
            error
        )

        return


    logger.info(
        "Backup manager initialized"
    )


    logger.info(
        "Initializing limit manager"
    )

    try:

        limit = LimitManager()

    except Exception as error:

        log_exception(
            logger,
            "Limit manager initialization failed",
            error
        )

        return


    logger.info(
        "Limit manager initialized"
    )


    # ---------------------------------------------------------
    # Continue in Part 4
    # AI / Search / Image / Publisher initialization
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

    logger.info(
        "Initializing Gemini AI"
    )

    try:

        ai = GeminiAI(
            logger=logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Gemini AI initialization failed",
            error
        )

        return


    logger.info(
        "Gemini AI initialized"
    )


    # ---------------------------------------------------------
    # Topic Generator
    # ---------------------------------------------------------

    logger.info(
        "Initializing topic generator"
    )

    try:

        topic_generator = TopicGenerator(
            ai,
            config,
            logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Topic generator initialization failed",
            error
        )

        return


    logger.info(
        "Topic generator initialized"
    )


    # ---------------------------------------------------------
    # Article Writer
    # ---------------------------------------------------------

    logger.info(
        "Initializing article writer"
    )

    try:

        article_writer = ArticleWriter(
            ai,
            config,
            logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Article writer initialization failed",
            error
        )

        return


    logger.info(
        "Article writer initialized"
    )


    # ---------------------------------------------------------
    # Source Adapter
    # ---------------------------------------------------------

    logger.info(
        "Initializing source adapter"
    )

    try:

        source_adapter = SourceAdapter(
            config,
            logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Source adapter initialization failed",
            error
        )

        return


    logger.info(
        "Source adapter initialized"
    )


    # ---------------------------------------------------------
    # Search Provider
    # ---------------------------------------------------------

    logger.info(
        "Initializing search provider"
    )

    try:

        search = SearchProvider(
            config,
            logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Search provider initialization failed",
            error
        )

        return


    logger.info(
        "Search provider initialized"
    )


    # ---------------------------------------------------------
    # Image Provider
    # ---------------------------------------------------------

    logger.info(
        "Initializing image provider"
    )

    try:

        image = ImageProvider(
            config,
            logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Image provider initialization failed",
            error
        )

        return


    logger.info(
        "Image provider initialized"
    )


    # ---------------------------------------------------------
    # Blogger Publisher
    # ---------------------------------------------------------

    logger.info(
        "Initializing Blogger publisher"
    )

    try:

        publisher = BloggerPublisher(
            logger=logger
        )

    except Exception as error:

        log_exception(
            logger,
            "Blogger publisher initialization failed",
            error
        )

        return


    logger.info(
        "Blogger publisher initialized"
    )


    # ---------------------------------------------------------
    # Blog Processing
    # ---------------------------------------------------------

    blogs = config.get(
        "blogs",
        []
    )


    logger.info(
        "Starting blog processing",
        {
            "total_blogs": len(blogs)
        }
    )


    processed_blogs = 0
    skipped_blogs = 0


    for index, blog in enumerate(
        blogs,
        start=1
    ):

        blog_name = blog.get(
            "name",
            f"Blog #{index}"
        )

        blog_id = blog.get(
            "blog_id"
        )


        logger.info(
            "Checking blog",
            {
                "index": index,
                "total_blogs": len(blogs),
                "blog": blog_name,
                "blog_id": blog_id,
                "enabled": blog.get(
                    "enabled",
                    False
                )
            }
        )


        if not blog.get(
            "enabled",
            False
        ):

            skipped_blogs += 1


            logger.info(
                "Blog disabled - skipping",
                {
                    "blog": blog_name,
                    "blog_id": blog_id
                }
            )

            continue


        processed_blogs += 1


        logger.info(
            "Starting enabled blog",
            {
                "index": index,
                "blog": blog_name,
                "blog_id": blog_id
            }
        )


        try:

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
                "Enabled blog process returned",
                {
                    "blog": blog_name,
                    "blog_id": blog_id
                }
            )


        except Exception as error:

            log_exception(
                logger,
                "Unhandled blog process exception",
                error,
                {
                    "blog": blog_name,
                    "blog_id": blog_id
                }
            )


            # สำคัญ:
            # ไม่หยุดระบบทั้งหมดเพราะ Blog เดียวมีปัญหา
            continue


    # ---------------------------------------------------------
    # System Summary
    # ---------------------------------------------------------

    logger.info(
        "Blog processing completed",
        {
            "total_blogs": len(blogs),
            "processed_blogs": processed_blogs,
            "skipped_blogs": skipped_blogs
        }
    )


    logger.info(
        "System Finished"
    )


# =============================================================
# PROGRAM ENTRY POINT
# =============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        # Logger อาจสร้างไม่ได้ในกรณีร้ายแรงมาก
        # จึงพยายามบันทึกผ่าน Logger ก่อน

        try:

            fatal_logger = Logger()

            log_exception(
                fatal_logger,
                "Fatal system error",
                error
            )

        except Exception:

            print(
                "FATAL SYSTEM ERROR:",
                str(error)
            )

            traceback.print_exc()

        raise





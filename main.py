"""
Project : Blogger Download Auto Post V1.1
Main Controller

Version : 1.1.2

หน้าที่:

- ควบคุมระบบทั้งหมด
- รองรับ Backup
- รองรับ Limit
- รองรับ Topic Queue
- ค้นหา Source แบบหลายแหล่ง
- ไม่หยุดทั้ง Blog เมื่อ Source ใด Source หนึ่งหาไม่พบ
- สร้างบทความ
- ส่งบทความให้ Blogger Publisher
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
    """
    ประมวลผล Blog หนึ่งรายการ

    Flow:

    Queue
      ↓
    Generate Topic
      ↓
    Select Topic
      ↓
    Search Source
      ↓
    Find Image
      ↓
    Generate Article
      ↓
    Publish / Draft
      ↓
    Archive Queue
    """

    blog_id = blog["blog_id"]

    logger.info(
        "Start Blog Process",
        {
            "blog": blog["name"],
            "blog_id": blog_id
        }
    )

    # ---------------------------------------------------------
    # ตรวจจำนวนโพสต์
    # ---------------------------------------------------------

    max_post = (
        config
        .get("settings", {})
        .get("schedule", {})
        .get("posts_per_run", 1)
    )

    logger.info(
        "Checking posting limit",
        {
            "blog_id": blog_id,
            "max_post": max_post
        }
    )

    if not limit.can_post(
        max_post,
        blog_id
    ):

        logger.warning(
            "Daily limit reached",
            {
                "blog_id": blog_id
            }
        )

        return False

    # ---------------------------------------------------------
    # Backup Queue
    # ---------------------------------------------------------

    queue_file = queue.get_queue_file(
        blog_id
    )

    backup.backup_file(
        queue_file
    )

    # ---------------------------------------------------------
    # Load Queue
    # ---------------------------------------------------------

    current_queue = queue.load_queue(
        blog_id
    )

    minimum_queue = (
        config
        .get("settings", {})
        .get("queue", {})
        .get("minimum_topics", 10)
    )

    logger.info(
        "Checking topic queue minimum",
        {
            "blog_id": blog_id,
            "current_queue": len(current_queue),
            "minimum_queue": minimum_queue
        }
    )

    # ---------------------------------------------------------
    # Generate Topics
    # ---------------------------------------------------------

    if len(current_queue) < minimum_queue:

        logger.info(
            "Topic queue below minimum",
            {
                "blog_id": blog_id,
                "current_queue": len(current_queue),
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
                    "blog": blog["name"]
                }
            )

            topics = topic_generator.generate(
                blog
            )

            added_count = 0

            for topic in topics:

                if queue.add_topic(
                    blog_id,
                    topic
                ):

                    added_count += 1

            logger.info(
                "Generated topics added to queue",
                {
                    "blog_id": blog_id,
                    "topics_generated": len(topics),
                    "topics_added": added_count
                }
            )

    # ---------------------------------------------------------
    # Get Topic
    # ---------------------------------------------------------

    item = queue.get_next(
        blog_id
    )

    if not item:

        logger.warning(
            "No topic available",
            {
                "blog_id": blog_id
            }
        )

        return False

    title = item["title"]

    logger.info(
        "Topic selected",
        {
            "blog_id": blog_id,
            "title": title
        }
    )

    # ---------------------------------------------------------
    # Search Source
    # ---------------------------------------------------------

    source_result = {
        "found_url": None,
        "results": []
    }

    try:

        if workflow.is_enabled(
            "search_download"
        ):

            logger.info(
                "Starting source search",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "blog_type": blog.get("type")
                }
            )

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

            for index, target in enumerate(
                targets,
                start=1
            ):

                source_name = target.get(
                    "source"
                )

                keyword = target.get(
                    "keyword",
                    title
                )

                logger.info(
                    "Searching source",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "source": source_name,
                        "keyword": keyword,
                        "target_number": index,
                        "target_count": len(targets)
                    }
                )

                candidate = search.search(
                    keyword,
                    source_name
                )

                logger.info(
                    "Search result received",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "source": source_name,
                        "found_url": candidate.get(
                            "found_url"
                        ),
                        "result_count": len(
                            candidate.get(
                                "results",
                                []
                            )
                        )
                    }
                )

                if candidate.get(
                    "found_url"
                ):

                    source_result = candidate

                    logger.info(
                        "Download source found",
                        {
                            "blog_id": blog_id,
                            "title": title,
                            "source": source_name,
                            "found_url": candidate.get(
                                "found_url"
                            )
                        }
                    )

                    break

            # -------------------------------------------------
            # ไม่มี Source
            # -------------------------------------------------

            if not source_result.get(
                "found_url"
            ):

                logger.warning(
                    "No download source found",
                    {
                        "blog_id": blog_id,
                        "title": title,
                        "target_count": len(targets)
                    }
                )

                # ไม่ archive topic
                # เพื่อให้สามารถกลับมาประมวลผลใหม่ได้
                return False

        else:

            logger.info(
                "Search workflow disabled",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

    except Exception as error:

        logger.error(
            "Source search process failed",
            {
                "blog_id": blog_id,
                "title": title,
                "error": str(error)
            }
        )

        return False

    # ---------------------------------------------------------
    # Image
    # ---------------------------------------------------------

    image_result = {
        "image_url": None
    }

    try:

        if workflow.is_enabled(
            "find_images"
        ):

            logger.info(
                "Starting image search",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            image_result = image.find_image(
                title,
                source_result.get(
                    "found_url"
                )
            )

            if not isinstance(
                image_result,
                dict
            ):

                image_result = {
                    "image_url": None
                }

            logger.info(
                "Image search completed",
                {
                    "blog_id": blog_id,
                    "title": title,
                    "image_url": image_result.get(
                        "image_url"
                    )
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

    except Exception as error:

        logger.warning(
            "Image search failed",
            {
                "blog_id": blog_id,
                "title": title,
                "error": str(error)
            }
        )

        image_result = {
            "image_url": None
        }

    # ---------------------------------------------------------
    # Article
    # ---------------------------------------------------------

    try:

        logger.info(
            "Starting article generation",
            {
                "blog_id": blog_id,
                "title": title
            }
        )

        article = article_writer.generate(
            blog,
            title,
            source_result,
            image_result
        )

        if not article:

            logger.error(
                "Article generation returned empty result",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            return False

        article_title = article.get(
            "title",
            title
        )

        article_content = article.get(
            "content"
        )

        if not article_content:

            logger.error(
                "Article content is empty",
                {
                    "blog_id": blog_id,
                    "title": title
                }
            )

            return False

        logger.info(
            "Article generation completed",
            {
                "blog_id": blog_id,
                "title": article_title,
                "content_length": len(
                    article_content
                )
            }
        )

    except Exception as error:

        logger.error(
            "Article generation failed",
            {
                "blog_id": blog_id,
                "title": title,
                "error": str(error)
            }
        )

        return False

    # ---------------------------------------------------------
    # Publish / Draft
    # ---------------------------------------------------------

    try:

        if workflow.allow_publish():

            logger.info(
                "Publishing article",
                {
                    "blog_id": blog_id,
                    "title": article_title
                }
            )

            publish_result = publisher.publish(
                blog_id,
                article_title,
                article_content,
                True
            )

            logger.info(
                "Blogger publish result received",
                {
                    "blog_id": blog_id,
                    "title": article_title,
                    "post_id": (
                        publish_result or {}
                    ).get("id"),
                    "url": (
                        publish_result or {}
                    ).get("url"),
                    "status": (
                        publish_result or {}
                    ).get("status")
                }
            )

            # ---------------------------------------------
            # Archive only after successful Blogger action
            # ---------------------------------------------

            queue.archive_post(
                blog_id,
                title
            )

            limit.increase(
                blog_id
            )

            logger.info(
                "Post completed",
                {
                    "blog_id": blog_id,
                    "title": article_title
                }
            )

            return True

        # -------------------------------------------------
        # Draft Mode
        # -------------------------------------------------

        logger.info(
            "Draft mode",
            {
                "blog_id": blog_id,
                "title": article_title
            }
        )

        return True

    except Exception as error:

        logger.error(
            "Publish process failed",
            {
                "blog_id": blog_id,
                "title": article_title,
                "error": str(error)
            }
        )

        return False


def main():

    logger = Logger()

    logger.info(
        "System Starting"
    )

    # ---------------------------------------------------------
    # Load Config
    # ---------------------------------------------------------

    try:

        config = load_config()

    except Exception as error:

        logger.error(
            "Configuration loading failed",
            {
                "error": str(error)
            }
        )

        return

    # ---------------------------------------------------------
    # Health Check
    # ---------------------------------------------------------

    health = HealthCheck()

    try:

        check = health.run(
            config
        )

    except Exception as error:

        logger.error(
            "Health Check Exception",
            {
                "error": str(error)
            }
        )

        return

    if not check.get(
        "status"
    ):

        logger.error(
            "Health Check Failed",
            check
        )

        return

    # ---------------------------------------------------------
    # Controllers
    # ---------------------------------------------------------

    workflow = WorkflowController(
        config["workflow"],
        logger
    )

    queue = QueueManager()

    backup = BackupManager()

    limit = LimitManager()

    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Providers
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Blog Processing
    # ---------------------------------------------------------

    total_blogs = len(
        config.get(
            "blogs",
            []
        )
    )

    processed_blogs = 0

    skipped_blogs = 0

    successful_blogs = 0

    failed_blogs = 0

    for index, blog in enumerate(
        config.get("blogs", []),
        start=1
    ):

        enabled = blog.get(
            "enabled",
            False
        )

        logger.info(
            "Checking blog",
            {
                "index": index,
                "total_blogs": total_blogs,
                "blog": blog.get(
                    "name"
                ),
                "blog_id": blog.get(
                    "blog_id"
                ),
                "enabled": enabled
            }
        )

        if not enabled:

            skipped_blogs += 1

            logger.info(
                "Blog disabled - skipping",
                {
                    "blog": blog.get(
                        "name"
                    ),
                    "blog_id": blog.get(
                        "blog_id"
                    )
                }
            )

            continue

        processed_blogs += 1

        try:

            success = process_blog(
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
                    "blog": blog.get(
                        "name"
                    ),
                    "blog_id": blog.get(
                        "blog_id"
                    ),
                    "success": success
                }
            )

            if success:

                successful_blogs += 1

            else:

                failed_blogs += 1

        except Exception as error:

            failed_blogs += 1

            logger.error(
                "Blog process exception",
                {
                    "blog": blog.get(
                        "name"
                    ),
                    "blog_id": blog.get(
                        "blog_id"
                    ),
                    "error": str(error)
                }
            )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    logger.info(
        "Blog processing completed",
        {
            "total_blogs": total_blogs,
            "processed_blogs": processed_blogs,
            "successful_blogs": successful_blogs,
            "failed_blogs": failed_blogs,
            "skipped_blogs": skipped_blogs
        }
    )

    logger.info(
        "System Finished"
    )


if __name__ == "__main__":

    main()

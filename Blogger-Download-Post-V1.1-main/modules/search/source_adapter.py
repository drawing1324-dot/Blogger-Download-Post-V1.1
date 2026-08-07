"""
Project : Blogger Download Auto Post V1.1
Module  : Source Adapter
Version : 1.1.0

หน้าที่:
- เลือก Source ตามประเภท Blog
- อ่านค่าจาก sources.json
- เตรียม Source สำหรับ Search Module
"""


class SourceAdapter:


    def __init__(
        self,
        config,
        logger=None
    ):

        self.sources = (
            config
            .get("sources", {})
        )

        self.logger = logger



    def get_sources(
        self,
        blog_type
    ):

        sources = (
            self.sources
            .get(
                blog_type,
                []
            )
        )


        if self.logger:

            self.logger.info(
                "Sources loaded",
                {
                    "type": blog_type,
                    "count": len(sources)
                }
            )


        return sources



    def get_primary_source(
        self,
        blog_type
    ):

        sources = self.get_sources(
            blog_type
        )


        if not sources:

            return None


        return sources[0]



    def build_search_targets(
        self,
        blog_type,
        keyword
    ):

        sources = self.get_sources(
            blog_type
        )


        targets = []


        for source in sources:

            targets.append(
                {
                    "source": source,

                    "keyword": keyword
                }
            )


        return targets

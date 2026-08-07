"""
Project : Blogger Download Auto Post V1.1

Content Quality Checker

หน้าที่:
ตรวจสอบบทความก่อนโพสต์
"""


class ContentChecker:


    def __init__(
        self,
        logger=None
    ):

        self.logger = logger



    def check(
        self,
        article
    ):


        errors = []


        title = article.get(
            "title",
            ""
        )


        content = article.get(
            "content",
            ""
        )



        if not title:

            errors.append(
                "Missing title"
            )



        if not content:

            errors.append(
                "Missing content"
            )



        if len(content) < 500:


            errors.append(
                "Content too short"
            )



        keywords = [

            "download",

            "file",

            "format",

            "use"

        ]



        text = content.lower()



        for keyword in keywords:


            if keyword not in text:


                errors.append(

                    "Missing keyword: "
                    +
                    keyword

                )



        result = {


            "approved":

            len(errors) == 0,


            "errors":

            errors

        }



        if self.logger:


            self.logger.info(

                "Content checked",

                result

            )



        return result

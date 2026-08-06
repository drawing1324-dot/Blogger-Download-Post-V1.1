"""
Project : Blogger Download Auto Post V1.1

URL Checker

หน้าที่:
- ตรวจสอบ URL
- ตรวจ Redirect
- ตรวจสถานะเว็บไซต์
"""


import requests



class URLChecker:


    def __init__(
        self,
        logger=None
    ):

        self.logger = logger



    def check(
        self,
        url
    ):


        result = {

            "url": url,

            "valid": False,

            "status": None,

            "final_url": None

        }


        try:


            response = requests.get(

                url,

                timeout=10,

                allow_redirects=True

            )


            result["status"] = (
                response.status_code
            )


            result["final_url"] = (
                response.url
            )



            if response.status_code < 400:

                result["valid"] = True



            if self.logger:

                self.logger.info(

                    "URL checked",

                    result

                )



        except Exception as error:


            if self.logger:

                self.logger.warning(

                    "URL check failed",

                    {

                        "url": url,

                        "error":
                        str(error)

                    }

                )



        return result

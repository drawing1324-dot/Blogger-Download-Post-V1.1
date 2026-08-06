"""
Project : Blogger Download Auto Post V1.1

AI Connection Test

หน้าที่:
- ทดสอบ Gemini API
- สร้างบทความตัวอย่าง
- ไม่ Publish
"""


import os
import json

from datetime import datetime



OUTPUT = (
    "storage/cache/ai_test_result.json"
)



def check_api_key():


    key = os.getenv(
        "GEMINI_API_KEY"
    )


    if not key:

        raise Exception(
            "Missing GEMINI_API_KEY"
        )


    print(
        "[OK] Gemini API Key Found"
    )



def create_test_prompt():


    return """

Create one SEO friendly article.

Topic:

Free 3D CAD Mechanical Part Download


Requirements:

- English language
- Explain file details
- Explain usage
- Include download information
- Natural SEO keywords

Return:

Title

Content

"""



def call_gemini(prompt):


    try:


        import google.generativeai as genai


        genai.configure(

            api_key=os.getenv(
                "GEMINI_API_KEY"
            )

        )


        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )


        response = model.generate_content(
            prompt
        )


        return response.text



    except Exception as error:


        return {

            "error":
            str(error)

        }



def save_result(data):


    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:


        json.dump(

            data,

            file,

            indent=2,

            ensure_ascii=False

        )



def main():


    print(
        "=== AI TEST START ==="
    )


    check_api_key()


    prompt = (
        create_test_prompt()
    )


    result = call_gemini(
        prompt
    )


    data = {


        "time":

        datetime.now()
        .isoformat(),


        "status":

        "completed",


        "publish":

        False,


        "result":

        result

    }



    save_result(
        data
    )


    print(
        "Saved:",
        OUTPUT
    )


    print(
        "=== AI TEST END ==="
    )



if __name__ == "__main__":

    main()

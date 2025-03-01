from openai import OpenAI


def test():
    import requests
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("PERPLEXITY_API_KEY")    

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "How many stars are there in our galaxy?"
            }
        ],
        "max_tokens": 123,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["https://semanticscholar.org"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "year",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "response_format": None
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)    


if __name__ == "__main__":
    test()
    # import os
    # from dotenv import load_dotenv
    # load_dotenv()
    # api_key = os.getenv("PERPLEXITY_API_KEY")

    # client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    # messages = [
    #     {
    #         "role": "system",
    #         "content": (
    #             "You are an expert at doing research on the internet."
    #         )
    #     },
    #     {
    #         "role": "user",
    #         "content": (
    #             "How many stars are there in the universe?"
    #         )
    #     }
    # ]

    # response = client.chat.completions.create(
    #     model="sonar-pro",
    #     messages=messages
    # )    
    # print(response)    
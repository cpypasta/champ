import requests, os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("JINA_API_KEY")
api_url = "https://s.jina.ai"


if __name__ == "__main__":
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Retain-Images": "none"
    }
    data = {
        "q": "What is the Python programming language?"
    }
    result = requests.post(api_url, headers=headers, data=data)
    print(result.text)
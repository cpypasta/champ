import requests, json, os
from groq import Groq

class LLMCaller:
    def __init__(self, model_name="qwen2.5:7b", base_url="http://localhost:11434/api"):
        self.model_name = model_name
        self.base_url = base_url

    def generate_groq(self, prompt: str) -> str:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        completion = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages = [
                {"role": "user", "content": prompt}
            ],
            stream=False,
            reasoning_format="hidden"
        )
        if completion:
            return completion.choices[0].message.content
        else:
            return None


    def generate_ollama(self, prompt: str, json_format: bool=True) -> str:
        url = f"{self.base_url}/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if json_format:
            payload["format"] = "json"

        response = requests.post(url, json=payload)

        if response.ok:
            json_response = response.json()["response"]
            return json_response
        else:
            print(response.text)
            return None

    def generate(self, prompt, json_format=False):
        response = self.generate_ollama(prompt, json_format=json_format)
        if response:
            if json_format:
                try:
                    return json.loads(response)
                except:                    
                    return None
            else:
                return response
        else:
            return None
        

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    caller = LLMCaller()
    print(caller.generate_groq("hello world"))
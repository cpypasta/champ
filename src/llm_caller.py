import requests, json, os, ollama
from groq import Groq
from typing import List, Dict, Callable
from tools.wiki import get_wikipedia_article
from google import genai
from google.genai import types

class LLMCaller:
    def __init__(
            self, 
            provider="ollama",
            model_name="qwen2.5:7b", 
            base_url="http://localhost:11434/api",
            tools: List[Callable] = [],
        ):
        self.provider = provider
        self.model_name = model_name
        self.base_url = base_url
        self.tools = tools
        self.tool_lookup = {
            tool.__name__: tool
            for tool in tools
        }


    def generate_gemini(self, prompt: str) -> str:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        model = "gemini-2.0-flash-lite"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ]
            )
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain"
        )

        response: types.GenerateContentResponse = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config
        )
        return response.text        


    def generate_groq(self, prompt: str) -> str:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            # model="deepseek-r1-distill-llama-70b-specdec",
            # model="qwen-qwq-32b",
            # model="llama-3.3-70b-versatile",
            messages = [
                {"role": "user", "content": prompt}
            ],
            stream=False,
            # reasoning_format="hidden"
        )
        if completion:
            return completion.choices[0].message.content
        else:
            return None


    def generate_ollama(self, prompt: str, json_format: bool=True) -> str:
        url = f"{self.base_url}/generate"
        payload = {
            # "model": "deepseek-r1:14b",
            "model": "qwen2.5:7b",
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


    def chat_ollama(
            self, 
            prompt: str, 
            format: str = None, 
            tools: List[Dict] = None,
            tool_calls: List[Dict] = []
        ) -> ollama.ChatResponse:
        messages = [
            {"role": "user", "content": prompt}
        ]
        if len(tool_calls) > 0:
            messages.extend(tool_calls)
            
        # print(json.dumps(messages, indent=4))

        response = ollama.chat(
            model=self.model_name, 
            messages=messages, 
            format=format,
            tools=tools
        )
        return response

    def chat(
            self, 
            prompt: str, 
            format: str = None, 
        ) -> str:
        response = self.chat_ollama(prompt, format=format, tools=self.tools)
        if response and "message" in response:
            message: ollama.Message = response["message"]
            if "tool_calls" in message:
                message_tool_calls: List[ollama.Message.ToolCall] = message.tool_calls
                tool_responses = [message.model_dump()]
                for tool in message_tool_calls:
                    print(f"{tool.function.name}...")
                    tool_function = self.tool_lookup[tool.function.name]
                    tool_arguments = tool.function.arguments
                    if isinstance(tool_arguments, str):
                        tool_response = tool_function(tool_arguments)
                    else:
                        tool_response = tool_function(**tool_arguments)
                    tool_responses.append({ "role": "tool", "content": str(tool_response), "name": tool.function.name})
                    
                final_tool_result = self.chat_ollama(
                    prompt, 
                    format=format, 
                    tool_calls=tool_responses
                )
                final_answer = final_tool_result.message.content
            else:
                final_answer = message.content
        else:
            return None
        
        if format == "json":
            try:
                return json.loads(final_answer)
            except:
                return final_answer
        else:
            return final_answer

    def generate(self, prompt, json_format=False):
        if self.provider == "ollama":
            response = self.generate_ollama(prompt, json_format=json_format)
        elif self.provider == "groq":
            response = self.generate_groq(prompt)
        else:
            response = self.generate_gemini(prompt)

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
        

def add_numbers(a: float, b: float) -> float:
    """Adds two numbers and return the result.
    
    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: The sum of the two numbers.
    """
    return a + b

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    tools = [
        get_wikipedia_article
    ]

    caller = LLMCaller(        
        tools=tools
    )

    # print(caller.chat("""What are the key componets of a microservice architecture? Use Wikipedia to research the topic.""", format=None))

    print(caller.generate("What are microservices?"))
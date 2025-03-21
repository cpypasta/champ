import os
from openai import OpenAI
from tools.research_tool import ResearchTool, Question, Context
from typing import List
from tqdm import tqdm

class PerplexityTool(ResearchTool):
    def __init__(self):
        self.api_key = os.environ["PERPLEXITY_API_KEY"]

    def search(self, query: str):
        client = OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
        try:
            response = client.chat.completions.create(
                model="sonar",
                messages=[
                    {"role": "user", "content": query}
                ],
                stream=False
            )
        except Exception as ex:
            print(ex)
            return None
        
        if response:
            content = response.choices[0].message.content
            return content
        return None

    def research(self, questions: List[Question]) -> List[Question]:    
        questions_updated = []
        for question in tqdm(questions, desc="researching perplexity", unit="question"):
            response = self.search(question.question)
            if response:
                context = Context("Perplexity", response)
                question_updated = question.add_context(context)
                questions_updated.append(question_updated)
        return questions_updated

def search_internet(query: str) -> str:
    """Search the internet to find the latest information about any topic.

    Args:
        query (str): The topic to search for.

    Returns:
        str: The latest information about the topic.    
    """
    return PerplexityTool().search(query)

if __name__ == "__main__":
    pass
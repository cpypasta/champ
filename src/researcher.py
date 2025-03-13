from llm_caller import LLMCaller
from tools.research_tool import Question
from tools.wiki import Wiki
from tools.perplexity import PerplexityTool
from enum import Enum
from typing import List

class Tool(Enum):
    WIKIPEDIA = "wikipedia"
    PERPLEXITY = "perplexity"

class Researcher:
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.tools = {
            "wikipedia": Wiki(),
            "perplexity": PerplexityTool()
        }

    def research(self, questions: List[Question], tools_to_use: List[Tool]) -> List[Question]:
        for tool in tools_to_use:
            questions = self.tools[tool.value].research(questions)

        return questions
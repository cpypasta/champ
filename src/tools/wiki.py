import wikipedia
from dataclasses import dataclass
from tools.research_tool import ResearchTool, Question, Context
from typing import List
from tqdm import tqdm

@dataclass
class WikiResponse:
    title: str
    content: str

class Wiki(ResearchTool):
    def search(self, query: str):
        try:
            results = wikipedia.search(query, results=1)
        except Exception as ex_search:
            print("search", ex_search)
            return None

        if len(results) > 0:
            result = results[0]
            try:
                page = wikipedia.page(result)
                return WikiResponse(page.title, page.summary)
            except Exception as page_ex:
                print("page", page_ex)
                return None
        else:
            return None

    def research(self, questions: List[str]) -> List[str]:
        answers = []
        for question in questions:
            response = self.search(question)
            if response:
                answers.append(response.content)
        return answers


    # def research(self, questions: List[Question]) -> List[Question]:
    #     questions_updated = []
    #     for question in tqdm(questions, desc="researching wikipedia", unit="title"):
    #         response = self.search(question.title)
    #         if response:
    #             context = Context(f"Wikipedia ({response.title})", response.content)
    #             question_updated = question.add_context(context)
    #             questions_updated.append(question_updated)
    #     return questions_updated


if __name__ == "__main__":
    query = "Goal-Setting Theory"

    results = wikipedia.search(query, results=2)
    page = wikipedia.page(results[0])
    print(page.content)

    # results = wikipedia.search("Python") # search for articles (keyword based)
    # page = wikipedia.page(results[0]) # load page details including content
    # print(page.url, len(page.links))

    # print(wikipedia.summary("what is Python?")) # for quick summaries (it is what is at the top of an article page)
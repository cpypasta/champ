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
                page = wikipedia.page(title=result, auto_suggest=False)
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
                answers.append(f"{response.title}:\n\n{response.content}")
        return answers


def get_wikipedia_article(query: str) -> str:
    """Search for an article on Wikipedia.

    The query should be formatted appropriately for Wikipedia articles. So instead of a long question, focus on what topics will likely be found as a Wikipedia article. Therefore, the `query` should look like an article title.

    Args:
        query (str): A query to find articles on Wikipedia.

    Returns:
        str: Wikipedia article text.
    """        
    wiki = Wiki()
    answers = wiki.research([query])
    return answers[0]


if __name__ == "__main__":
    query = "Microservices architecture"

    results = wikipedia.search(query)
    page_title = results[0]
    print(page_title)
    print(wikipedia.page(title=page_title, auto_suggest=False))

    # results = wikipedia.search("Python") # search for articles (keyword based)
    # page = wikipedia.page(results[0]) # load page details including content
    # print(page.url, len(page.links))

    # print(wikipedia.summary("what is Python?")) # for quick summaries (it is what is at the top of an article page)
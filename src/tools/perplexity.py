import os, re
from openai import OpenAI
from typing import List, Dict, Tuple
from tools.article import ResearchArticle, ArticleCitation
from tools.llm_caller import LLMCaller

class PerplexityTool():
    def __init__(self, llm_caller: LLMCaller):
        self.llm = llm_caller
        self.article = ResearchArticle(llm_caller)
        self.api_key = os.environ["PERPLEXITY_API_KEY"]

    def _replace_inline_references(self, content: str, citations: List[ArticleCitation]) -> Tuple[str,List[ArticleCitation]]:
        single_inline_reference_pattern = r"\[(\d+)\]"      
        all_inline_reference_pattern = r"\[\d+\](?:\s*\[\d+\])*"
        matches = re.finditer(all_inline_reference_pattern, content)
        citations_used = {}
        for match in sorted(matches, key=lambda x: x.start(), reverse=True):
            reference = match.group(0)
            inline_citation_ids = re.findall(single_inline_reference_pattern, reference)
            inline_citation_ids = [int(num) for num in inline_citation_ids]

            inline_citations = [
                citations[num-1]
                for num in inline_citation_ids
                if num <= len(citations)
            ]

            if inline_citations:
                for citation in inline_citations:
                    citations_used[citation.url] = citation
                inline_citations = [citation.inline() for citation in inline_citations]
                inline_citations = sorted(inline_citations)
                combined_citation = f" ({'; '.join(inline_citations)})"
                content = content[:match.start()] + combined_citation + content[match.end():]      

        return content, citations_used.values()

    def search(self, query: str, update_citations: bool = True) -> Dict:
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
            urls: List[str] = response.citations if hasattr(response, "citations") else []
            content = response.choices[0].message.content

            if update_citations:
                citations: List[ArticleCitation] = [self.article.cite(url) for url in urls]
                content, citations = self._replace_inline_references(content, citations)
            else:
                citations = urls

            return {
                "content": content,
                "citations": citations
            }
        return None

def search_internet(query: str) -> str:
    """Search the internet to find the latest information about any topic.

    Args:
        query (str): The topic to search for.

    Returns:
        str: The latest information about the topic.    
    """
    return PerplexityTool().search(query)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    llm = LLMCaller()
    perp = PerplexityTool(llm)
    response = perp.search("""Provide a high-level overview of the following topic:

# "Goal-Setting Theory"

# Please format the response in a way this concise, clear, and easily readable. Include only the important information only.""")
    
    from rich import print as rprint
    from rich.markdown import Markdown
    rprint(Markdown(response["content"]))

    print()
    for c in response["citations"]:
        print(c.reference())

    with open("debug.md", "w") as f:
        f.write(response["content"])

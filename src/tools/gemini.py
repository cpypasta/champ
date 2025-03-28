import requests
from typing import Dict
from tools.article import ResearchArticle, ArticleCitation
from tools.llm_caller import LLMCaller
from google.genai.types import GroundingMetadata, GroundingChunk

class Gemini:
    def __init__(self):
        self.llm = LLMCaller(
            provider="gemini",
            model_name="gemini-2.0-flash"
        )

    def _follow_url(self, url: str) -> str:
        response = requests.head(url, allow_redirects=True)
        return response.url

    def  search(self, query: str, update_citations: bool = True) -> Dict:
        response = self.llm.generate_gemini(query, search=True)
        content: str = response.get("content")
        grounding = response.get("grounding")

        article_llm = LLMCaller(provider="gemini")
        article = ResearchArticle(article_llm)
        citations = []
        
        for query in grounding:            
            grounding: GroundingMetadata = query.grounding_metadata
            if grounding:
                supports = grounding.grounding_supports or []              
                chunk_indices = set()                    
                inline_groundings = []                    

                for support in supports:
                    grounding_chunk_indices = support.grounding_chunk_indices                        
                    chunk_indices.update(grounding_chunk_indices)          
                    if update_citations:                                      
                        inline_groundings.append((support.segment.end_index, grounding_chunk_indices))                     
                    else:
                        inline_groundings = []

                citation_index = {}
                for chunk_index in chunk_indices:
                    chunk: GroundingChunk = grounding.grounding_chunks[chunk_index]
                    uri = chunk.web.uri
                    url = self._follow_url(uri)
                    if update_citations:
                        citation = article.cite(url)                    
                    else:
                        citation = ArticleCitation(url)
                    citation_index[chunk_index] = citation                    
                    citations.append(citation)

                for end_index, chunk_indices in sorted(inline_groundings, key=lambda x: x[0], reverse=True):
                    end_index = end_index - 1
                    inline_citations = [citation_index[chunk_index] for chunk_index in chunk_indices]
                    inline_citations = [citation.inline() for citation in inline_citations]
                    inline_citations = f" ({'; '.join(inline_citations)})"
                    content = content[:end_index] + str(inline_citations) + content[end_index:]                       

        return {
            "content": content,
            "citations": citations
        }

if __name__ == "__main__":
    import config.prompts as prompts
    from dotenv import load_dotenv
    from rich import print as rprint
    from rich.markdown import Markdown
    load_dotenv()

    # with open("candidates.md", "r") as f:
    #     prompt = f.read()

    prompt = "What is Zinc?"

    gemini = Gemini()
    response = gemini.search(prompt, update_citations=True)
    rprint(Markdown(response.get("content")))
    print(response["citations"])

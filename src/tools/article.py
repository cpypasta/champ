import config.prompts as prompts, re, json
from tools.llm_caller import LLMCaller
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List
from citeproc import CitationStylesStyle, CitationStylesBibliography, Citation, CitationItem
from citeproc.source.json import CiteProcJSON
from nameparser import HumanName
from rich import print as rprint
from rich.markdown import Markdown
from newspaper import Article
from datetime import datetime
from tools.play import fetch
from tools.doi import DOI

@dataclass
class ArticleCitation:
    url: str
    authors: List[str] = field(default_factory=list)
    published_date: datetime = None
    title: str = None
    domain: str = None
    journal: str = None
    doi: str = None
    source: str = None

    def reference(self):        
        if self.authors:
            authors = [HumanName(author) for author in self.authors]
            authors = [{"family": author.last, "given": author.first} for author in authors]
        else:
            authors = []

        if self.published_date:        
            date_parts = str(self.published_date).split("-")
            date_parts = [int(part) for part in date_parts]
            published = {"date-parts": [date_parts]}
        else:
            published = None

        csl_data = {
            "id": "source1",
            "type": "webpage" if self.domain else "article-journal",
            "URL": self.url
        }
        if published:
            csl_data["issued"] = published   
        if authors:
            csl_data["author"] = authors         
        if self.title:
            csl_data["title"] = self.title
        if self.journal:
            csl_data["container-title"] = self.journal
        if self.domain:
            csl_data["container-title"] = self.domain
        if self.doi:
            csl_data["DOI"] = self.doi

        # print(json.dumps(csl_data, indent=4))

        style = CitationStylesStyle("./config/apa-6th-edition.csl", validate=False)        
        source = CiteProcJSON([csl_data])
        biblio = CitationStylesBibliography(style, source)
        citation = Citation([CitationItem("source1")])
        biblio.register(citation)
        return str(biblio.bibliography()[0]).replace("&amp;", "&").replace("<i>", "_").replace("</i>", "_")

    def inline(self):
        def get_author_name(author: HumanName) -> str:
            first = f"{author.first[0]}." if author.first else ""
            middle = f"{author.middle[0]}." if author.middle else ""
            last = author.last
            if first and middle and last:
                return f"{last}, {first}{middle}"
            elif first and last:
                return f"{last}, {first}"
            else:
                return f"{last}"
            

        if self.authors:
            authors = [HumanName(author) for author in self.authors]
            if len(authors) > 2:
                authors = f"{get_author_name(authors[0])} et al."
            elif len(authors) == 2:
                authors = f"{get_author_name(authors[0])} & {get_author_name(authors[1])}"
            else:
                authors = get_author_name(authors[0])
        elif self.domain:
            authors = self.domain
        elif self.title:
            authors = f"_{self.title}_"
        else:
            authors = self.url
            
        
        if self.published_date:
            year = str(self.published_date).split("-")[0]
        else:
            year = "n.d."

        return f"{authors}, {year}"


class ResearchArticle:
    def __init__(self, llm_caller: LLMCaller):
        self.llm = llm_caller

    def _find_doi(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        meta_tags = soup.find_all("meta")
        
        meta_dict = {}
        for tag in meta_tags:
            if tag.get("scheme"):
                if tag.get("scheme") == "doi":
                    return tag.get("content")
            meta_dict[tag.get("name")] = tag.get("content")

        for name, content in meta_dict.items():
            if name and "doi" in name.lower():
                return content

        return None

    def cite(self, url: str) -> ArticleCitation:
        domain_match = re.match(r"https?\:\/\/w{0,3}\.?(.+)\.(?:org|com|edu|ai|io|net|gov|ca)", url) 
        if domain_match:
            domain = domain_match.group(1)
            domain = domain.split(".")[-1].capitalize()
        else:
            domain = None

        if url.endswith(".pdf"):
            return ArticleCitation(url, domain=domain)
        
        try:
            html = fetch(url)
            article = Article(url)
            article.download(input_html=html)
            article.parse()
        except Exception as ex:
            return ArticleCitation(url, domain=domain)

        doi = self._find_doi(article.html)
        if doi:
            bib = DOI().cite(doi)
            return ArticleCitation(
                url, 
                bib.get("authors"), 
                bib.get("published_date"), 
                bib.get("title"), 
                journal=bib.get("journal"),
                doi=doi,
                source=bib.get("source")
            )

        if article.publish_date:
            publish_date = article.publish_date.year
        else:
            publish_date = None

        if article.authors:
            authors = article.authors
            valid_authors_prompt = prompts.valid_authors(authors)
            valid_authors = self.llm.generate(valid_authors_prompt)
            valid_authors = re.findall("NAME:\s(.+)", valid_authors)
            valid_authors = [author.strip() for author in valid_authors if author in authors]
        else:
            valid_authors = []
        
        if article.title:
            if "." in article.title:
                title = None
            else:
                title = article.title
        else:
            title = None 
        
        return ArticleCitation(url, valid_authors, publish_date, title, domain=domain, source="newspaper")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # url = "https://www.betterup.com/blog/smart-goals-examples"    
    # url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10539547/"
    # url = "https://www.sciencedirect.com/science/article/pii/S0010854521006767"
    url = "https://www.neurology.org/doi/10.1212/WNL.0000000000207912"

    llm = LLMCaller(provider="gemini")
    article = ResearchArticle(llm)
    citation = article.cite(url)
    print(citation)
    print(citation.inline())
    print(citation.reference())
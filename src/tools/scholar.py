import requests, json
from play import fetch
from bs4 import BeautifulSoup
from semanticscholar import SemanticScholar

api_url = "https://api.semanticscholar.org/graph/v1"
page_url = "https://www.semanticscholar.org"


# https://api.semanticscholar.org/api-docs/graph
# https://github.com/danielnsilva/semanticscholar/tree/master

def get_paper2(id: str):
    response = fetch(f"{page_url}/paper/{id}")
    soup = BeautifulSoup(response, "html.parser")
    title = soup.find("h1", { "data-test-id": "paper-detail-title"})
    if title:
        title = title.text
    else:
        print("no title")
        print(response)
        return
    year = soup.find("span", { "data-test-id": "paper-year"}).text.strip()
    year = year.split()[-1]
    print(title, year)

def get_paper(id: str):
    params = {
        "fields": "title,year,abstract,citationCount,venue"
    }
    response = requests.get(f"{api_url}/paper/{id}", params=params)
    if response.ok:
        results = response.json()
        print(json.dumps(results, indent=4))
    else:
        print(response.status_code)  
        get_paper2(id)


def search(query: str):
    params = {
        "query": query,
        "fields": "title,year,venue",
        "publicationTypes": "JournalArticle,MetaAnalysis,Review",
        "openAccessPdf": "",
        "minCitationCount": "10",
        "publicahDateOrYear": "2020:",
        "limit": "10",
    }
    response = requests.get(f"{api_url}/paper/search", params=params)
    if response.ok:
        results = response.json()
        print(json.dumps(results, indent=4))
    else:
        print(response.text)


if __name__ == "__main__":
    # search("scrum agile")
    # get_paper("84c8c874633fbb0aa1e48276fb31b1869d9b6766")
    # get_paper("84c8c874633fbb0aa1e48276fb31b1869d9b6766")

    paper = SemanticScholar().get_paper("84c8c874633fbb0aa1e48276fb31b1869d9b6766")
    print(paper.title)
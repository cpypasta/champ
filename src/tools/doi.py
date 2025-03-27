import pyalex, re
from habanero import Crossref
from scholarly import scholarly
from typing import Dict

class DOI:
    def _remove_special_charc(self, value: str) -> str:
        new_value = re.sub(r"[^\w\s\-,\:]", "", value)
        return new_value.strip()

    def _crossref(self, doi: str) -> Dict:
        cr = Crossref()
        try:
            # try to find paper using Crossref first
            result = cr.works(ids=doi)
            if "message" in result:
                data: Dict = result["message"]
            else:
                return None
        except Exception as ex:
            return None

        cr = Crossref()
        result = cr.works(ids=doi)
        title = data.get("title")[0] if "title" in data else None

        authors = []
        if 'author' in data:
            for author in data['author']:
                if 'given' in author and 'family' in author:
                    authors.append(f"{author['given'].capitalize()} {author['family'].capitalize()}")
                elif 'family' in author:
                    authors.append(author['family'].capitalize())     

        published_date = None
        if 'published-print' in data and 'date-parts' in data['published-print']:
            published_date = '-'.join([str(x) for x in data['published-print']['date-parts'][0]])
        elif 'published-online' in data and 'date-parts' in data['published-online']:
            published_date = '-'.join([str(x) for x in data['published-online']['date-parts'][0]])                       

        journal = data.get('container-title', [''])[0] if data.get('container-title') else ''

        return {
            "title": title,
            "authors": authors,
            "published_date": published_date,
            "journal": journal,
            "source": "Crossref"
        }        

    def _openalex(self, doi: str) -> Dict:
        pyalex.config.email = "app.maestro@gmail.com"
        doi_work = f"https://doi.org/{doi}"
        try:
            work: Dict = pyalex.Works()[doi_work]
        except Exception as ex:
            return None
        
        title = work.get("title")
        authors = [author.get("author").get('display_name', '') for author in work.get('authorships', [])]
        publication_date = work.get("publication_date")
        journal = work.get('host_venue', {}).get('display_name')
        return {
            "title": title.replace(".", ""),
            "authors": authors,
            "published_date": publication_date,
            "journal": journal,
            "source": "OpenAlex"
        }
        
    def _googlescholar(self, doi: str) -> Dict:
        def format_author_name(author_name: str) -> str:
            parts = author_name.split()
            
            if len(parts) == 2 and len(parts[0]) > 1 and parts[0].isupper():
                initials = ' '.join(parts[0])
                return f"{initials} {parts[1]}"
            
            return author_name

        query = scholarly.search_pubs(doi)
        try:
            pub = next(query)
        except Exception as ex:
            return None
        bib = pub.get("bib", {})
        title = bib.get("title")
        authors = bib.get("author")
        published_date = bib.get("pub_year")
        journal = bib.get("venue")
        return {
            "title": title,
            "authors": [format_author_name(author) for author in authors],
            "published_date": published_date,
            "journal": self._remove_special_charc(journal),
            "source": "Google Scholar"
        }

    def cite(self, doi: str) -> Dict:
        crossref = self._crossref(doi)
        if crossref:
            return crossref
        else:
            openalex = self._openalex(doi)
            if openalex:
                return openalex
            else:
                googlescholar = self._googlescholar(doi)
                return googlescholar

        

if __name__ == "__main__":
    # doi = "10.17179/excli2023-6335"
    # doi = "10.1111/j.1749-6632.1991.tb37894.x"
    doi = "j.ccr.2021.214402"

    print(DOI().cite(doi))
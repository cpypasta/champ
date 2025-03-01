import os, requests, json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OACORE_API_KEY")
api_url = "https://api.core.ac.uk/v3"

def search_works(query: str):
    headers = {"Authorization": f"Bearer {api_key}"}
    query = {
        "q": query,
        "limit": 10
    }

    try:
        url = f"{api_url}/search/works"
        response = requests.post(url, data=json.dumps(query), headers=headers)
        if response.ok:
            results = response.json()["results"]
            keys = results[0].keys()
            for k in keys:
                print(k)
            return results
        else:
            return None
    except Exception as ex:
        print(ex)
        return None
    
""" Result Keys
https://api.core.ac.uk/docs/v3#tag/Outputs/operation/get_outputs_by_identifier

acceptedDate
arxivId
authors
citationCount
contributors
outputs
createdDate
dataProviders
depositedDate
abstract
documentType
doi
downloadUrl
fieldOfStudy
fullText
id
identifiers
title
language
magId
oaiIds
publishedDate
publisher
pubmedId
references
sourceFulltextUrls
updatedDate
yearPublished
journals
links
"""

if __name__ == "__main__":
    # https://api.core.ac.uk/docs/v3#section/How-to-search
    search_works("covid AND yearPublished>=2010 AND yearPublished<=2021")
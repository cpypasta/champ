import arxiv, json

# https://info.arxiv.org/help/api/user-manual.html#query_details

def search(query: str):
    client = arxiv.Client()
    search = arxiv.Search(
        query = query,
        max_results = 2,
        sort_by = arxiv.SortCriterion.Relevance
    )
    results = client.results(search)
    for r in results:
        print("\n".join([r.entry_id, r.title, str(r.published), str(len(r.summary)), r.journal_ref]))
        print()

if __name__ == "__main__":
    search("Relationships between Agile Work Practices and Occupational Well-Being")
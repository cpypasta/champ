import wikipedia

if __name__ == "__main__":
    results = wikipedia.search("Python") # search for articles (keyword based)
    page = wikipedia.page(results[0]) # load page details including content
    print(page.url, len(page.links))

    print(wikipedia.summary("what is Python?")) # for quick summaries (it is what is at the top of an article page)
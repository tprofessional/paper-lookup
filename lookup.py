import requests
import re

#---- One-time use functions ----
'''
    Get title from formatted line in index.html.
'''
def get_title(line):
    match = re.search(r"'([^']+)'", line)
    if match:
        return match.group(1)
    else:
        return None

'''
    Helper to get the correct DOI from title.
'''
def search_doi(title):
    url = "https://api.crossref.org/works"
    params = {
        "query.title": title,
        "rows": 5
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    works = r.json()["message"]["items"]

    if not works:
        print("No results.")
        return

    paper = works[0]

    doi = paper.get("DOI", "")
    volume = paper.get("volume", "")
    issue = paper.get("issue", "")
    pages = paper.get("page", "")

    # print("Title:", title)
    # print("DOI:", doi)
    # print("URL:", f"https://doi.org/{doi}" if doi else "")
    # print("Volume:", volume)
    # print("Issue:", issue)
    # print("Pages:", pages)
    # print("\n")
    return doi, volume, issue, pages

#---- Main functions ----
'''
    Return title, vol, issue, pgs from doi.
'''
def get_metadata(doi):

    return title, volume, issue, pages

def fill_fields(line, doi, volume, issue, pages):
    url = f"https://doi.org/{doi}" if doi else ""

    line = re.sub(r"\[volume:[^\]]*\]", f"[volume:{volume}]", line)
    line = re.sub(r"\[issue:[^\]]*\]", f"[issue:{issue}]", line)
    line = re.sub(r"\[pages:[^\]]*\]", f"[pages:{pages}]", line)
    line = re.sub(r"\[doi:[^\]]*\]", f"[doi:{doi}]", line)
    line = re.sub(r"\[url:[^\]]*\]", f"[url:{url}]", line)

    return line

def main():
    with open("papers.txt", "r") as f:
        lines = f.readlines()
    
    print(lines[0])
    for line in lines:
        title = get_title(line)

        if title:
            lookup(title)

if __name__ == "__main__":
    main()
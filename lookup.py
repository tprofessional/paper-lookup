import requests
import re

#---- One-time use for AGI lab website ----

TYPE_MAP = {
    "journal": ["journal-article"],
    "conference": ["proceedings-article", "journal-article"],
    "preprint": ["posted-content"],
}

def get_title(line):
    """
    Get title from formatted line in index.html.

    Args:
        line (str): Line in format from index.html
    
    Return:
        str or None: Title string or None if not found
    """
    match = re.search(r"'([^']+)'", line)
    if match:
        return match.group(1)
    else:
        return None

def search_doi(title, pub_type):
    """
    Helper to get the correct DOI from title.

    Args:
        title (str): Title of the paper
        pub_type (str): Type of publication ('journal', 'conference', 'preprint')

    Return:
        str or None: DOI string or None if not found
    """
    allowed_types = TYPE_MAP[pub_type]

    url = "https://api.crossref.org/works"
    params = {
        "query.title": title,
        "rows": 10
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    works = r.json()["message"]["items"]

    def normalize(s):
        return " ".join(s.lower().split())

    for paper in works:
        if not paper.get("title"):
            continue

        if normalize(paper["title"][0]) != normalize(title):
            continue

        if paper.get("type") not in allowed_types:
            continue

        doi = paper.get("DOI")
        if doi:
            return doi

    return None

#---- Main functions ----
'''
    Return title, volume, issue, pages from doi.
'''
def get_metadata(doi):
    url = f"https://api.crossref.org/works/{doi}"

    r = requests.get(url)
    r.raise_for_status()

    paper = r.json()["message"]

    metadata = {
        "title": paper.get("title", [""])[0],
        "volume": paper.get("volume", ""),
        "issue": paper.get("issue", ""),
        "pages": paper.get("page", ""),
        "doi": doi,
        "url": f"https://doi.org/{doi}",
    }

    return metadata

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
    
    # print(lines[0])
    for line in lines:
        title = get_title(line)

        if title:
            metadata = get_metadata(title)
        


if __name__ == "__main__":
    main()
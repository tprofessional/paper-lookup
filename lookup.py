import requests
import re
import argparse

#---- One-time use for AGI lab website ----

TYPE_MAP = {
    "j": ["journal-article"],
    "c": ["proceedings-article", "journal-article"],
    "p": ["posted-content"],
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

def _metadata_from_paper(paper, doi=None):
    """Build metadata dict from a Crossref work item."""
    doi = doi or paper.get("DOI", "")
    return {
        "title": paper.get("title", [""])[0],
        "volume": paper.get("volume", ""),
        "issue": paper.get("issue", ""),
        "pages": paper.get("page", ""),
        "doi": doi,
        "url": f"https://doi.org/{doi}" if doi else "",
    }

def search_paper(title, pub_type):
    """
    Look up a paper by title and return its metadata from the search hit.

    Args:
        title (str): Title of the paper
        pub_type (str): Type of publication ('j', 'c', 'p')

    Return:
        dict or None: Metadata dict or None if not found
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
            return _metadata_from_paper(paper, doi)

    return None

#---- Main functions ----
def get_metadata(doi):
    """Return title, volume, issue, pages from doi."""
    url = f"https://api.crossref.org/works/{doi}"

    r = requests.get(url)
    r.raise_for_status()

    return _metadata_from_paper(r.json()["message"], doi)

def fill_fields(line, doi, volume, issue, pages):
    url = f"https://doi.org/{doi}" if doi else ""

    line = re.sub(r"\[volume:[^\]]*\]", f"[volume:{volume}]", line)
    line = re.sub(r"\[issue:[^\]]*\]", f"[issue:{issue}]", line)
    line = re.sub(r"\[pages:[^\]]*\]", f"[pages:{pages}]", line)
    line = re.sub(r"\[doi:[^\]]*\]", f"[doi:{doi}]", line)
    line = re.sub(r"\[url:[^\]]*\]", f"[url:{url}]", line)

    return line

def process_from_input(input_file, pub_type):
    """Look up DOIs from titles in formatted publication entries."""
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    completed = []
    successes = 0
    total = 0

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        total += 1

        title = get_title(line)

        if title is None:
            print(f"[FAIL] Could not extract title:\n{line.strip()}")
            completed.append(line)
            continue

        metadata = search_paper(title, pub_type)

        if metadata is None:
            print(f"[FAIL] {title}")
            # for out format consistency on fail
            completed.append(line.rstrip() + "\n\n")
            continue

        line = fill_fields(
            line,
            metadata["doi"],
            metadata["volume"],
            metadata["issue"],
            metadata["pages"],
        )

        completed.append(line.rstrip() + "\n\n")
        successes += 1

        print(f"[ OK ] {title}")

    return completed, successes, total

def process_from_dois(doi_file):
    """Fetch metadata for each DOI in a file (one DOI per line)."""
    with open(doi_file, "r", encoding="utf-8") as f:
        dois = [line.strip() for line in f if line.strip()]

    completed = []
    successes = 0
    total = 0

    for doi in dois:
        total += 1

        metadata = get_metadata(doi)
        title = metadata["title"] or doi

        # Minimal template so fill_fields can populate the known slots
        line = "[volume:][issue:][pages:][doi:][url:]"
        line = fill_fields(
            line,
            metadata["doi"],
            metadata["volume"],
            metadata["issue"],
            metadata["pages"],
        )

        completed.append(line.rstrip() + "\n\n")
        successes += 1

        print(f"[ OK ] {title}")

    return completed, successes, total

def main():
    parser = argparse.ArgumentParser(
        description="Fill publication metadata using Crossref."
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-d",
        help=".txt file containing DOIs of each publication."
    )
    mode.add_argument(
        "-i",
        help=".txt file containing publication entries formatted as [authors][yr][title]...[vol][iss][pgs]."
    )

    parser.add_argument(
        "-p",
        "--pub-type",
        required=False,
        # journal, conference, preprint
        choices=["j", "c", "p"],
        help="Publication type (required with -i)."
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file."
    )

    args = parser.parse_args()

    if args.i and not args.pub_type:
        parser.error("-p/--pub-type is required when using -i")

    if args.i:
        completed, successes, total = process_from_input(args.i, args.pub_type)
    else:
        completed, successes, total = process_from_dois(args.d)

    with open(args.output, "w", encoding="utf-8") as f:
        f.writelines(completed)

    print(f"\nRetrieved metadata for {successes}/{total} papers.")

if __name__ == "__main__":
    main()

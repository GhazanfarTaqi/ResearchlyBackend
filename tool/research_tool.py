from langchain.tools import tool
import os
from rich import print
import requests
from dotenv import load_dotenv

load_dotenv()


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort(key=lambda x: x[0])

    return " ".join(
        word for _, word in words
    )

@tool
def get_research_data(query:str) -> list:
    """Search academic papers about a topic. Return titles, abstracts, authors, publication years, citation counts, and source URLs."""

    params = {
        "api_key": os.getenv("OPENALEX_API_KEY"),
        "search": query,
        "per_page": 5,
        "sort": "relevance_score:desc"
    }

    results = requests.get(
        "https://api.openalex.org/works",
        params=params
    ).json()

    papers = []

    for work in results["results"]:

        papers.append({
            "title": work["display_name"],
            "year": work.get("publication_year"),
            "citations": work.get("cited_by_count"),
            "doi": work.get("doi"),
            "url": work.get("primary_location", {})
                         .get("landing_page_url"),
            "abstract": reconstruct_abstract(
                work.get("abstract_inverted_index")
            )
        })

    return papers
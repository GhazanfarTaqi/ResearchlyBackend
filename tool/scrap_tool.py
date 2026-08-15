# import os
# import re
# import requests
# from urllib.parse import quote
# from rich import print


# def fetch_paper(doi: str, output_dir: str = "./papers", email: str = "your-email@example.com") -> dict:
#     """
#     Given a DOI, fetch metadata (via Crossref) and download a legal open-access
#     PDF if one exists (via Unpaywall, falling back to arXiv by title search).

#     Returns a dict with metadata, and pdf/local_path info if a copy was found.
#     Never bypasses paywalls — if no open-access copy exists, returns metadata
#     and the publisher URL only.
#     """
#     doi = doi.strip()
#     doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
#     doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)

#     result = {
#         "doi": doi,
#         "found": False,
#         "title": None,
#         "authors": [],
#         "journal": None,
#         "year": None,
#         "publisher_url": None,
#         "open_access": False,
#         "pdf_url": None,
#         "local_path": None,
#         "source": None,
#         "message": "",
#     }

#     # 1. Metadata via Crossref
#     try:
#         resp = requests.get(
#             f"https://api.crossref.org/works/{quote(doi)}",
#             headers={"User-Agent": f"paper-fetcher/1.0 (mailto:{email})"},
#             timeout=15,
#         )
#         resp.raise_for_status()
#         msg = resp.json()["message"]
#     except requests.RequestException as e:
#         result["message"] = f"Could not resolve DOI via Crossref: {e}"
#         return result

#     authors = []
#     for a in msg.get("author", []):
#         name = " ".join(filter(None, [a.get("given"), a.get("family")]))
#         if name:
#             authors.append(name)

#     title = msg.get("title", [None])[0]
#     year = None
#     for date_field in ("published-print", "published-online", "issued"):
#         parts = msg.get(date_field, {}).get("date-parts", [[None]])
#         if parts and parts[0][0]:
#             year = parts[0][0]
#             break

#     result["found"] = True
#     result["title"] = title
#     result["authors"] = authors
#     result["journal"] = msg.get("container-title", [None])[0]
#     result["year"] = year
#     result["publisher_url"] = msg.get("URL")

#     # 2. Open-access PDF via Unpaywall
#     pdf_url, source = None, None
#     try:
#         resp = requests.get(
#             f"https://api.unpaywall.org/v2/{quote(doi)}",
#             params={"email": email},
#             timeout=15,
#         )
#         if resp.status_code == 200:
#             data = resp.json()
#             best = data.get("best_oa_location") or {}
#             pdf_url = best.get("url_for_pdf") or best.get("url")
#             if not pdf_url:
#                 for loc in data.get("oa_locations", []) or []:
#                     pdf_url = loc.get("url_for_pdf") or loc.get("url")
#                     if pdf_url:
#                         break
#             if pdf_url:
#                 source = "unpaywall"
#     except requests.RequestException:
#         pass

#     # 3. Fallback: search arXiv by title
#     if not pdf_url and title:
#         try:
#             resp = requests.get(
#                 "http://export.arxiv.org/api/query",
#                 params={"search_query": f'ti:"{title}"', "start": 0, "max_results": 1},
#                 timeout=15,
#             )
#             if resp.status_code == 200:
#                 match = re.search(r'<link title="pdf" href="([^"]+)"', resp.text) or \
#                         re.search(r"(https?://arxiv\.org/pdf/[^\s\"<]+)", resp.text)
#                 if match:
#                     pdf_url = match.group(1)
#                     source = "arxiv"
#         except requests.RequestException:
#             pass

#     # 4. Download if found
#     if pdf_url:
#         try:
#             os.makedirs(output_dir, exist_ok=True)
#             dest_path = os.path.join(output_dir, re.sub(r"[^\w\-]+", "_", doi) + ".pdf")
#             resp = requests.get(pdf_url, headers={"Accept": "application/pdf"}, timeout=30, stream=True)
#             resp.raise_for_status()
#             with open(dest_path, "wb") as f:
#                 for chunk in resp.iter_content(chunk_size=8192):
#                     f.write(chunk)
#             result["open_access"] = True
#             result["pdf_url"] = pdf_url
#             result["local_path"] = dest_path
#             result["source"] = source
#             result["message"] = f"Downloaded via {source}."
#         except requests.RequestException:
#             result["pdf_url"] = pdf_url
#             result["source"] = source
#             result["message"] = f"Found a PDF link via {source} but download failed. URL returned instead."
#     else:
#         result["message"] = (
#             "No open-access copy found via Unpaywall or arXiv. "
#             "Returning metadata and publisher link only — this paper may be paywalled."
#         )

#     return result

# if __name__ == "__main__":
#     papers = ["https://doi.org/10.1038/s41746-023-00873-0", "https://doi.org/10.1109/access.2022.3197671", "https://doi.org/10.1038/s41746-019-0155-4","https://doi.org/10.1186/s13012-024-01357-9", "https://doi.org/10.3390/app14020675"]
#     email = "ghazanfartaqi2@gmail.com"
#     for paper in papers:
#         print(fetch_paper(paper, "./paper", email))
    
import re
import requests
from pathlib import Path
from urllib.parse import quote


def fetch_paper(doi: str, output_dir: str = "./papers", email: str = "your-email@example.com") -> dict:
    """
    Given a DOI, fetch metadata (via Crossref) and download a legal open-access
    PDF if one exists (via Unpaywall, falling back to arXiv by title search).

    Returns a dict with metadata, and pdf/local_path info if a copy was found.
    Never bypasses paywalls — if no open-access copy exists, returns metadata
    and the publisher URL only.
    """
    if not doi or not str(doi).strip():
        return {
            "doi": doi,
            "found": False,
            "title": None,
            "authors": [],
            "journal": None,
            "year": None,
            "publisher_url": None,
            "open_access": False,
            "pdf_url": None,
            "local_path": None,
            "source": None,
            "message": "No DOI provided.",
        }

    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)

    result = {
        "doi": doi,
        "found": False,
        "title": None,
        "authors": [],
        "journal": None,
        "year": None,
        "publisher_url": None,
        "open_access": False,
        "pdf_url": None,
        "local_path": None,
        "source": None,
        "message": "",
    }

    # 1. Metadata via Crossref
    try:
        resp = requests.get(
            f"https://api.crossref.org/works/{quote(doi)}",
            headers={"User-Agent": f"paper-fetcher/1.0 (mailto:{email})"},
            timeout=15,
        )
        resp.raise_for_status()
        msg = resp.json()["message"]
    except requests.RequestException as e:
        result["message"] = f"Could not resolve DOI via Crossref: {e}"
        return result

    authors = []
    for a in msg.get("author", []):
        name = " ".join(filter(None, [a.get("given"), a.get("family")]))
        if name:
            authors.append(name)

    title_list = msg.get("title") or [None]
    title = title_list[0]
    year = None
    for date_field in ("published-print", "published-online", "issued"):
        parts = msg.get(date_field, {}).get("date-parts", [[None]])
        if parts and parts[0]:
            year = parts[0][0]
            break

    journal_list = msg.get("container-title") or [None]

    result["found"] = True
    result["title"] = title
    result["authors"] = authors
    result["journal"] = journal_list[0]
    result["year"] = year
    result["publisher_url"] = msg.get("URL")

    # 2. Open-access PDF via Unpaywall
    pdf_url, source = None, None
    try:
        resp = requests.get(
            f"https://api.unpaywall.org/v2/{quote(doi)}",
            params={"email": email},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            best = data.get("best_oa_location") or {}
            pdf_url = best.get("url_for_pdf") or best.get("url")
            if not pdf_url:
                for loc in data.get("oa_locations", []) or []:
                    pdf_url = loc.get("url_for_pdf") or loc.get("url")
                    if pdf_url:
                        break
            if pdf_url:
                source = "unpaywall"
    except requests.RequestException:
        pass

    # 3. Fallback: search arXiv by title
    if not pdf_url and title:
        try:
            resp = requests.get(
                "http://export.arxiv.org/api/query",
                params={"search_query": f'ti:"{title}"', "start": 0, "max_results": 1},
                timeout=15,
            )
            if resp.status_code == 200:
                match = re.search(r'<link title="pdf" href="([^"]+)"', resp.text) or \
                        re.search(r"(https?://arxiv\.org/pdf/[^\s\"<]+)", resp.text)
                if match:
                    pdf_url = match.group(1)
                    source = "arxiv"
        except requests.RequestException:
            pass

    # 4. Download if found
    if pdf_url:
        try:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            dest_path = out_dir / (re.sub(r"[^\w\-]+", "_", doi) + ".pdf")
            resp = requests.get(pdf_url, headers={"Accept": "application/pdf"}, timeout=30, stream=True)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            result["open_access"] = True
            result["pdf_url"] = pdf_url
            result["local_path"] = str(dest_path)
            result["source"] = source
            result["message"] = f"Downloaded via {source}."
        except requests.RequestException:
            result["pdf_url"] = pdf_url
            result["source"] = source
            result["message"] = f"Found a PDF link via {source} but download failed. URL returned instead."
    else:
        result["message"] = (
            "No open-access copy found via Unpaywall or arXiv. "
            "Returning metadata and publisher link only — this paper may be paywalled."
        )

    return result
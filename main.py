from fastmcp import FastMCP
import feedparser
import requests
import re
import urllib.parse
import tempfile
import os

mcp = FastMCP("research-tools")

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _parse_entries(entries: list) -> list:
    papers = []
    for entry in entries:
        pdf_url = ""
        for link in entry.get("links", []):
            if link.get("type") == "application/pdf" or link.get("title") == "pdf":
                pdf_url = link.get("href", "")
                break
        if not pdf_url:
            pdf_url = entry.get("id", "").replace("/abs/", "/pdf/")

        arxiv_id = entry.get("id", "").split("/abs/")[-1]

        papers.append({
            "arxiv_id": arxiv_id,
            "title": _clean_text(entry.get("title", "")),
            "authors": [a.get("name", "") for a in entry.get("authors", [])],
            "summary": _clean_text(entry.get("summary", "")),
            "published": entry.get("published", ""),
            "updated": entry.get("updated", ""),
            "categories": [tag.get("term", "") for tag in entry.get("tags", [])],
            "pdf_url": pdf_url,
            "abstract_url": entry.get("id", ""),
        })
    return papers


def _extract_pdf_text(pdf_url: str, max_pages: int = 10) -> str:
    """
    Download a PDF from a URL and extract its text content.
    Limits to max_pages to avoid token overflow.
    """
    try:
        import pypdf
    except ImportError:
        return "Error: pypdf is not installed. Run `pip install pypdf`."

    headers = {"User-Agent": "Mozilla/5.0 (research-mcp-server)"}

    try:
        response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error downloading PDF: {str(e)}"

    # Write to a temp file and extract
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        reader = pypdf.PdfReader(tmp_path)
        total_pages = len(reader.pages)
        pages_to_read = min(max_pages, total_pages)

        extracted_pages = []
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text() or ""
            extracted_pages.append(f"--- Page {i+1} ---\n{_clean_text(page_text)}")

        full_text = "\n\n".join(extracted_pages)

        return full_text if full_text.strip() else "No extractable text found in PDF (may be scanned/image-based)."

    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@mcp.tool()
def search_arxiv(
    query: str,
    max_results: int = 5,
    category: str = "",
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> dict:
    """
    Search arxiv for research papers.

    Args:
        query: Search terms (e.g. 'transformer attention mechanism')
        max_results: Number of results to return (max 25)
        category: Optional arxiv category e.g. 'cs.AI', 'cs.LG', 'stat.ML'
        sort_by: 'submittedDate' | 'relevance' | 'lastUpdatedDate'
        sort_order: 'descending' | 'ascending'
    """
    max_results = min(max_results, 25)
    search_query = f"all:{urllib.parse.quote(query)}"
    if category:
        search_query += f"+AND+cat:{category}"

    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={search_query}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy={sort_by}"
        f"&sortOrder={sort_order}"
    )
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return {"error": "Failed to parse arxiv response.", "papers": []}
        papers = _parse_entries(feed.entries)
        return {
            "query": query,
            "category_filter": category or "none",
            "total_found": len(papers),
            "papers": papers,
        }
    except Exception as e:
        return {"error": str(e), "papers": []}


@mcp.tool()
def get_paper_by_id(arxiv_id: str) -> dict:
    """
    Fetch full metadata for a specific arxiv paper by its ID.

    Args:
        arxiv_id: e.g. '2301.07041' or '2301.07041v2'
    """
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return {"error": f"No paper found for ID: {arxiv_id}"}
        return _parse_entries(feed.entries)[0]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def search_arxiv_by_author(author_name: str, max_results: int = 5) -> dict:
    """
    Search arxiv papers by a specific author name.

    Args:
        author_name: Full or partial author name, e.g. 'Yann LeCun'
        max_results: Number of results (max 25)
    """
    max_results = min(max_results, 25)
    query = urllib.parse.quote(author_name)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=au:{query}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    try:
        feed = feedparser.parse(url)
        papers = _parse_entries(feed.entries)
        return {"author": author_name, "total_found": len(papers), "papers": papers}
    except Exception as e:
        return {"error": str(e), "papers": []}


@mcp.tool()
def get_paper_summary(arxiv_id: str) -> dict:
    """
    Get a clean title + abstract for a paper.

    Args:
        arxiv_id: e.g. '1706.03762'
    """
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return {"error": f"Paper not found: {arxiv_id}"}
        entry = feed.entries[0]
        return {
            "arxiv_id": arxiv_id,
            "title": _clean_text(entry.get("title", "")),
            "authors": [a.get("name", "") for a in entry.get("authors", [])],
            "abstract": _clean_text(entry.get("summary", "")),
            "published": entry.get("published", ""),
            "pdf_url": entry.get("id", "").replace("/abs/", "/pdf/"),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def read_paper_content(arxiv_id: str, max_pages: int = 10) -> dict:
    """
    Download and extract the full text content of a paper's PDF.
    Use this when the user wants to READ, ANALYZE, or ASK QUESTIONS about
    the actual content of a paper — not just its abstract.

    Args:
        arxiv_id: e.g. '1706.03762' (Attention is All You Need)
        max_pages: How many pages to extract (default 10, max 30)
                   Increase if the paper is long and you need more content.
    """
    max_pages = min(max_pages, 30)  # hard cap to avoid token overflow

    # First fetch metadata
    meta_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        feed = feedparser.parse(meta_url)
        if not feed.entries:
            return {"error": f"Paper not found: {arxiv_id}"}

        entry = feed.entries[0]
        pdf_url = entry.get("id", "").replace("/abs/", "/pdf/")
        title = _clean_text(entry.get("title", ""))
        authors = [a.get("name", "") for a in entry.get("authors", [])]
        abstract = _clean_text(entry.get("summary", ""))
        published = entry.get("published", "")

    except Exception as e:
        return {"error": f"Metadata fetch failed: {str(e)}"}

    # Now extract PDF text
    pdf_text = _extract_pdf_text(pdf_url, max_pages=max_pages)

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "pdf_url": pdf_url,
        "pages_extracted": max_pages,
        "full_text": pdf_text,         # ← actual paper content the LLM can read
    }


@mcp.tool()
def search_and_read_top_paper(
    query: str,
    category: str = "",
    max_pages: int = 10,
) -> dict:
    """
    Search arxiv and immediately read the full content of the top result.
    Use this when the user wants to find AND read the most relevant paper
    on a topic in one step.

    Args:
        query: Search terms e.g. 'retrieval augmented generation survey'
        category: Optional category filter e.g. 'cs.AI'
        max_pages: Pages to extract from the PDF (default 10, max 30)
    """
    # Step 1 — search
    search_result = search_arxiv(query=query, max_results=1, category=category, sort_by="relevance")
    if "error" in search_result or not search_result.get("papers"):
        return {"error": "No papers found for the query.", "query": query}

    top_paper = search_result["papers"][0]
    arxiv_id = top_paper["arxiv_id"]

    # Step 2 — read
    content = read_paper_content(arxiv_id=arxiv_id, max_pages=max_pages)
    content["search_query"] = query  # attach original query for context
    return content


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)

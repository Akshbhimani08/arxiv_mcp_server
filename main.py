from fastmcp import FastMCP
import feedparser
import requests
import re
import urllib.parse
from datetime import datetime

mcp = FastMCP("research-tools")

def _clean_text(text: str) -> str:
    """Remove excess whitespace and newlines from arxiv text fields."""
    return re.sub(r"\s+", " ", text).strip()

def _parse_entries(entries: list) -> list:
    """Safely parse feedparser entries into clean dicts."""
    papers = []
    for entry in entries:
        # Safely get PDF link — it's not always index 1
        pdf_url = ""
        for link in entry.get("links", []):
            if link.get("type") == "application/pdf" or link.get("title") == "pdf":
                pdf_url = link.get("href", "")
                break
        if not pdf_url:
            # fallback: replace /abs/ with /pdf/ in the entry id
            pdf_url = entry.get("id", "").replace("/abs/", "/pdf/")

        # Extract arxiv ID from URL
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
        category: Optional arxiv category filter e.g. 'cs.AI', 'cs.LG', 'stat.ML', 'math.CO'
        sort_by: 'submittedDate' | 'relevance' | 'lastUpdatedDate'
        sort_order: 'descending' | 'ascending'
    """
    max_results = min(max_results, 25)  # cap to avoid abuse

    # Build query — combine keyword and category if given
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
        arxiv_id: The arxiv paper ID, e.g. '2301.07041' or '2301.07041v2'
    """
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return {"error": f"No paper found for ID: {arxiv_id}"}
        papers = _parse_entries(feed.entries)
        return papers[0]
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
        return {
            "author": author_name,
            "total_found": len(papers),
            "papers": papers,
        }
    except Exception as e:
        return {"error": str(e), "papers": []}


@mcp.tool()
def get_paper_summary(arxiv_id: str) -> dict:
    """
    Get a clean title + abstract for a paper — useful for quick reading
    before deciding to fetch the full PDF.

    Args:
        arxiv_id: e.g. '1706.03762' (Attention is All You Need)
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


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)

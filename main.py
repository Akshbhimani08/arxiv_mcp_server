from fastmcp import FastMCP
import feedparser
import requests

mcp = FastMCP("research-tools")


@mcp.tool()
def search_arxiv(query: str, max_results: int = 5):

    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{query}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate"
        f"&sortOrder=descending"
    )

    feed = feedparser.parse(url)

    papers = []

    for entry in feed.entries:

        papers.append({
            "title": entry.title,
            "authors": [a.name for a in entry.authors],
            "summary": entry.summary,
            "published": entry.published,
            "pdf_url": entry.links[1].href
        })

    return papers


if __name__ == "__main__":
    mcp.run(transport="http",host="0.0.0.0",port=8000)
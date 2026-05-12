# arXiv MCP Server

Research paper discovery and retrieval over the Model Context Protocol (MCP).

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python) ![FastMCP](https://img.shields.io/badge/FastMCP-3.2.4-green) ![MCP](https://img.shields.io/badge/Protocol-MCP-purple) ![Deployed](https://img.shields.io/badge/Deployed-Render-orange) ![arXiv](https://img.shields.io/badge/Source-arXiv-red)

---

## Problem Statement

Researchers and AI agents lack a standardized way to programmatically search, retrieve, and read scientific papers from arXiv without manual copy-pasting or custom scrapers. This server exposes arXiv's research corpus as structured MCP tools, enabling any MCP-compatible AI client to autonomously navigate and reason over scientific literature in real time.

---

## Architecture

```
MCP Client (Claude / Cursor / ChatGPT / VS Code ...)
        │
        │  MCP over SSE (HTTP)
        ▼
arXiv MCP Server  (FastMCP · Python 3.13 · Render)
        │
        │  arXiv Atom Feed API
        ▼
  export.arxiv.org
```

---

## Tools

| Tool | Description |
|------|-------------|
| `search_arxiv` | Search papers by keyword/topic, sorted by submission date |

> More tools (get by ID, full PDF extraction, author search) are on the roadmap — see below.

---

## Quickstart

### Connect as a Remote MCP Client

Add the following to your MCP client config:

```json
{
  "mcpServers": {
    "arxiv": {
      "url": "https://arxiv-mcp-server-1jtq.onrender.com/mcp"
    }
  }
}
```

**Claude Desktop** → `claude_desktop_config.json`  
**Cursor** → `.cursor/mcp.json`  
**VS Code / Cline** → MCP Servers tab → Remote Extension → paste URL

### Run Locally

```bash
# Clone the repo
git clone https://github.com/Akshbhimani08/arxiv_mcp_server.git
cd arxiv_mcp_server

# Install dependencies (requires uv)
uv sync

# Run the server
python main.py
```

Server starts at `http://localhost:8000/mcp`.

---

## Compatible Clients

| Client | Type | Transport |
|--------|------|-----------|
| Claude Desktop | AI Assistant | SSE |
| ChatGPT Desktop | AI Assistant | SSE |
| Cursor | Code Editor | SSE |
| VS Code + Copilot | Code Editor | SSE |
| Cline (VSCode ext.) | AI Agent | SSE |
| Zed | Code Editor | SSE |
| Goose (Block) | CLI Agent | SSE |
| LangChain / LangGraph | Framework | SSE |
| Microsoft Semantic Kernel | Framework | SSE |

---

## Project Structure

```
arxiv_mcp_server/
├── main.py            # FastMCP server + tool definitions
├── pyproject.toml     # Project metadata and dependencies
├── uv.lock            # Locked dependency versions
├── .python-version    # Python version pin (3.13)
└── README.md
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | ≥ 3.2.4 | MCP server framework |
| `feedparser` | ≥ 6.0.12 | arXiv Atom feed parsing |
| `requests` | ≥ 2.33.1 | HTTP client |

---

## Deployment

Deployed as a remote MCP server on **Render** using SSE (Server-Sent Events) transport.

```
Server URL: https://arxiv-mcp-server-1jtq.onrender.com/mcp
```

No local setup required — connect any MCP-compatible client directly to the URL above.

---

## Roadmap

- [ ] `get_paper_by_id` — Fetch full metadata for a specific arXiv paper ID
- [ ] `get_paper_summary` — Return clean title + abstract only
- [ ] `read_paper_content` — Download and extract full PDF text
- [ ] `search_and_read_top_paper` — One-shot search + read pipeline
- [ ] `search_arxiv_by_author` — Browse papers by a specific researcher
- [ ] Category/subject-area filtering (`cs.AI`, `math.ST`, etc.)
- [ ] Pagination support for large result sets
- [ ] OAuth authentication for enterprise deployments

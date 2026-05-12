# arXiv MCP Server

Research paper discovery and retrieval over the Model Context Protocol (MCP).

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://www.python.org/downloads/release/python-3130/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.2.4-green)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io/)
[![Deployed](https://img.shields.io/badge/Deployed-Render-orange)](https://arxiv-mcp-server-1jtq.onrender.com/mcp)
[![arXiv](https://img.shields.io/badge/Source-arXiv-red)](https://arxiv.org/)

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

## JSON-RPC 2.0 — The Data Transport Layer

The Model Context Protocol uses **[JSON-RPC 2.0](https://www.jsonrpc.org/specification)** as its underlying data transport layer. Every message exchanged between an MCP client and this server is a JSON-RPC 2.0 envelope.

### What is JSON-RPC 2.0?

JSON-RPC 2.0 is a stateless, lightweight remote procedure call (RPC) protocol encoded in JSON. It defines a strict message structure so any client can call any server method without knowing the underlying transport (HTTP, WebSocket, SSE, stdio).

### Message Structure

**Request** (client → server):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_arxiv",
    "arguments": { "query": "transformer attention mechanism", "max_results": 5 }
  }
}
```

**Success Response** (server → client):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "Found 5 papers on transformer attention..." }
    ]
  }
}
```

**Error Response** (server → client):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Field 'query' is required"
  }
}
```

**Notification** (fire-and-forget, no `id`, no response expected):
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": { "progressToken": "abc123", "progress": 50, "total": 100 }
}
```

### Key Rules

| Rule | Detail |
|------|--------|
| `"jsonrpc": "2.0"` | **Required** on every message |
| `id` | Present on requests; must be echoed in the matching response. Omit for notifications |
| `method` | String naming the procedure (e.g. `tools/call`, `tools/list`) |
| `params` | Optional object or array of arguments |
| `result` **xor** `error` | A response carries exactly one of these, never both |

### Standard Error Codes

| Code | Meaning |
|------|---------|
| `-32700` | Parse error — invalid JSON |
| `-32600` | Invalid request — missing required fields |
| `-32601` | Method not found |
| `-32602` | Invalid params |
| `-32603` | Internal error |
| `-32000` to `-32099` | Server-defined application errors |

### How MCP Uses JSON-RPC 2.0

MCP is **transport-agnostic**: the same JSON-RPC messages flow over:
- **SSE (HTTP)** — used by this server (and Claude Desktop, Cursor, etc.)
- **stdio** — used for local subprocess servers
- **WebSocket** — used by some browser-based clients

FastMCP handles all serialisation and routing automatically. When you call `search_arxiv`, FastMCP wraps your tool result in a `tools/call` JSON-RPC response before sending it back over SSE — you never have to write the envelope yourself.

> **Spec**: https://www.jsonrpc.org/specification

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

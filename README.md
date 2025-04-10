# SQLite MCP Server

A lightweight Model Context Protocol (MCP) server that enables Large Language Models (LLMs) to autonomously interact with SQLite databases.

## Showcases

<video src="https://github.com/dubydu/sqlite-mcp/raw/main/sqlite-mcp.mov" autoplay loop muted></video>

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dubydu/sqlite-mcp.git
cd sqlite-mcp
```

2. Set up a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Start
```bash
python src/entry.py --db-path /path/to/your/database.db
```

### Command Line Options

- `--db-path`: Path to SQLite database file (default: "./db/database.db")

## Available MCP Tools

For the full list of tools, see the [MCP_TOOLS.md](MCP_TOOLS.md)

## MCP CLients Configuration

* 5ire
```json
{
  "name": "SQLite",
  "key": "sqlite",
  "command": "/absolute/path/to/sqlite-mcp/.venv/bin/python",
  "args": [
    "/absolute/path/to/sqlite-mcp/src/entry.py",
    "--db-path",
    "/path/to/database.db"
  ]
}
```

* Claude Desktop
```json
{
  "mcpServers": {
    "sqlite-mcp": {
      "command": "/absolute/path/to/sqlite-mcp/.venv/bin/python",
      "args": [
        "/absolute/path/to/sqlite-mcp/src/entry.py",
         "--db-path",
         "/path/to/database.db"
      ]
    }
  }
}
```

## Requirements

- Python 3.12.7+
- [MCP](https://pypi.org/project/mcp/) 1.6.0+
- [PyTest](https://pypi.org/project/pytest/) 8.3.5+
# SQLite MCP Server

A lightweight Model Context Protocol (MCP) server that enables Large Language Models (LLMs) to autonomously interact with SQLite databases.

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
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
python server.py
```

### Custom Configuration
```bash
python server.py --db-path /path/to/your/database.db --host 0.0.0.0 --port 9000
```

### Command Line Options

- `--db-path`: Path to SQLite database file (default: "./db/default.db")
- `--host`: Host address to bind the server (default: "127.0.0.1")
- `--port`: Port number to bind the server (default: 8080)

## Available MCP Tools

1. **sqlite_query**
   - Execute custom SQL queries with optional parameters
   - Supports both read (SELECT) and write (INSERT/UPDATE/DELETE) operations

2. **get_all_items**
   - Retrieve all rows from a specified table
   - Usage: `get_all_items(table_name)`

3. **get_item_by_id**
   - Retrieve a single row by ID from any table
   - Usage: `get_item_by_id(table_name, id_value, id_column)`

4. **get_item_by_name**
   - Retrieve a single row by name from any table
   - Usage: `get_item_by_name(table_name, name_value, name_column="name")`

5. **list_all_tables**
   - Get a list of all tables in the database
   - Usage: `list_all_tables()`

6. **create_item**
   - Create a new row in a specified table
   - Usage: `create_item(table_name, data)`
   - Returns the ID of the newly created row

7. **update_item**
   - Update an existing row in a specified table
   - Usage: `update_item(table_name, id_value, data, id_column)`
   - Updates specified columns with new values

8. **delete_item**
   - Delete a row from a specified table
   - Usage: `delete_item(table_name, id_value, id_column)`
   - Removes the specified row from the table

## MCP CLients Configuration

* 5ire
```json
{
  "name": "SQLite",
  "key": "sqlite",
  "command": "/absolute/path/to/sqlite-mcp/.venv/bin/python",
  "args": [
    "/absolute/path/to/sqlite-mcp/server.py",
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
        "/absolute/path/to/sqlite-mcp/server.py",
         "--db-path",
         "/path/to/database.db"
      ]
    }
  }
}
```

## Requirements

- Python 3.7+
- SQLite3
- FastMCP library
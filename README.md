# SQLite MCP Server

A lightweight Model Context Protocol (MCP) server that enables Large Language Models (LLMs) to autonomously interact with SQLite databases.

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

1. **sqlite_query**
   - Execute custom SQL queries with optional parameters
   - Supports both read (SELECT) and write (INSERT/UPDATE/DELETE) operations

2. **get_item_by_id**
   - Retrieve a single row by ID from any table
   - Usage: `get_item_by_id(table_name, id_value, id_column)`

3. **get_item_by_name**
   - Retrieve a single row by name from any table
   - Usage: `get_item_by_name(table_name, name_value, name_column="name")`

4. **create_item**
   - Create a new row in a specified table
   - Usage: `create_item(table_name, data)`
   - Returns the ID of the newly created row

5. **update_item**
   - Update an existing row in a specified table
   - Usage: `update_item(table_name, id_value, data, id_column)`
   - Updates specified columns with new values

6. **delete_item**
   - Delete a row from a specified table
   - Usage: `delete_item(table_name, id_value, id_column)`
   - Removes the specified row from the table

7. **get_all_items**
   - Retrieve all rows from a specified table
   - Usage: `get_all_items(table_name)`

8. **get_all_tables**
   - Get a list of all tables in the database
   - Usage: `get_all_tables()`

9. **get_db_version()**
   - Get version of the database
   - Usage: `get_db_version()`

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

- Python 3.7+
- SQLite3
- FastMCP library
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

2. **get_item**
   - Retrieve a single row from any table using a specified column
   - Usage: `get_item(table_name, value, column)`

3. **update_item**
   - Update an existing row in a specified table
   - Usage: `update_item(table_name, value, data, column)`
   - Updates specified columns with new values

4. **delete_item**
   - Delete a row from a specified table
   - Usage: `delete_item(table_name, value, column)`
   - Removes the specified row from the table

5. **create_item**
   - Create a new row in a specified table
   - Usage: `create_item(table_name, data)`
   - Returns the ID of the newly created row

6. **get_all_items**
   - Retrieve all rows from a specified table
   - Usage: `get_all_items(table_name)`

7. **get_all_tables**
   - Get a list of all tables in the database
   - Usage: `get_all_tables()`

8. **create_table**
   - Create a new table in the database
   - Usage: `create_table(table_name, columns)`
   - Columns should be a dictionary defining column properties

9. **drop_table**
   - Drop (delete) a table from the database
   - Usage: `drop_table(table_name, check_exists)`

10. **alter_table**
    - Modify the structure of an existing table
    - Usage: `alter_table(table_name, operation, column_name, column_type, new_column_name)`
    - Supports operations: add_column, drop_column, rename_column

11. **backup_database**
    - Create a backup of the SQLite database
    - Usage: `backup_database(backup_filename)`
    - Creates a backup file in the same directory as the main database

12. **get_db_version**
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

- Python 3.12.7+
- [MCP](https://pypi.org/project/mcp/) 1.6.0+
- [PyTest](https://pypi.org/project/pytest/) 8.3.5+
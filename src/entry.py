import time
import signal
import sys
import logging
import sqlite3
from typing import Optional, Dict, Any
import os
from mcp.server.fastmcp import FastMCP
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_NAME = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "db/database.db"))

def signal_handler(sig, frame):
    """
    Handle system signals to gracefully shut down the server.
    """
    print("Shutting down server...")
    sys.exit(0)

def setup_signal_handling():
    """
    Setup signal handling for graceful termination.
    """
    signal.signal(signal.SIGINT, signal_handler)

def validate_database():
    """
    Validate database existence and accessibility.
    Creates the database directory if it doesn't exist.
    """
    db_dir = os.path.dirname(DB_NAME)
    
    # Create directory structure if it doesn't exist
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")
            sys.exit(1)
    
    # Test database connection
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.close()
        logger.info(f"Successfully connected to database at: {DB_NAME}")
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Database path: {DB_NAME}")
        logger.error(f"Check if you have write permissions to: {db_dir}")
        sys.exit(1)

# Initialize the FastMCP server
mcp = FastMCP(name="sqlite-mcp")

@mcp.tool(name="sqlite_query", description="Execute a SQL query on the SQLite database")
def execute_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a SQL query on the SQLite database.

    Args:
        query (str): The SQL query string.
        parameters (Optional[Dict[str, Any]]): Optional dictionary of parameters for parameterized queries.

    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing the results or error.
    """
    # Additional comment: This function handles both read (SELECT) and write (INSERT/UPDATE/DELETE) queries
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)

        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            results = [dict(row) for row in results]
            return {"success": True, "results": results}
        else:
            conn.commit()
            return {"success": True, "message": "Query executed successfully"}
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()

@mcp.tool(name="get_item", description="Retrieve a single row from a specified table")
def get_item(table_name: str, value: str, column: str) -> Dict[str, Any]:
    """
    Retrieves a single row from the specified table.

    Args:
        table_name (str): The name of the table to query.
        value (str): The value to search for.
        column (str): The name of the column.

    Returns:
        Dict[str, Any]: A dictionary containing the query result or an error.
    """
    # Using parameterized query to prevent SQL injection
    query = f"SELECT * FROM {table_name} WHERE {column} = ?;"
    parameters = (value,)

    return execute_query(query, parameters)

@mcp.tool(name="update_item", description="Update an existing row in a specified table")
def update_item(table_name: str, value: Any, data: Dict[str, Any], column: str) -> Dict[str, Any]:
    """
    Updates an existing row in the specified table.

    Args:
        table_name (str): The name of the table to update.
        value (Any): The value of the row to update.
        data (Dict[str, Any]): Dictionary containing column names and their new values.
        column (str, optional): The name of the column.

    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing the result or error.
    """
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {column} = ?;"
    
    # Add id_value to the parameters
    parameters = tuple(data.values()) + (value,)
    
    try:
        result = execute_query(query, parameters)
        if result["success"]:
            return {
                "success": True,
                "message": "Item updated successfully"
            }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@mcp.tool(name="delete_item", description="Delete a row from a specified table")
def delete_item(table_name: str, value: Any, column: str) -> Dict[str, Any]:
    """
    Deletes a row from the specified table.

    Args:
        table_name (str): The name of the table to delete from.
        value (Any): The ID value of the row to delete.
        column (str, optional): The name of the ID column. Defaults to "id".

    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing the result or error.
    """
    query = f"DELETE FROM {table_name} WHERE {column} = ?;"
    
    try:
        result = execute_query(query, (value,))
        if result["success"]:
            return {
                "success": True,
                "message": "Item deleted successfully"
            }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@mcp.tool(name="create_item", description="Create a new row in a specified table")
def create_item(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new row in the specified table with the provided data.

    Args:
        table_name (str): The name of the table to insert into.
        data (Dict[str, Any]): Dictionary containing column names and their values.

    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing the new row's ID or error.
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
    
    try:
        result = execute_query(query, tuple(data.values()))
        if result["success"]:
            # Get the last inserted row ID
            last_id_query = "SELECT last_insert_rowid();"
            id_result = execute_query(last_id_query)
            if id_result["success"]:
                return {
                    "success": True,
                    "message": "Item created successfully",
                    "id": id_result["results"][0]["last_insert_rowid()"]
                }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="get_all_items", description="Retrieve all rows from a specified table in the SQLite database")
def get_all_items(table_name: str) -> Dict[str, Any]:
    """
    Retrieves all rows from the specified table.

    Args:
        table_name (str): The name of the table to query.

    Returns:
        Dict[str, Any]: A dictionary containing the query results or an error.
    """
    # IMPORTANT: This is a simple example.
    # In a real application, sanitize/validate 'table_name' to avoid SQL injection!
    query = f"SELECT * FROM {table_name};"
    return execute_query(query)

@mcp.tool(name="get_all_tables", description="Returns a list of all table names in the SQLite database")
def get_all_tables() -> Dict[str, Any]:
    """
    Fetch all table names from the SQLite database.

    Returns:
        Dict[str, Any]: A dictionary containing the list of tables or an error.
    """
    query = """
    SELECT name 
    FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name;
    """
    return execute_query(query)

@mcp.tool(name="get_db_version", description="Returns the version of the SQLite database")
def get_db_version() -> Dict[str, Any]:
    """
    Fetch the version information of the SQLite database.

    Returns:
        Dict[str, Any]: A dictionary containing the database version information or an error.
    """
    query = "SELECT sqlite_version();"
    return execute_query(query)

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='SQLite MCP Server')
    parser.add_argument(
        '--db-path',
        required=True,
        help='Path to SQLite database file'
    )
    parser.add_argument(
        '--host',
        default="127.0.0.1",
        help='Host address to bind the server'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port number to bind the server'
    )
    return parser.parse_args()

def main():
    """
    Main entry point for the MCP server.
    """
    args = parse_arguments()
    
    # Update DB_NAME with command line argument
    global DB_NAME
    print(f"Database path 1: {DB_NAME}")
    DB_NAME = os.path.abspath(args.db_path)
    
    print(f"Database path: {DB_NAME}")
    setup_signal_handling()
    validate_database()

    print(f"Starting MCP server 'sqlite-mcp' on {args.host}:{args.port}")
    mcp.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}")
        # Sleep before exiting to give time for error logs
        time.sleep(5)

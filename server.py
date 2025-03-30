# Refactored code with an additional comment

import time
import signal
import sys
import logging
import sqlite3
from typing import Optional, Dict, Any
import os
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_NAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "db/chinook.db"))

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
mcp = FastMCP(
    name="sqlite-mcp",
    host="127.0.0.1",
    port=8080,
    timeout=30
)

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

@mcp.tool(name="list_all_tables", description="Returns a list of all table names in the SQLite database")
def list_all_tables() -> Dict[str, Any]:
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

def main():
    """
    Main entry point for the MCP server.
    """
    print(DB_NAME)
    setup_signal_handling()
    validate_database()
    print("Starting MCP server 'sqlite-mcp' on 127.0.0.1:8080")
    mcp.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}")
        # Sleep before exiting to give time for error logs
        time.sleep(5)

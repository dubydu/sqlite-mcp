import time
import signal
import sys
import logging
import sqlite3
from typing import Optional, Dict, Any
import os
from mcp.server.fastmcp import FastMCP
import argparse
import json

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

@mcp.tool(name="execute_query", description="Execute a SQL query on the database")
def execute_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a SQL query on the database.

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

@mcp.tool(name="get_all_items", description="Retrieve all rows from a specified table in the database")
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

@mcp.tool(name="get_all_tables", description="Returns a list of all table names in the database")
def get_all_tables() -> Dict[str, Any]:
    """
    Fetch all table names from the database.

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

@mcp.tool(name="create_table", description="Create a new table in the database")
def create_table(table_name: str, columns: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates a new table in the database with the specified columns.
    
    Args:
        table_name (str): The name of the table to create.
        columns (Dict[str, Dict[str, Any]]): Dictionary where keys are column names and values are 
                                             dictionaries with column definitions:
                                             {
                                                 "type": "TEXT/INTEGER/REAL/BLOB",
                                                 "primary_key": bool,
                                                 "not_null": bool,
                                                 "unique": bool,
                                                 "default": Any (optional)
                                             }
    
    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing a result message or error.
    """
    try:
        if not table_name or not columns:
            return {"success": False, "error": "Table name and columns are required"}
        
        # Build column definitions
        column_defs = []
        for col_name, col_def in columns.items():
            # Validate column type
            col_type = col_def.get("type", "").upper()
            if col_type not in ["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"]:
                return {"success": False, "error": f"Invalid column type: {col_type}"}
            
            # Start building the column definition
            col_str = f"{col_name} {col_type}"
            
            # Add constraints
            if col_def.get("primary_key"):
                col_str += " PRIMARY KEY"
            if col_def.get("not_null"):
                col_str += " NOT NULL"
            if col_def.get("unique"):
                col_str += " UNIQUE"
            if "default" in col_def:
                default_val = col_def["default"]
                # Handle string defaults with quotes
                if isinstance(default_val, str):
                    col_str += f" DEFAULT '{default_val}'"
                else:
                    col_str += f" DEFAULT {default_val}"
            
            column_defs.append(col_str)
        
        # Build the complete CREATE TABLE query
        columns_str = ", ".join(column_defs)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str});"
        
        # Execute the query
        result = execute_query(query)
        if result["success"]:
            return {
                "success": True,
                "message": f"Table '{table_name}' created successfully"
            }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="alter_table", description="Modify the structure of an existing table in the database")
def alter_table(table_name: str, operation: str, column_name: str = None, column_type: str = None, 
                new_column_name: str = None) -> Dict[str, Any]:
    """
    Alters an existing table structure in the database.
    
    Args:
        table_name (str): The name of the table to alter.
        operation (str): The type of alteration ('add_column', 'drop_column', 'rename_column').
        column_name (str, optional): The name of the column to add, drop or rename.
        column_type (str, optional): The data type for the new column (required when adding a column).
        new_column_name (str, optional): The new name for the column (required when renaming a column).
    
    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing a result message or error.
    """
    try:
        if operation.lower() == "add_column":
            if not column_name or not column_type:
                return {"success": False, "error": "Column name and type are required for add_column operation"}
            
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"
            return execute_query(query)
            
        elif operation.lower() == "rename_column":
            if not column_name or not new_column_name:
                return {"success": False, "error": "Column name and new column name are required for rename_column operation"}
            
            query = f"ALTER TABLE {table_name} RENAME COLUMN {column_name} TO {new_column_name};"
            return execute_query(query)
            
        elif operation.lower() == "drop_column":
            if not column_name:
                return {"success": False, "error": "Column name is required for drop_column operation"}
            
            # SQLite doesn't directly support DROP COLUMN before version 3.35.0 (Feb 2021)
            # For compatibility, we need to use a more complex approach involving creating a new table
            
            # Get current table schema excluding the column to drop
            table_info_query = f"PRAGMA table_info({table_name});"
            table_info = execute_query(table_info_query)
            
            if not table_info["success"]:
                return table_info
                
            # Filter out the column to drop and build column definitions
            columns = []
            select_columns = []
            
            for col in table_info["results"]:
                if col["name"] != column_name:
                    col_def = f"{col['name']} {col['type']}"
                    if col["notnull"] == 1:
                        col_def += " NOT NULL"
                    if col["dflt_value"] is not None:
                        col_def += f" DEFAULT {col['dflt_value']}"
                    if col["pk"] == 1:
                        col_def += " PRIMARY KEY"
                    
                    columns.append(col_def)
                    select_columns.append(col['name'])
            
            if len(columns) == len(table_info["results"]):
                return {"success": False, "error": f"Column {column_name} does not exist in table {table_name}"}
                
            # Execute the drop operation as a transaction
            column_str = ", ".join(columns)
            select_column_str = ", ".join(select_columns)
            
            queries = [
                f"BEGIN TRANSACTION;",
                f"CREATE TABLE {table_name}_temp ({column_str});",
                f"INSERT INTO {table_name}_temp SELECT {select_column_str} FROM {table_name};",
                f"DROP TABLE {table_name};",
                f"ALTER TABLE {table_name}_temp RENAME TO {table_name};",
                f"COMMIT;"
            ]
            
            for query in queries:
                result = execute_query(query)
                if not result["success"]:
                    execute_query("ROLLBACK;")
                    return result
                    
            return {"success": True, "message": f"Column {column_name} dropped from table {table_name}"}
            
        else:
            return {"success": False, "error": f"Unsupported operation: {operation}. Supported operations are 'add_column', 'drop_column', and 'rename_column'"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="drop_table", description="Drop (delete) a table from the database")
def drop_table(table_name: str, check_exists: bool = True) -> Dict[str, Any]:
    """
    Drops (deletes) a table from the database.
    
    Args:
        table_name (str): The name of the table to drop.
        check_exists (bool, optional): If True, checks if the table exists before dropping.
                                      Defaults to True.
    
    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing a result message or error.
    """
    try:
        # Check if table exists when required
        if check_exists:
            check_query = f"""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='{table_name}';
            """
            check_result = execute_query(check_query)
            
            if not check_result["success"]:
                return check_result
                
            if not check_result["results"]:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' does not exist"
                }
        
        # Build the drop table query
        if check_exists:
            query = f"DROP TABLE IF EXISTS {table_name};"
        else:
            query = f"DROP TABLE {table_name};"
        
        # Execute the query
        result = execute_query(query)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Table '{table_name}' dropped successfully"
            }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(name="backup_database", description="Create a backup of the SQLite database")
def backup_database(backup_filename: str = None) -> Dict[str, Any]:
    """
    Creates a backup of the current SQLite database in the same directory.
    
    Args:
        backup_filename (str, optional): The filename for the backup. 
                                         If not provided, a timestamp-based name will be used.
    
    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing a result message or error.
    """
    try:
        # Get the directory where the main database is located
        db_dir = os.path.dirname(DB_NAME)
        
        # Generate backup filename if not provided
        if not backup_filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"database_backup_{timestamp}.db"
        elif not backup_filename.endswith(".db"):
            backup_filename = f"{backup_filename}.db"
            
        # Sanitize: strip any directory components to prevent path traversal
        backup_filename = os.path.basename(backup_filename)

        # Create the full destination path
        destination_path = os.path.join(db_dir, backup_filename)

        # Validate the resolved path stays within the database directory
        if not os.path.abspath(destination_path).startswith(os.path.abspath(db_dir) + os.sep) and \
           os.path.abspath(destination_path) != os.path.abspath(db_dir):
            return {"success": False, "error": "Invalid backup filename: path traversal not allowed"}

        # Make sure we're not overwriting the original database
        if os.path.abspath(destination_path) == os.path.abspath(DB_NAME):
            return {"success": False, "error": "Backup filename cannot be the same as the original database"}
            
        # Connect to the source database
        source_conn = None
        dest_conn = None
        try:
            # Open the source database
            source_conn = sqlite3.connect(DB_NAME)
            
            # Open the destination database
            dest_conn = sqlite3.connect(destination_path)
            
            # Back up database
            source_conn.backup(dest_conn)
            
            return {
                "success": True,
                "message": f"Database successfully backed up to {destination_path}"
            }
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error during backup: {str(e)}"}
        finally:
            # Close connections
            if source_conn:
                source_conn.close()
            if dest_conn:
                dest_conn.close()
    except Exception as e:
        return {"success": False, "error": f"Error creating backup: {str(e)}"}

@mcp.tool(name="extract_to_json", description="Extract data from a table and save it as a JSON file")
def extract_to_json(table_name: str, output_filename: str = None) -> Dict[str, Any]:
    """
    Extracts data from a specified table in the SQLite database and saves it as a JSON file.

    Args:
        table_name (str): The name of the table to extract data from.
        output_filename (str, optional): The name of the output JSON file. 
                                         If not provided, a timestamp-based name will be used.

    Returns:
        Dict[str, Any]: A dictionary indicating success/failure and containing a result message or error.
    """
    try:
        # Validate table_name to prevent SQL injection
        if not table_name.isidentifier():
            return {"success": False, "error": "Invalid table name"}

        # Anchor exports to the database directory
        export_dir = os.path.dirname(DB_NAME)

        # Generate output filename if not provided
        if not output_filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{table_name}_data_{timestamp}.json"
        elif not output_filename.endswith(".json"):
            output_filename = f"{output_filename}.json"

        # Sanitize: strip any directory components to prevent path traversal
        output_filename = os.path.basename(output_filename)

        # Build the full path and validate it stays within the export directory
        output_path = os.path.join(export_dir, output_filename)
        if not os.path.abspath(output_path).startswith(os.path.abspath(export_dir) + os.sep) and \
           os.path.abspath(output_path) != os.path.abspath(export_dir):
            return {"success": False, "error": "Invalid output filename: path traversal not allowed"}

        # Query all data from the table using parameterized identifier
        query = f"SELECT * FROM [{table_name}];"
        result = execute_query(query)

        if not result["success"]:
            return result

        # Write data to JSON file
        data = result.get("results", [])
        with open(output_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        return {
            "success": True,
            "message": f"Data from table '{table_name}' successfully extracted to {output_path}"
        }
    except Exception as e:
        return {"success": False, "error": f"Error extracting data to JSON: {str(e)}"}

@mcp.tool(name="get_db_version", description="Returns the version of the database")
def get_db_version() -> Dict[str, Any]:
    """
    Fetch the version information of the database.

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
        help='Path to database file'
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

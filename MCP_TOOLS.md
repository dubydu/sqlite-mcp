## Available MCP Tools

1. **execute_query**
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

13. **extract_to_json**
    - Extract data from a table and save it as a JSON file
    - Usage: `extract_to_json(table_name, output_filename)`
    - Saves the table's data to a JSON file. If `output_filename` is not provided, a timestamp-based name is used.
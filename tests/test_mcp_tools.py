# tests/test_mcp_tools.py
import pytest
import os
import sqlite3
import sys
import tempfile
# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.entry import execute_query, get_item, get_all_items, get_all_tables
from src.entry import update_item, delete_item, create_item, extract_to_json
from src.entry import create_table, alter_table, drop_table, backup_database, get_db_version

@pytest.fixture
def test_db():
    """Create a temporary test database with sample data"""
    # Create a temporary file for the test database
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    
    # Connect to the database and create test schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a test table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        age INTEGER
    )
    ''')
    
    # Insert test data
    test_data = [
        (1, 'Alice', 'alice@example.com', 30),
        (2, 'Bob', 'bob@example.com', 25),
        (3, 'Charlie', 'charlie@example.com', 35)
    ]
    cursor.executemany('INSERT INTO users VALUES (?, ?, ?, ?)', test_data)
    
    # Create another test table
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')
    
    # Insert product data
    product_data = [
        (1, 'Laptop', 999.99),
        (2, 'Phone', 499.99)
    ]
    cursor.executemany('INSERT INTO products VALUES (?, ?, ?)', product_data)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    # Patch the DB_NAME variable in the module
    import src.entry
    original_db = src.entry.DB_NAME
    src.entry.DB_NAME = db_path
    
    yield db_path
    
    # Clean up
    src.entry.DB_NAME = original_db
    os.unlink(db_path)


def test_execute_query(test_db):
    # Test SELECT query
    result = execute_query("SELECT * FROM users WHERE id = 1")
    assert result["success"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["name"] == "Alice"
    
    # Test parameterized query
    result = execute_query("SELECT * FROM users WHERE name = ?", ("Bob", ))
    assert result["success"] is True
    assert result["results"][0]["email"] == "bob@example.com"
    
    # Test non-SELECT query (INSERT)
    result = execute_query("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", 
                           ("Dave", "dave@example.com", 40))
    assert result["success"] is True
    
    # Verify insertion worked
    result = execute_query("SELECT * FROM users WHERE name = 'Dave'")
    assert result["success"] is True
    assert len(result["results"]) == 1
    
    # Test error handling with invalid query
    result = execute_query("SELECT * FROM nonexistent_table")
    assert result["success"] is False
    assert "error" in result


def test_get_item_by_id(test_db):
    # Test valid ID
    result = get_item("users", "1", "id")
    assert result["success"] is True
    assert result["results"][0]["name"] == "Alice"
    
    # Test non-existent ID
    result = get_item("users", "999", "id")
    assert result["success"] is True
    assert len(result["results"]) == 0


def test_get_item_by_name(test_db):
    # Test valid name
    result = get_item("users", "Bob", "name")
    assert result["success"] is True
    assert result["results"][0]["id"] == 2
    
    # Test with non-default column name
    result = get_item("products", "Laptop", "name")
    assert result["success"] is True
    assert result["results"][0]["price"] == 999.99
    
    # Test non-existent name
    result = get_item("users", "NonExistent", "name")
    assert result["success"] is True
    assert len(result["results"]) == 0


def test_get_all_items(test_db):
    # Test users table
    result = get_all_items("users")
    assert result["success"] is True
    assert len(result["results"]) >= 3  # At least the 3 we inserted
    
    # Test products table
    result = get_all_items("products")
    assert result["success"] is True
    assert len(result["results"]) == 2


def test_get_all_tables(test_db):
    result = get_all_tables()
    assert result["success"] is True
    # The test database should contain the users and products tables
    tables = [row["name"] for row in result["results"]]
    assert "users" in tables
    assert "products" in tables


def test_update_item(test_db):
    # Update a user's age
    update_data = {"age": 31}
    result = update_item("users", 1, update_data, "id")
    assert result["success"] is True
    
    # Verify update worked
    check_result = get_item("users", "1", "id")
    assert check_result["results"][0]["age"] == 31
    
    # Test updating multiple fields
    update_data = {"name": "Alice Smith", "email": "alice.smith@example.com"}
    result = update_item("users", 1, update_data, "id")
    assert result["success"] is True
    
    # Verify updates
    check_result = get_item("users", "1", "id")
    assert check_result["results"][0]["name"] == "Alice Smith"
    assert check_result["results"][0]["email"] == "alice.smith@example.com"


def test_delete_item(test_db):
    # First verify item exists
    result = get_item("users", "3", "id")
    assert len(result["results"]) == 1
    
    # Delete the item
    delete_result = delete_item("users", 3, "id")
    assert delete_result["success"] is True
    
    # Verify deletion worked
    result = get_item("users", "3", "id")
    assert len(result["results"]) == 0


def test_create_item(test_db):
    # Create a new user
    user_id = 10
    new_user = {
        "id": user_id,
        "name": "Eve",
        "email": "eve@example.com",
        "age": 28
    }
    
    result = create_item("users", new_user)
    assert result["success"] is True
    assert "id" in result
    check_result = get_item("users", str(user_id), "id")
    assert check_result["results"][0]["name"] == "Eve"
    assert check_result["results"][0]["email"] == "eve@example.com"
    
    # Create a new product
    new_product = {
        "name": "Tablet",
        "price": 299.99
    }
    
    result = create_item("products", new_product)
    assert result["success"] is True
    assert "id" in result

def test_create_table(test_db):
    # Define table schema
    columns = {
        "id": {"type": "INTEGER", "primary_key": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "price": {"type": "REAL", "default": 0.0}
    }
    
    # Create table
    result = create_table("new_table", columns)
    assert result["success"] is True
    assert "message" in result

    # Verify table creation
    tables = get_all_tables()
    table_names = [row["name"] for row in tables["results"]]
    assert "new_table" in table_names


def test_alter_table(test_db):
    # Add a new column
    result = alter_table("users", "add_column", column_name="phone", column_type="TEXT")
    assert result["success"] is True

    # Verify column addition
    query = "PRAGMA table_info(users);"
    result = execute_query(query)
    columns = [col["name"] for col in result["results"]]
    assert "phone" in columns


def test_drop_table(test_db):
    # Drop the products table
    result = drop_table("products")
    assert result["success"] is True

    # Verify table deletion
    tables = get_all_tables()
    table_names = [row["name"] for row in tables["results"]]
    assert "products" not in table_names


def test_backup_database(test_db):
    # Create a backup
    result = backup_database("test_backup.db")
    assert result["success"] is True
    assert "message" in result

    # Verify backup file exists
    backup_path = os.path.join(os.path.dirname(test_db), "test_backup.db")
    assert os.path.exists(backup_path)

    # Clean up backup file
    os.remove(backup_path)


def test_extract_to_json(test_db):
    # Extract users table to JSON
    result = extract_to_json("users", "users_data.json")
    assert result["success"] is True
    assert "message" in result

    # Verify JSON file exists in the database directory
    db_dir = os.path.dirname(test_db)
    json_path = os.path.join(db_dir, "users_data.json")
    assert os.path.exists(json_path)

    # Clean up JSON file
    os.remove(json_path)


def test_extract_to_json_path_traversal(test_db):
    # Attempt path traversal — file should still land in the db directory
    result = extract_to_json("users", "../../../../tmp/evil")
    assert result["success"] is True

    db_dir = os.path.dirname(test_db)
    safe_path = os.path.join(db_dir, "evil.json")
    assert os.path.exists(safe_path)
    assert not os.path.exists(os.path.join("/tmp", "evil.json"))

    os.remove(safe_path)


def test_extract_to_json_invalid_table_name(test_db):
    # SQL injection attempt via table_name
    result = extract_to_json("users; DROP TABLE users;--")
    assert result["success"] is False
    assert "Invalid table name" in result["error"]


def test_backup_database_path_traversal(test_db):
    # Attempt path traversal — backup should stay in db directory
    result = backup_database("../../evil_backup.db")
    assert result["success"] is True

    db_dir = os.path.dirname(test_db)
    safe_path = os.path.join(db_dir, "evil_backup.db")
    assert os.path.exists(safe_path)

    os.remove(safe_path)

def test_alter_table(test_db):
    # Add a new column
    result = alter_table("users", "add_column", column_name="phone", column_type="TEXT")
    assert result["success"] is True
    assert "message" in result

    # Verify column addition using PRAGMA table_info
    query = "PRAGMA table_info(users);"
    pragma_result = execute_query(query)
    
    # Ensure the query returned results
    assert pragma_result["success"] is True

def test_get_db_version(test_db):
    # Get database version
    result = get_db_version()
    assert result["success"] is True
    assert "results" in result
    assert "sqlite_version()" in result["results"][0]
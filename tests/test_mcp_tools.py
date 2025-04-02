# tests/test_mcp_tools.py
import pytest
import os
import sqlite3
import sys
import tempfile
# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.entry import execute_query, get_item, get_all_items, get_all_tables
from src.entry import update_item, delete_item, create_item

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
import sqlite3
import os

DB_PATH = "pragyanai_silicon.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables for Groups, IP Models, and Document Registries if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table for Protocol Groups and IP Models
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            ip_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for Added Documents and Metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_name TEXT NOT NULL,
            source_name TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            brief_summary TEXT,
            FOREIGN KEY (ip_name) REFERENCES ip_registry (ip_name) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def db_add_ip(group_name: str, ip_name: str):
    """Inserts or verifies an IP model under a protocol group in SQLite."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO ip_registry (group_name, ip_name) VALUES (?, ?)",
            (group_name, ip_name)
        )
        conn.commit()
    except Exception as e:
        print(f"Database Error adding IP: {e}")
    finally:
        conn.close()

def db_add_document(ip_name: str, source_name: str, doc_type: str, page_count: int, brief: str):
    """Records an added document into the SQLite database."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO document_registry (ip_name, source_name, doc_type, page_count, brief_summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ip_name, source_name, doc_type, page_count, brief)
        )
        conn.commit()
    except Exception as e:
        print(f"Database Error adding document: {e}")
    finally:
        conn.close()

def db_remove_document(ip_name: str, source_name: str):
    """Removes a document record from SQLite."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM document_registry WHERE ip_name = ? AND source_name = ?",
            (ip_name, source_name)
        )
        conn.commit()
    except Exception as e:
        print(f"Database Error removing document: {e}")
    finally:
        conn.close()

def db_get_all_groups_and_ips():
    """Retrieves all stored groups and their corresponding IP models as a dictionary {ip_name: group_name}."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_name, ip_name FROM ip_registry")
    rows = cursor.fetchall()
    conn.close()
    
    ip_groups = {}
    for row in rows:
        ip_groups[row["ip_name"]] = row["group_name"]
    return ip_groups

def db_get_file_registry(ip_name: str):
    """Retrieves all document records for a given IP model."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT source_name, doc_type, page_count, brief_summary FROM document_registry WHERE ip_name = ?", (ip_name,))
    rows = cursor.fetchall()
    conn.close()
    
    registry = {}
    for row in rows:
        registry[row["source_name"]] = {
            "type": row["doc_type"],
            "pages": row["page_count"],
            "brief": row["brief_summary"]
        }
    return registry

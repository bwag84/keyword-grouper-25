import sqlite3
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib # To hash the prompt for consistency check

load_dotenv()
DB_NAME = os.getenv("DATABASE_NAME", "keyword_groups.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

def init_db():
    """Initializes the database table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            language TEXT NOT NULL,
            prompt_hash TEXT NOT NULL, -- Store hash of the prompt used for grouping
            main_cat TEXT NOT NULL,
            sub_cat_1 TEXT NOT NULL,
            sub_cat_2 TEXT NOT NULL,
            semantic_theme TEXT NOT NULL,
            date_added TEXT NOT NULL,
            UNIQUE(keyword, language, prompt_hash) -- Ensure reliability for a given prompt
        )
    ''')
    conn.commit()
    conn.close()

def get_prompt_hash(prompt_text):
    """Generates a SHA-256 hash of the prompt text."""
    return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()

def get_existing_grouping(keyword, language, prompt_text):
    """Checks if a keyword grouping exists for the given keyword, lang, and prompt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    prompt_hash = get_prompt_hash(prompt_text)
    cursor.execute(
        "SELECT main_cat, sub_cat_1, sub_cat_2, semantic_theme FROM keyword_groups WHERE keyword = ? AND language = ? AND prompt_hash = ?",
        (keyword, language, prompt_hash)
    )
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def add_keyword_grouping(keyword, language, prompt_text, main_cat, sub_cat_1, sub_cat_2, semantic_theme):
    """Adds a new keyword grouping to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt_hash = get_prompt_hash(prompt_text)
    try:
        cursor.execute('''
            INSERT INTO keyword_groups (keyword, language, prompt_hash, main_cat, sub_cat_1, sub_cat_2, semantic_theme, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (keyword, language, prompt_hash, main_cat, sub_cat_1, sub_cat_2, semantic_theme, date_added))
        conn.commit()
    except sqlite3.IntegrityError:
        # Keyword with this language and prompt hash already exists, handle if necessary (e.g., log it)
        print(f"Warning: Attempted to add duplicate entry for Keyword: {keyword}, Lang: {language}, Prompt Hash: {prompt_hash[:8]}...")
        pass # Or update if needed, but INSERT OR IGNORE/REPLACE might be better
    finally:
        conn.close()

def get_all_data():
    """Retrieves all data from the database."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT main_cat, sub_cat_1, sub_cat_2, keyword, language, semantic_theme, date_added FROM keyword_groups ORDER BY date_added DESC", conn)
    conn.close()
    return df

# Initialize the database when this module is imported
init_db()
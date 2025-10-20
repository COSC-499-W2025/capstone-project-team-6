import sqlite3

DB_NAME = "myapp.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("SQLite setup complete!!!!!!!")

# makes sure you only create the database when you exectute the script and not when you import it
if __name__ == "__main__":
    create_database()
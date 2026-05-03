import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

conn.commit()
conn.close()

print("Admins table created successfully")
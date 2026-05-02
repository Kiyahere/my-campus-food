import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

# create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# clear old data (important)
cursor.execute("DELETE FROM admins")

# insert clean admin
cursor.execute("""
INSERT INTO admins (username, password)
VALUES (?, ?)
""", ("FoodApp@2026", generate_password_hash("1234")))

conn.commit()
conn.close()

print("Admins reset successfully")
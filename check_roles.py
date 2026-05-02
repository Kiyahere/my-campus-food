import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

rows = cursor.execute("SELECT username, role FROM admins").fetchall()

for row in rows:
    print(row)

conn.close()
import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

print("VENDORS:", cursor.execute("SELECT * FROM vendors").fetchall())
print("RIDERS:", cursor.execute("SELECT * FROM riders").fetchall())

conn.close()
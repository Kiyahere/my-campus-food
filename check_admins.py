import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM admins")
print(cursor.fetchall())

conn.close()
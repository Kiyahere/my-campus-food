import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO admins (username, password)
VALUES (?, ?)
""", ("FoodApp@2026", "1234"))

conn.commit()
conn.close()

print("Admin added successfully")
import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

cursor.execute("""
DELETE FROM admins 
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM admins
    GROUP BY username
)
""")

conn.commit()
conn.close()

print("Duplicates removed")
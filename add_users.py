import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

# Add vendor
cursor.execute("INSERT INTO vendors (username, password) VALUES (?, ?)", ("vendor1", "1234"))

# Add rider
cursor.execute("INSERT INTO riders (username, password) VALUES (?, ?)", ("rider1", "1234"))

conn.commit()
conn.close()

print("Vendor and Rider added!")
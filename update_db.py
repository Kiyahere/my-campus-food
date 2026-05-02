import sqlite3

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

# Add order reference column
try:
    cursor.execute("ALTER TABLE orders ADD COLUMN reference TEXT")
except:
    pass

# Add user role column
try:
    cursor.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'admin'")
except:
    pass

conn.commit()
conn.close()

print("Database updated successfully")
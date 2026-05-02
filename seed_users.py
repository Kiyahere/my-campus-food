import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("foods.db")
cursor = conn.cursor()

# Admin
cursor.execute(
    "INSERT INTO admins (username, password, role) VALUES (?, ?, ?)",
    ("FoodApp@2026", generate_password_hash("1234"), "admin")
)

# Vendor
cursor.execute(
    "INSERT INTO admins (username, password, role) VALUES (?, ?, ?)",
    ("vendor1", generate_password_hash("1234"), "vendor")
)

# Rider
cursor.execute(
    "INSERT INTO admins (username, password, role) VALUES (?, ?, ?)",
    ("rider1", generate_password_hash("1234"), "rider")
)

conn.commit()
conn.close()

print("Users created successfully")
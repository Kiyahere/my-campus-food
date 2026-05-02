from app import get_db
from werkzeug.security import generate_password_hash

conn = get_db()
cursor = conn.cursor()

cursor.execute("DELETE FROM admins")

cursor.executemany(
    "INSERT INTO admins (username, password) VALUES (?, ?)",
    [
        ("FoodApp@2026", generate_password_hash("AdminOne@2026")),
        ("CampusFood@2026", generate_password_hash("AdminTwo@2026"))
    ]
)

conn.commit()
conn.close()

print("Admins reset.")
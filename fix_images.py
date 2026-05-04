from app import get_db   # make sure app.py has get_db()

conn = get_db()
conn.execute("UPDATE foods SET image = REPLACE(image, 'static/uploads/', '')")
conn.commit()
conn.close()

print("Images fixed successfully")
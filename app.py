from supabase import create_client
import os
import uuid
import sqlite3
import requests
from functools import wraps

from flask import Flask, render_template, render_template_string, request, redirect, session, url_for
render_template_string
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

SUPABASE_URL = os.getenv("https://iieupxswfvxmmcjqzdml.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpZXVweHN3ZnZ4bW1janF6ZG1sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwOTg0ODIsImV4cCI6MjA5MzY3NDQ4Mn0.90CwhwMvmO-3xKK_wKaGyUx3OyLq-xX2AWpVTdas4Z4")

app = Flask(__name__)
app.secret_key = "secret123"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

HTML = """
<h2>Supabase Upload Test</h2>
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="file">
  <button type="submit">Upload</button>
</form>

{% if url %}
<p>Uploaded successfully!</p>
<p><a href="{{ url }}" target="_blank">View File</a></p>
{% endif %}
"""

@app.route("/test-upload", methods=["GET", "POST"])
def test_upload():
    url = None

    if request.method == "POST":
        file = request.files.get("file")

        if file:
            filename = str(uuid.uuid4()) + file.filename
            file_bytes = file.read()

            supabase.storage.from_("food-images").upload(
                filename,
                file_bytes
            )

            url = supabase.storage.from_("food-images").get_public_url(filename)

    return render_template_string(HTML, url=url)


print(f"URL: {SUPABASE_URL}")
print("KEY:", SUPABASE_KEY[:10] if SUPABASE_KEY else None)

@app.route('/')
def index():
    return render_template("index.html")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper

PAYSTACK_SECRET = "sk_test_de9b43e65653c097853fad214e5713d7aa7a9b02"

def get_db():
    conn = sqlite3.connect("foods.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("foods.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            image TEXT
        )
    """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE,
                   password TEXT
                   )
                   """)
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    vendor TEXT,
    rider TEXT,
    items TEXT,
    total INTEGER,
    status TEXT DEFAULT 'Pending'
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")


    conn.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")


    cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_type TEXT,          -- admin, vendor, rider
    message TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS riders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""") 
    
    conn.execute("UPDATE foods SET image = REPLACE(image, 'static/uploads/', '')")
    conn.execute("UPDATE foods SET image = REPLACE(image, '/static/uploads/', '')")


    
    conn.commit()
    conn.close()


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":

        conn = get_db()

        username = request.form.get("username")
        password = request.form.get("password")

        admin = conn.execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if admin and admin["password"] == password:
            session["admin"] = username
            return redirect("/admin_dashboard")
        else:
            return "Invalid credentials"

    return render_template("admin_login.html")


    print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY loaded:", bool(SUPABASE_KEY))


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/test")
def test():
    return "Working"

@app.route("/admin_login")
def admin_login_test():
    return "Admin route exists"


@app.route('/create_admins')
def create_admins():
    conn = get_db()
    conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("FoodApp@2026", "1234"))
    conn.commit()
    conn.close()
    return "Admins created!"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            supabase.table("users").insert({
                "username": username,
                "password": password
            }).execute()
        except Exception as e:
            return f"Error: {str(e)}"

        return redirect("/login")

    return render_template("signup.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            response = supabase.table("users") \
                .select("*") \
                .eq("username", username) \
                .eq("password", password) \
                .execute()

            user = response.data

            if user and len(user) > 0:
                session["user"] = username
                return redirect("/menu")
            else:
                return "Invalid login"

        except Exception as e:
            return f"Login error: {str(e)}"

    return render_template("login.html")


# ---------------- MENU ----------------

@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    foods = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()

    return render_template("menu.html", foods=foods)


@app.route('/create_admin')
def create_admin():
    conn = get_db()
    conn.execute(
        "INSERT INTO admins (username, password) VALUES (?, ?)",
        ("FoodApp@2026", "1234")
        )
    conn.commit()
    conn.close()
    return "Admin created"



@app.route('/check-admins')
def check_admins():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, password FROM admins")
    admins = cursor.fetchall()

    conn.close()

    return render_template("debug.html", admins=admins)

@app.route("/test_admins")
def test_admins():
    conn = get_db()
    data = conn.execute("SELECT * FROM admins").fetchall()
    conn.close()

    print(data)
    return str(data)   



# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")



@app.route('/pay')
def pay():
    cart = session.get('cart', [])

    if not cart:
        return "Cart is empty"

    total = sum(item['price'] for item in cart)

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    data = {
        "email": session["user_email"],
        "amount": total * 100
    }

    response = requests.post(url, json=data, headers=headers)
    res = response.json()

    reference = request.args.get("reference")

    print(res)  # DEBUG

    if res.get("status") and res["data"]["authorization_url"]:
        return redirect(res["data"]["authorization_url"])
    else:
        return f"Payment failed: {res}"
    

@app.route("/verify_payment")
def verify_payment():
    reference = request.args.get("reference")

    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}"
    }
    data = response.json()
    if data["data"]["status"] == "success":
        conn = get_db
        
    response = requests.get(url, headers=headers)
    res = response.json()
    reference = request.args.get("reference")

    print(res)

    conn = get_db()
    if res["data"]["status"] == "success":
        order_id = request.args.get("order_id")
        if order_id:
            conn.execute(
                "UPDATE orders SET status = 'Paid' WHERE id = ?",
                (order_id,)
            )
            conn.commit()
        conn.close()
        session["cart"] = []  # clear cart
        return  redirect("/payment-success")
    else:
        return "Payment Failed"   
    

# ---------------- ADD FOOD ----------------
@app.route("/add_food", methods=["GET", "POST"])
def add_food():

    if "admin" not in session:
        return redirect("/admin_login")

    if request.method == "GET":
        return render_template("add_food.html")

    name = request.form.get("name")
    price = request.form.get("price")
    file = request.files.get("image")

    if not name or not price:
        return "Missing name or price"

    if not file or file.filename == "":
        return "No image selected"

    filename = file.filename

    # Read image once
    file_bytes = file.read()

    # Upload to Supabase Storage
    supabase.storage.from_("food-images").upload(
        filename,
        file_bytes,
        {"content-type": file.content_type}
    )

    # Get public URL
    image_url = supabase.storage.from_("food-images").get_public_url(filename)

    # Save into Supabase database
    supabase.table("foods").insert({
        "name": name,
        "price": int(price),
        "image": image_url
    }).execute()

    return redirect("/admin_dashboard")



@app.route("/view_foods")
def view_foods():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    foods = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()

    return render_template("view_foods.html", foods=foods)



@app.route("/delete_food/<int:id>")
def delete_food(id):
    if "admin" not in session:
        return redirect(url_for("/admin_login"))

    conn = get_db()
    conn.execute("DELETE FROM foods WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/view_orders")
def view_orders():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()

    return render_template("view_orders.html", orders=orders)


@app.route("/rider_dashboard")
def rider_dashboard():
    if "rider" not in session:
        return redirect("/rider_login")

    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE rider = ?",
        (session["rider"],)
    ).fetchall()
    conn.close()

    return render_template("rider_dashboard.html", orders=orders)


@app.route("/check-db")
def check_db():
    conn = get_db()
    data = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()
    return str(data)


@app.route("/test-db")
def test_db():
    conn = get_db()
    data = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()
    return str(data)

@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):
    conn = get_db()
    food = conn.execute("SELECT * FROM foods WHERE id=?", (id,)).fetchone()
    conn.close()

    if food:
        cart = session.get("cart", [])
        cart.append({
            "id": food["id"],
            "name": food["name"],
            "price": food["price"]
        })
        session["cart"] = cart

    return redirect("/menu")

@app.route("/vendor_dashboard")
def vendor_dashboard():
    if "vendor" not in session:
        return redirect("/vendor_login")

    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE vendor = ?",
        (session["vendor"],)
    ).fetchall()
    conn.close()

    return render_template("vendor_dashboard.html", orders=orders)


@app.route("/update_status", methods=["POST"])
def update_status():
    order_id = request.form["order_id"]
    status = request.form["status"]

    conn = get_db()
    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )
    conn.commit()
    conn.close()

    return redirect("/vendor_dashboard")

@app.route("/deliver_order", methods=["POST"])
def deliver_order():
    order_id = request.form["order_id"]

    conn = get_db()
    conn.execute(
        "UPDATE orders SET status='Delivered' WHERE id=?",
        (order_id,)
    )
    conn.commit()
    conn.close()

    return redirect("/rider_dashboard")

@app.route("/assign_rider", methods=["POST"])
def assign_rider():
    order_id = request.form["order_id"]
    rider = request.form["rider"]

    conn = get_db()
    conn.execute(
        "UPDATE orders SET rider=?, status='Assigned' WHERE id=?",
        (rider, order_id)
    )
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")



@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect("/login")

    cart = session.get("cart", [])

    if not cart:
        return "Cart is empty"

    total = sum(item["price"] for item in cart)
    user = session["user"]

    conn = get_db()
    conn.execute(
        "INSERT INTO orders (user, items, total, status) VALUES (?, ?, ?, ?)",
        (user, str(cart), total, "Pending")
    )
    conn.commit()
    conn.close()

    session.pop("cart", None)

    return redirect("/orders")


@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user=?",
        (user,)
    ).fetchall()
    conn.close()

    return render_template("orders.html", orders=orders)


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route('/admin/foods')
def admin_foods():
    conn = get_db()
    foods = conn.execute("SELECT * FROM foods").fetchall()

    print(foods)
    return render_template("admin_foods.html", foods=foods)


@app.route("/update_order/<int:id>")
def update_order(id):
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    conn.execute(
        "UPDATE orders SET status = 'Delivered' WHERE id = ?",
        (id,)
    )
    conn.commit()
    conn.close()

    return redirect("/view_orders")


@app.route("/vendor_login", methods=["GET", "POST"])
def vendor_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        vendor = conn.execute(
            "SELECT * FROM vendors WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if vendor:
            session["vendor"] = username
            return redirect("/vendor_dashboard")
        else:
            return "Invalid vendor login"

    return render_template("vendor_login.html")


@app.route("/rider_login", methods=["GET", "POST"])
def rider_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        rider = conn.execute(
            "SELECT * FROM riders WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if rider:
            session["rider"] = username
            return redirect("/rider_dashboard")
        else:
            return "Invalid rider login"

    return render_template("rider_login.html")



# ---------------- LOGOUT ----------------


@app.route("/adminlogout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- RUN APP ----------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
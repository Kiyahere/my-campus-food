from unittest import result
from supabase import create_client
import os
import uuid
import sqlite3
import requests
from functools import wraps
import bcrypt

from flask import Flask, render_template, request,render_template_string, redirect, session, url_for
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

load_dotenv(dotenv_path=".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_KEY environment variable")
if not SUPABASE_URL:
 raise Exception("Missing SUPABASE_URL environment variable")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


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


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test")
def test():
    return "Working"



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
        email = request.form["email"]
        password = request.form["password"]

        if not username or not email or not password:
            return "All fields are required", 400


        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        result =  supabase.table("users").insert({
                "username": username,
                "email": email,
                "password": hashed_password
            }).execute()
        print("SUPABASE RESULT:", result)
        
        return redirect("/login")

    return render_template("signup.html")

    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = supabase.table("users") \
            .select("*") \
            .eq("username", username) \
            .execute()
        
        if user.data: stored_hash = user.data[0]
        ["password"]
            
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')): 
        
            session["user"] = user.data[0]["username"]
            session["email"] = user.data[0]["email"]

            return redirect("/dashboard")
        
        else: return "Invalid username or password"

    return render_template("login.html")


# ---------------- MENU ----------------

@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/login")

    foods = supabase.table("foods").select("*").execute().data

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
    

    foods = supabase.table("foods").select("*").execute().data

    return render_template("admin_dashboard.html", foods=foods)
    

@app.route('/pay')
def pay():
    cart = session.get('cart', [])

    if not cart:
        return "Cart is empty"

    email = session.get("user_email")

    print("EMAIL:", email)

    if not email:
        return "User email not found. Please login again."

    total = sum(int(item['price']) for item in cart)

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    data = {
        "email": email,
        "amount": total * 100,
        "callback_url": "https://my_campus_food.onrender.com/verify_payment"
    }

    response = requests.post(url, json=data, headers=headers)
    res = response.json()

    print(res)

    if res.get("status"):
        return redirect(res["data"]["authorization_url"])

    return f"Payment failed: {res}"


@app.route("/verify_payment")
def verify_payment():
    reference = request.args.get("reference")

    if not reference:
        return "No reference found"

    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}"
    }

    response = requests.get(url, headers=headers)
    res = response.json()

    print(res)

    if res.get("data") and res["data"]["status"] == "success":
        session["cart"] = []  # clear cart

        return redirect("/payment-success")

    return "Payment Failed"


# ---------------- ADD FOOD ----------------
@app.route("/add_food", methods=["GET", "POST"])
def add_food():

    if request.method == "POST":

        try:
            name = request.form.get("name")
            price = request.form.get("price")

            image_file = request.files.get("image")

            image_url = ""

            if image_file:

                filename = secure_filename(image_file.filename)

                file_bytes = image_file.read()

                supabase.storage.from_("food-images").upload(
                    filename,
                    file_bytes
                )

                image_url = f"{SUPABASE_URL}/storage/v1/object/public/food-images/{filename}"

            data = {
                "name": name,
                "price": price,
                "image": image_url
            }

            supabase.table("foods").insert(data).execute()

            return redirect(url_for("admin_dashboard"))

        except Exception as e:
            return f"ERROR: {e}"

    return render_template("add_food.html")


@app.route("/delete-food/<id>", methods=["POST"])
def delete_food(id):
    try:
        supabase.table("foods").delete().eq("id", id).execute()
        return redirect(url_for("admin_dashboard"))

    except Exception as e:
        return f"ERROR: {e}"



@app.route("/place-order", methods=["POST"])
def place_order():

    items = request.form.get("items")
    total = request.form.get("total")

    supabase.table("orders").insert({
        "items": items,
        "total": total,
        "status": "Pending",
        "rider": None
    }).execute()

    return redirect("/menu")



@app.route("/view_orders")
def view_orders():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()

    return render_template("view_orders.html", orders=orders)


@app.route("/assign_rider/<order_id>", methods=["POST"])
def assign_rider(order_id):

    rider = request.form.get("rider")

    supabase.table("orders").update({
        "rider": rider,
        "status": "Assigned"
    }).eq("id", order_id).execute()

    return redirect("/view_orders")


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


@app.route("/add-to-cart/<id>")
def add_to_cart(id):
    if "user" not in session:
        return redirect("/login")

    response = supabase.table("foods").select("*").eq("id", id).execute()
    food = response.data[0] if response.data else None

    if food:
        cart = session.get("cart", [])

        cart.append({
            "id": food["id"],
            "name": food["name"],
            "price": food["price"]
        })

        session["cart"] = cart
        session.modified = True

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

@app.route('/admin_foods')
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
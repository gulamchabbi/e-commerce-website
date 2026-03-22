from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import os

app = Flask(__name__)

# ---------- DATABASE ----------
DB_NAME = "store.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER, category TEXT, image TEXT)''')
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("Laptop", 50000, 10, "Electronics", "laptop.jpg"),
            ("Phone", 20000, 15, "Electronics", "phone.jpg"),
            ("Headphones", 2000, 30, "Electronics", "headphones.jpg"),
            ("Shoes", 3000, 20, "Fashion", "shoes.jpg"),
            ("Watch", 1500, 25, "Fashion", "watch.jpg"),
            ("Backpack", 1200, 18, "Accessories", "backpack.jpg"),
            ("Keyboard", 2500, 12, "Electronics", "keyboard.jpg")
        ]
        c.executemany("INSERT INTO products (name, price, stock, category, image) VALUES (?, ?, ?, ?, ?)", products)
    conn.commit()
    conn.close()

# ---------- AI PRICING ----------
def dynamic_price(price, stock):
    demand = random.randint(50, 100)
    if demand > 80:
        price *= 1.25
    if stock < 10:
        price *= 1.3
    return round(price, 2)

# ---------- AI RECOMMEND ----------
def recommend_products(category, current_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category=? AND id!=?", (category, current_id))
    same_cat = c.fetchall()
    if len(same_cat) < 3:
        c.execute("SELECT * FROM products WHERE id!=?", (current_id,))
        same_cat = c.fetchall()
    conn.close()
    return random.sample(same_cat, min(3, len(same_cat)))

# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products():
    search = request.args.get("search", "")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if search:
        c.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM products")
    items = c.fetchall()
    conn.close()
    return render_template("products.html", products=items, dynamic_price=dynamic_price)

@app.route("/buy/<int:pid>")
def buy(pid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (pid,))
    product = c.fetchone()
    if not product:
        conn.close()
        return "Product not found"
    stock = product[3]
    category = product[4]
    if stock > 0:
        c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (pid,))
        conn.commit()
        message = "✅ Order Successful!"
    else:
        message = "❌ Sorry, Out of Stock"
    conn.close()
    recs = recommend_products(category, pid)
    return render_template("cart.html", product=product, message=message, recs=recs, dynamic_price=dynamic_price)

# ---------- RUN ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
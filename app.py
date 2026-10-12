import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-only-change-me")

def db():
    return mysql.connector.connect(**DB_CONFIG)

def admin_only():
    return session.get("role") == "admin"

@app.context_processor
def common():
    cart = session.get("cart", {})
    return {"cart_count": sum(cart.values())}

@app.route("/")
def home():
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM medicines ORDER BY id DESC LIMIT 6")
    products=cur.fetchall()
    cur.close(); conn.close()
    return render_template("index.html", products=products)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=generate_password_hash(request.form["password"])
        conn=db(); cur=conn.cursor()
        try:
            cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                        (name,email,password))
            conn.commit(); flash("Account created successfully.","success")
            return redirect(url_for("login"))
        except mysql.connector.Error:
            conn.rollback(); flash("Email already exists.","danger")
        finally:
            cur.close(); conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        conn=db(); cur=conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user=cur.fetchone(); cur.close(); conn.close()
        if user and check_password_hash(user["password"],password):
            session.update(user_id=user["id"],name=user["name"],role=user["role"])
            return redirect(url_for("admin_dashboard" if user["role"]=="admin" else "home"))
        flash("Invalid email or password.","danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/doctors")
def doctors():
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM doctors ORDER BY name")
    data=cur.fetchall(); cur.close(); conn.close()
    return render_template("doctors.html",doctors=data)

@app.route("/medicines")
def medicines():
    q=request.args.get("q","").strip()
    category=request.args.get("category","").strip()
    conn=db(); cur=conn.cursor(dictionary=True)
    sql="SELECT * FROM medicines WHERE 1=1"; params=[]
    if q:
        sql+=" AND (name LIKE %s OR description LIKE %s)"
        params += [f"%{q}%",f"%{q}%"]
    if category:
        sql+=" AND category=%s"; params.append(category)
    sql+=" ORDER BY id DESC"
    cur.execute(sql,params); products=cur.fetchall()
    cur.execute("SELECT DISTINCT category FROM medicines ORDER BY category")
    cats=[x["category"] for x in cur.fetchall()]
    cur.close(); conn.close()
    return render_template("medicines.html",products=products,categories=cats,q=q,category=category)

@app.route("/medicine/<int:id>")
def medicine_detail(id):
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM medicines WHERE id=%s",(id,))
    product=cur.fetchone(); cur.close(); conn.close()
    if not product: return redirect(url_for("medicines"))
    return render_template("medicine_detail.html",product=product)

@app.route("/cart/add/<int:id>")
def cart_add(id):
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM medicines WHERE id=%s",(id,))
    product=cur.fetchone(); cur.close(); conn.close()
    if not product or product["stock"]<1:
        flash("Product is out of stock.","danger"); return redirect(url_for("medicines"))
    cart=session.get("cart",{})
    key=str(id); qty=int(request.args.get("qty",1))
    cart[key]=min(cart.get(key,0)+max(qty,1),product["stock"])
    session["cart"]=cart
    flash("Product added to cart.","success")
    return redirect(request.referrer or url_for("medicines"))

@app.route("/cart")
def cart():
    cart=session.get("cart",{}); items=[]; total=0
    if cart:
        conn=db(); cur=conn.cursor(dictionary=True)
        ids=list(map(int,cart.keys()))
        marks=",".join(["%s"]*len(ids))
        cur.execute(f"SELECT * FROM medicines WHERE id IN ({marks})",ids)
        rows=cur.fetchall(); cur.close(); conn.close()
        for p in rows:
            qty=min(cart[str(p["id"])],p["stock"])
            subtotal=float(p["price"])*qty; total+=subtotal
            items.append({"product":p,"qty":qty,"subtotal":subtotal})
    return render_template("cart.html",items=items,total=total)

@app.route("/cart/update",methods=["POST"])
def cart_update():
    cart=session.get("cart",{})
    conn=db(); cur=conn.cursor(dictionary=True)
    for key,value in request.form.items():
        if key.startswith("qty_"):
            pid=key[4:]; qty=max(0,int(value))
            cur.execute("SELECT stock FROM medicines WHERE id=%s",(int(pid),))
            row=cur.fetchone()
            if row: cart[pid]=min(qty,row["stock"])
    cur.close(); conn.close()
    cart={k:v for k,v in cart.items() if v>0}
    session["cart"]=cart
    flash("Cart updated.","success")
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:id>")
def cart_remove(id):
    cart=session.get("cart",{}); cart.pop(str(id),None); session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/checkout",methods=["GET","POST"])
def checkout():
    if "user_id" not in session: return redirect(url_for("login"))
    if not session.get("cart"): return redirect(url_for("cart"))
    cart=session["cart"]; items=[]; total=0
    conn=db(); cur=conn.cursor(dictionary=True)
    for pid,qty in cart.items():
        cur.execute("SELECT * FROM medicines WHERE id=%s",(int(pid),)); p=cur.fetchone()
        if p:
            qty=min(qty,p["stock"]); items.append((p,qty)); total+=float(p["price"])*qty
    if request.method=="POST":
        address=request.form["address"].strip()
        payment=request.form["payment_method"]
        if not address: flash("Address is required.","danger"); return render_template("checkout.html",items=items,total=total)
        try:
            cur.execute("INSERT INTO orders(user_id,total_amount,address,payment_method) VALUES(%s,%s,%s,%s)",
                        (session["user_id"],total,address,payment))
            order_id=cur.lastrowid
            for p,qty in items:
                cur.execute("INSERT INTO order_items(order_id,medicine_id,quantity,price) VALUES(%s,%s,%s,%s)",
                            (order_id,p["id"],qty,p["price"]))
                cur.execute("UPDATE medicines SET stock=stock-%s WHERE id=%s",(qty,p["id"]))
            conn.commit(); session["cart"]={}
            flash(f"Order #{order_id} placed successfully.","success")
            return redirect(url_for("orders"))
        except Exception:
            conn.rollback(); flash("Could not place order.","danger")
    cur.close(); conn.close()
    return render_template("checkout.html",items=items,total=total)

@app.route("/orders")
def orders():
    if "user_id" not in session: return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC",(session["user_id"],))
    data=cur.fetchall(); cur.close(); conn.close()
    return render_template("orders.html",orders=data)

@app.route("/appointment",methods=["GET","POST"])
def appointment():
    if "user_id" not in session: return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    if request.method=="POST":
        cur.execute("""INSERT INTO appointments(user_id,doctor_id,appointment_date,appointment_time,message)
                       VALUES(%s,%s,%s,%s,%s)""",
                    (session["user_id"],request.form["doctor_id"],request.form["date"],
                     request.form["time"],request.form["message"]))
        conn.commit(); flash("Appointment request submitted.","success")
    cur.execute("SELECT * FROM doctors ORDER BY name"); doctors=cur.fetchall()
    cur.close(); conn.close()
    return render_template("appointment.html",doctors=doctors)

@app.route("/admin")
def admin_dashboard():
    if not admin_only(): return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    stats={}
    for key,sql in {
        "patients":"SELECT COUNT(*) n FROM users WHERE role='patient'",
        "doctors":"SELECT COUNT(*) n FROM doctors",
        "medicines":"SELECT COUNT(*) n FROM medicines",
        "orders":"SELECT COUNT(*) n FROM orders"
    }.items():
        cur.execute(sql); stats[key]=cur.fetchone()["n"]
    cur.execute("""SELECT o.*,u.name patient FROM orders o JOIN users u ON o.user_id=u.id
                   ORDER BY o.id DESC LIMIT 10""")
    recent=cur.fetchall(); cur.close(); conn.close()
    return render_template("admin/dashboard.html",stats=stats,recent=recent)

@app.route("/admin/medicines",methods=["GET","POST"])
def admin_medicines():
    if not admin_only(): return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    if request.method=="POST":
        cur.execute("""INSERT INTO medicines(name,category,description,price,stock,image)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (request.form["name"],request.form["category"],request.form["description"],
                     request.form["price"],request.form["stock"],request.form["image"]))
        conn.commit(); flash("Medicine added.","success")
    cur.execute("SELECT * FROM medicines ORDER BY id DESC"); products=cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin/medicines.html",products=products)

@app.route("/admin/medicines/delete/<int:id>")
def admin_medicine_delete(id):
    if not admin_only(): return redirect(url_for("login"))
    conn=db(); cur=conn.cursor()
    cur.execute("DELETE FROM medicines WHERE id=%s",(id,)); conn.commit()
    cur.close(); conn.close(); return redirect(url_for("admin_medicines"))

@app.route("/admin/orders")
def admin_orders():
    if not admin_only(): return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("""SELECT o.*,u.name patient FROM orders o JOIN users u ON o.user_id=u.id
                   ORDER BY o.id DESC""")
    orders=cur.fetchall(); cur.close(); conn.close()
    return render_template("admin/orders.html",orders=orders)

@app.route("/admin/orders/<int:id>/status",methods=["POST"])
def admin_order_status(id):
    if not admin_only(): return redirect(url_for("login"))
    status=request.form["status"]
    conn=db(); cur=conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s",(status,id))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("admin_orders"))

@app.route("/admin/appointments")
def admin_appointments():
    if not admin_only(): return redirect(url_for("login"))
    conn=db(); cur=conn.cursor(dictionary=True)
    cur.execute("""SELECT a.*,u.name patient,d.name doctor FROM appointments a
                   JOIN users u ON a.user_id=u.id JOIN doctors d ON a.doctor_id=d.id
                   ORDER BY a.id DESC""")
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("admin/appointments.html",appointments=rows)

if __name__=="__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

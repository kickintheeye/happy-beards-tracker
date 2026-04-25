from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///orders.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    orders = db.relationship("Order", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), nullable=False)
    customer = db.Column(db.String(100), nullable=False)
    puppy = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    amount_paid = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

with app.app_context():
    db.create_all()
def current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None


def is_logged_in():
    return "user_id" in session


@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))

    orders = Order.query.filter_by(user_id=session["user_id"]).all()
    return render_template("index.html", orders=orders, user=current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. Go back and choose another."

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        else:
            return "Invalid username or password."

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add", methods=["GET", "POST"])
def add_order():
    if not is_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":
        new_order = Order(
            order_id=request.form["order_id"],
            customer=request.form["customer"],
            puppy=request.form["puppy"],
            total_price=int(request.form["total_price"]),
            amount_paid=int(request.form["amount_paid"]),
            user_id=session["user_id"]
        )

        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("add.html")


@app.route("/edit/<int:order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()

    if not order:
        return "Order not found or not authorized."

    if request.method == "POST":
        order.order_id = request.form["order_id"]
        order.customer = request.form["customer"]
        order.puppy = request.form["puppy"]
        order.total_price = int(request.form["total_price"])
        order.amount_paid = int(request.form["amount_paid"])

        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", order=order)


@app.route("/delete/<int:order_id>")
def delete_order(order_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()

    if not order:
        return "Order not found or not authorized."

    db.session.delete(order)
    db.session.commit()
    return redirect(url_for("home"))
@app.route("/api/v1/orders")
def api_all_orders():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    orders = Order.query.filter_by(user_id=session["user_id"]).all()

    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "order_id": order.order_id,
            "customer": order.customer,
            "puppy": order.puppy,
            "total_price": order.total_price,
            "amount_paid": order.amount_paid,
            "user_id": order.user_id
        })

    return jsonify(orders_list)


@app.route("/api/v1/orders/<int:order_id>")
def api_one_order(order_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "id": order.id,
        "order_id": order.order_id,
        "customer": order.customer,
        "puppy": order.puppy,
        "total_price": order.total_price,
        "amount_paid": order.amount_paid,
        "user_id": order.user_id
    })

if __name__ == "__main__":
    app.run()

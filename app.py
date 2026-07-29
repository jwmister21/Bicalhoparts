import os
import secrets
from functools import wraps
from urllib.parse import quote

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, Response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite:///bicalho.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(32)),
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)

db = SQLAlchemy(app)

WHATSAPP_NUMBER = "5511991807768"
WHATSAPP_DISPLAY = "(11) 99180-7768"
INSTAGRAM = "@bicalho_parts"
INSTAGRAM_URL = "https://www.instagram.com/bicalho_parts/"
EMAIL = "Bicalhoparts@gmail.com"

CATEGORIES = [
    "Placas Eletrônicas de Elevadores Multimarcas",
    "Inversores de Comandos Para Elevadores",
    "Corrediças e Roldanas",
    "Diversas Peças Multimarcas",
]

ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp"}


class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mime = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Faça login para acessar o gerenciador.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


def verify_csrf():
    token = request.form.get("_csrf_token", "")
    if not token or not secrets.compare_digest(token, session.get("_csrf_token", "")):
        abort(400, "Token de segurança inválido.")


def create_default_admin():
    email = os.getenv("ADMIN_EMAIL", "admin@bicalho.com.br").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "TroqueEssaSenha123!")
    existing = AdminUser.query.filter_by(email=email).first()
    if not existing:
        db.session.add(
            AdminUser(
                email=email,
                password_hash=generate_password_hash(password),
            )
        )
        db.session.commit()


@app.context_processor
def inject_company():
    return {
        "whatsapp_number": WHATSAPP_NUMBER,
        "whatsapp_display": WHATSAPP_DISPLAY,
        "instagram": INSTAGRAM,
        "instagram_url": INSTAGRAM_URL,
        "company_email": EMAIL,
        "categories": CATEGORIES,
    }


@app.route("/")
def home():
    products = Product.query.filter_by(is_active=True).order_by(Product.id.desc()).all()
    return render_template("index.html", products=products)


@app.route("/produto/<int:product_id>/imagem")
def product_image(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.image_data:
        return redirect(url_for("static", filename="img/sem-foto.svg"))
    return Response(
        product.image_data,
        mimetype=product.image_mime or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.route("/orcamento/<int:product_id>")
def product_quote(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        abort(404)

    message = (
        f"Olá! Tenho interesse no produto: {product.name}. "
        "Gostaria de solicitar um orçamento."
    )
    return redirect(
        f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        verify_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = AdminUser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["admin_id"] = user.id
            session["_csrf_token"] = secrets.token_urlsafe(32)
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do gerenciador.", "success")
    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/dashboard.html", products=products)


def read_product_form(product=None):
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    is_active = request.form.get("is_active") == "on"

    errors = []
    if len(name) < 2:
        errors.append("Informe o nome do produto.")
    if category not in CATEGORIES:
        errors.append("Selecione uma categoria válida.")
    if len(description) < 5:
        errors.append("Informe uma descrição com pelo menos 5 caracteres.")

    image = request.files.get("image")
    image_data = None
    image_mime = None

    if image and image.filename:
        if image.mimetype not in ALLOWED_MIMES:
            errors.append("A imagem deve ser JPG, PNG ou WEBP.")
        else:
            image_data = image.read()
            image_mime = image.mimetype
            if len(image_data) > app.config["MAX_CONTENT_LENGTH"]:
                errors.append("A imagem deve ter no máximo 5 MB.")

    return {
        "name": name,
        "category": category,
        "description": description,
        "is_active": is_active,
        "image_data": image_data,
        "image_mime": image_mime,
        "errors": errors,
    }


@app.route("/admin/produtos/novo", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "POST":
        verify_csrf()
        data = read_product_form()

        if data["errors"]:
            for error in data["errors"]:
                flash(error, "danger")
            return render_template("admin/product_form.html", product=None)

        product = Product(
            name=data["name"],
            category=data["category"],
            description=data["description"],
            is_active=data["is_active"],
            image_data=data["image_data"],
            image_mime=data["image_mime"],
        )
        db.session.add(product)
        db.session.commit()
        flash("Produto cadastrado com sucesso.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/product_form.html", product=None)


@app.route("/admin/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    if request.method == "POST":
        verify_csrf()
        data = read_product_form(product)

        if data["errors"]:
            for error in data["errors"]:
                flash(error, "danger")
            return render_template("admin/product_form.html", product=product)

        product.name = data["name"]
        product.category = data["category"]
        product.description = data["description"]
        product.is_active = data["is_active"]

        if data["image_data"]:
            product.image_data = data["image_data"]
            product.image_mime = data["image_mime"]

        db.session.commit()
        flash("Produto atualizado com sucesso.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/product_form.html", product=product)


@app.route("/admin/produtos/<int:product_id>/excluir", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    verify_csrf()
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    db.session.delete(product)
    db.session.commit()
    flash("Produto excluído.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(413)
def too_large(_error):
    flash("A imagem é muito grande. O limite é 5 MB.", "danger")
    return redirect(request.referrer or url_for("admin_dashboard"))


with app.app_context():
    db.create_all()
    create_default_admin()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )

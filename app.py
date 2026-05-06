import os
import re
import sqlite3

from flask import Flask, redirect, render_template, request, url_for


BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, "contacts.db")


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=DATABASE,
    )

    init_app(app)

    @app.route("/")
    def index():
        search = request.args.get("search", "").strip()
        message = request.args.get("message", "")
        sort = request.args.get("sort", "asc")

        if sort == "desc":
            order_by = "last_name DESC, first_name DESC"
        else:
            sort = "asc"
            order_by = "last_name ASC, first_name ASC"

        conn = get_connection()
        if search:
            contacts = conn.execute(
                "SELECT * FROM contacts "
                "WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? "
                "ORDER BY " + order_by,
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            contacts = conn.execute(
                "SELECT * FROM contacts ORDER BY " + order_by
            ).fetchall()
        conn.close()

        return render_template(
            "index.html",
            contacts=contacts,
            search=search,
            message=message,
            sort=sort,
        )

    @app.route("/contact/<int:contact_id>")
    def contact_detail(contact_id):
        conn = get_connection()
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        conn.close()
        return render_template("detail.html", contact=contact)

    @app.route("/add", methods=["GET", "POST"])
    def add_contact():
        if request.method == "POST":
            first_name = request.form["first_name"].strip()
            last_name = request.form["last_name"].strip()
            phone = request.form["phone"].strip()
            email = request.form["email"].strip()
            address = request.form["address"].strip()

            error = validate_contact(first_name, last_name, phone, email)
            if error:
                return render_template(
                    "form.html",
                    contact=request.form,
                    title="Добавление контакта",
                    error=error,
                )

            conn = get_connection()
            conn.execute(
                """
                INSERT INTO contacts (first_name, last_name, phone, email, address)
                VALUES (?, ?, ?, ?, ?)
                """,
                (first_name, last_name, phone, email, address),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index", message="Контакт успешно добавлен"))

        return render_template("form.html", contact=None, title="Добавление контакта", error="")

    @app.route("/edit/<int:contact_id>", methods=["GET", "POST"])
    def edit_contact(contact_id):
        conn = get_connection()
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()

        if not contact:
            conn.close()
            return redirect(url_for("index", message="Контакт не найден"))

        if request.method == "POST":
            first_name = request.form["first_name"].strip()
            last_name = request.form["last_name"].strip()
            phone = request.form["phone"].strip()
            email = request.form["email"].strip()
            address = request.form["address"].strip()

            error = validate_contact(first_name, last_name, phone, email)
            if error:
                conn.close()
                return render_template(
                    "form.html",
                    contact=request.form,
                    title="Редактирование контакта",
                    error=error,
                )

            conn.execute(
                """
                UPDATE contacts
                SET first_name = ?, last_name = ?, phone = ?, email = ?, address = ?
                WHERE id = ?
                """,
                (first_name, last_name, phone, email, address, contact_id),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index", message="Контакт успешно изменен"))

        conn.close()
        return render_template("form.html", contact=contact, title="Редактирование контакта", error="")

    @app.route("/delete/<int:contact_id>", methods=["POST"])
    def delete_contact(contact_id):
        conn = get_connection()
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("index", message="Контакт удален"))

    return app


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_email(email):
    if not email:
        return True
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    pattern = r"^[0-9+\-\s()]{5,25}$"
    return re.match(pattern, phone) is not None


def validate_contact(first_name, last_name, phone, email):
    if not first_name or not last_name or not phone:
        return "Заполните обязательные поля"

    if len(first_name) < 2 or len(last_name) < 2:
        return "Имя и фамилия должны содержать хотя бы 2 символа"

    if not is_valid_phone(phone):
        return "Введите корректный номер телефона"

    if not is_valid_email(email):
        return "Введите корректный email"

    return ""


def init_db():
    conn = get_connection()
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as file:
        conn.executescript(file.read())
    conn.close()


def init_app(app):
    init_db()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

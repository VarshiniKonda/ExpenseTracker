from flask import Flask, request, redirect, session, render_template
import sqlite3

app = Flask(__name__)
app.secret_key = "expense-tracker-secret-key"


def get_db_connection():
    connection = sqlite3.connect("expenses.db")
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()

        try:

            connection.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Username already exists."

        connection.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        connection.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/dashboard")

        return "Invalid username or password."

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    expenses = connection.execute(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        expenses=expenses
    )


@app.route("/add-expense", methods=["POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form["description"]
    date = request.form["date"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO expenses
        (user_id, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            amount,
            category,
            description,
            date
        )
    )

    connection.commit()
    connection.close()

    return redirect("/dashboard")


@app.route("/delete-expense", methods=["POST"])
def delete_expense():

    if "user_id" not in session:
        return redirect("/login")

    expense_id = request.form["expense_id"]

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (
            expense_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect("/dashboard")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":

    create_database()

    app.run(debug=True)
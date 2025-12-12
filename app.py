from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ----------------------------
# MySQL connection
# ----------------------------
db = mysql.connector.connect(
    host="localhost",
    user="Sinchana",
    password="Sinchu@123",  # your MySQL password
    database="fake_news_app"  # your database
)
cursor = db.cursor(dictionary=True)

# ----------------------------
# OpenAI client
# ----------------------------
import os
api_key = os.getenv("OPENAI_API_KEY")


# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("login.html")

# Signup
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    if password != confirm:
        flash("Passwords do not match!", "danger")
        return redirect("/")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        flash("Username already exists!", "danger")
        return redirect("/")

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()
    flash("Signup successful! Please login.", "success")
    return redirect("/")

# Login
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()

    if user:
        session["username"] = username
        flash("Login successful!", "success")
        return redirect("/dashboard")
    else:
        flash("Invalid credentials!", "danger")
        return redirect("/")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "username" not in session:   
        return redirect("/")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user, feedback_text, rating FROM feedback ORDER BY id DESC")
    feedbacks = cursor.fetchall()
    cursor.close()

    return render_template("dashboard.html", user=session["username"], feedbacks=feedbacks)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect("/")

# Check news page
@app.route("/check-news", methods=["GET", "POST"])
def check_news():
    if "username" not in session:
        return redirect("/")

    result = None
    statement = ""

    if request.method == "POST":
        statement = request.form.get("statement")
        if statement:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a fake news detector. Reply with FAKE or REAL followed by a short explanation."},
                        {"role": "user", "content": statement}
                    ]
                )

                output = response.choices[0].message.content.strip()
                verdict = "REAL" if "REAL" in output.upper() else "FAKE"
                result = {"verdict": verdict, "explanation": output}

            except Exception as e:
                result = {"verdict": "ERROR", "explanation": str(e)}

    return render_template("check.html", user=session["username"], result=result, statement=statement)

# Feedback submission
@app.route("/feedback", methods=["POST"])
def feedback():
    if "username" not in session:
        return redirect("/login")

    fb_text = request.form.get("feedback")
    rating = request.form.get("rating")
    username = session["username"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO feedback (user, feedback_text, rating) VALUES (%s, %s, %s)",
        (username, fb_text, rating)
    )
    db.commit()
    cursor.close()

    flash("Feedback submitted successfully!", "success")
    return redirect("/dashboard")

# View all feedbacks
@app.route("/feedbacks")
def feedbacks_page():
    if "username" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user, feedback_text, rating FROM feedback ORDER BY id DESC")
    all_feedbacks = cursor.fetchall()
    cursor.close()

    return render_template("feedbacks.html", feedbacks=all_feedbacks)


# ----------------------------
# Run app
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)

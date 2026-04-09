from flask import Flask, jsonify, render_template, request, redirect, session
import joblib
from flask_cors import CORS
import pandas as pd
import random
import numpy as np
import smtplib
from email.mime.text import MIMEText

# ================= DB CONNECTION =================
import sqlite3

conn = sqlite3.connect("bank.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
# Create tables if not exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    account_number TEXT PRIMARY KEY,
    password TEXT,
    email TEXT,
    security_question TEXT,
    security_answer TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id TEXT,
    username TEXT,
    password TEXT
)
""")

conn.commit()
import os
app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))


# ================= APP INIT =================

app.secret_key = "mysecretkey123"
CORS(app)
from datetime import timedelta
app.permanent_session_lifetime = timedelta(minutes=10)
# ================= LOAD MODEL =================
try:
    model, input_columns = joblib.load("ids_model.pkl")
    df = pd.read_csv("processed_input.csv")
except Exception as e:
    print("Error loading model/data:", e)
    model = None
    df = pd.DataFrame()

attack_types = [
    "smurf (DoS)",
    "neptune (DoS)",
    "teardrop (DoS)",
    "satan (Probe)",
    "nmap (Probe)",
    "ipsweep (Probe)",
    "guess_passwd (R2L)",
    "warezclient (R2L)",
    "buffer_overflow (U2R)",
    "rootkit (U2R)"
]

# ================= GLOBAL STORAGE =================
failed_attempts = {}
attack_logs = []

# ================= EMAIL ALERT =================
def send_email_alert(account):
    sender = "mulavagilahemasrirenuka@gmail.com"
    password = "lykf fshj dsmg bzhk"
    receiver = "mulavagilahemasrirenuka@gmail.com"

    subject = "🚨 SECURITY ALERT - BANK SYSTEM"
    body = f"""
ALERT!

Suspicious login detected.

Account: {account}
Type: Brute Force Attack

Check SOC dashboard immediately.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("✅ Email sent")
    except Exception as e:
        print("❌ Email failed:", e)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/soc")
def soc_dashboard():
    if "admin" not in session:
        return redirect("/soc-login")

    return render_template("index.html")
# ================= PREDICT =================
@app.route("/predict/<mode>")
def predict(mode):

    sample = df.sample(1)

    if mode == "normal":
        prediction = model.predict(sample)
        probabilities = model.predict_proba(sample)

        result = int(prediction[0])
        confidence = float(np.max(probabilities)) * 100
        attack_name = "None"

    elif mode == "attack":
        result = 1
        attack_name = random.choice(attack_types)
        confidence = random.uniform(80, 99)

    else:
        return jsonify({"error": "Invalid mode"}), 400

    return jsonify({
        "result": result,
        "attack": attack_name,
        "confidence": round(confidence, 2)
    })
@app.route("/soc-login", methods=["GET", "POST"])
def soc_login():
    if request.method == "POST":
        admin_id = request.form["admin_id"]
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE admin_id=? AND username=? AND password=?",
            (admin_id, username, password)
        )
        admin = cursor.fetchone()

        if admin:
            session.permanent = True
            session["admin"] = admin_id
            return redirect("/soc")
        else:
            return redirect("/soc-login?msg=invalid")

    return render_template("soc_login.html")
@app.route("/soc-logout")
def soc_logout():
    session.clear()
    return redirect("/soc-login")
# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        acc = request.form["account_number"]
        email = request.form["email"]
        pwd = request.form["password"]
        confirm = request.form["confirm_password"]
        ques = request.form["question"]
        ans = request.form["answer"]

        if pwd != confirm:
            return redirect("/register?msg=nomatch")

        cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
        user = cursor.fetchone()

        if user:
            return redirect("/login?msg=exists")

        cursor.execute(
            "INSERT INTO users (account_number, password, email, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
            (acc, pwd, email, ques, ans)
        )
        conn.commit()

        return redirect("/login?msg=registered")

    return render_template("register.html")

# ================= LOGIN + IDS =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        acc = request.form["account_number"]
        pwd = request.form["password"]

        if acc not in failed_attempts:
            failed_attempts[acc] = 0

        cursor.execute(
            "SELECT * FROM users WHERE account_number=? AND password=?",
            (acc, pwd)
        )
        user = cursor.fetchone()

        if user:
            failed_attempts[acc] = 0
            session["user"] = acc
            return redirect("/dashboard")

        else:
            failed_attempts[acc] += 1

            if failed_attempts[acc] >= 3:
                attack_logs.append({
                    "type": "Brute Force Attack",
                    "account": acc,
                    "source": "bank_system"
                })

                send_email_alert(acc)

                return redirect("/login?msg=attack")

            return redirect("/login?msg=invalid")

    return render_template("login.html")

# ================= BANK ATTACKS =================
@app.route("/bank-attacks")
def bank_attacks():
    bank_logs = [log for log in attack_logs if log.get("source") == "bank_system"]
    return jsonify(bank_logs)

@app.route("/attacks")
def get_attacks():
    return jsonify(attack_logs)

# ================= USER DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    acc = session["user"]
    cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
    user = cursor.fetchone()

    return render_template("dashboard.html", user=user)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= ADMIN LOGIN =================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = request.form["admin_id"]
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE admin_id=? AND username=? AND password=?",
            (admin_id, username, password)
        )
        admin = cursor.fetchone()

        if admin:
            session.permanent = True
            session["admin"] = admin_id
            return redirect("/admin-dashboard")
        else:
            return redirect("/admin-login?msg=invalid")

    return render_template("admin_login.html")

# ================= ADMIN DASHBOARD =================
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin-login")

    cursor.execute("SELECT account_number, email FROM users")
    users = cursor.fetchall()

    bank_logs = [log for log in attack_logs if log.get("source") == "bank_system"]

    return render_template("admin_dashboard.html", users=users, logs=bank_logs)

# ================= FORGOT PASSWORD =================
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        acc = request.form["account_number"]

        cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
        user = cursor.fetchone()

        if user:
            return render_template("verify.html", user=user)
        else:
            return redirect("/forgot?msg=notfound")

    return render_template("forgot.html")

# ================= VERIFY =================
@app.route("/verify", methods=["POST"])
def verify():
    acc = request.form["account_number"]
    answer = request.form["answer"]

    cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
    user = cursor.fetchone()

    if user and user["security_answer"] == answer:
        return render_template("reset.html", acc=acc)
    else:
        return redirect("/forgot?msg=wronganswer")

# ================= RESET =================
@app.route("/reset", methods=["POST"])
def reset():
    acc = request.form["account_number"]
    new_password = request.form["password"]

    cursor.execute(
        "UPDATE users SET password=? WHERE account_number=?",
        (new_password, acc)
    )
    conn.commit()

    return redirect("/login?msg=reset")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
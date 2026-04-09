from flask import Flask, jsonify, render_template, request, redirect, session
import sqlite3
import os
from flask_cors import CORS
import random
import numpy as np
import pandas as pd
import joblib
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
app.secret_key = "mysecretkey123"
CORS(app)
failed_attempts = {}

# ================= DB FUNCTION =================
def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn

# ================= CREATE TABLES =================
conn = get_db()
cursor = conn.cursor()

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
    admin_id TEXT PRIMARY KEY,
    username TEXT,
    password TEXT
)
""")

# Insert admins safely
conn = get_db()
cursor = conn.cursor()

admins = [
    ("153AD", "hemasri", "hemasri1221"),
    ("154AD", "chandra", "chandra123"),
    ("155AD", "tejaswini", "teju123"),
    ("156AD", "harika", "harika123")
]

for admin in admins:
    cursor.execute("""
    INSERT OR IGNORE INTO admin (admin_id, username, password)
    VALUES (?, ?, ?)
    """, admin)

conn.commit()
conn.close()

# ================= LOAD MODEL =================
try:
    model, input_columns = joblib.load("ids_model.pkl")
    df = pd.read_csv("processed_input.csv")
except:
    model = None
    df = pd.DataFrame()

attack_types = [
    "smurf (DoS)", "neptune (DoS)", "teardrop (DoS)",
    "satan (Probe)", "nmap (Probe)", "ipsweep (Probe)",
    "guess_passwd (R2L)", "warezclient (R2L)",
    "buffer_overflow (U2R)", "rootkit (U2R)"
]

failed_attempts = {}
attack_logs = []

# ================= HOME =================
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = request.form["admin_id"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE admin_id=? AND username=? AND password=?",
            (admin_id, username, password)
        )
        admin = cursor.fetchone()

        conn.close()

        if admin:
            session["admin"] = admin_id
            return redirect("/admin-dashboard")
        else:
            return redirect("/admin-login?msg=invalid")

    return render_template("admin_login.html")
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin-login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT account_number, email FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users)

# ================= SOC =================
@app.route("/soc")
def soc():
    if "admin" not in session:
        return redirect("/soc-login")
    return render_template("index.html")

@app.route("/soc-login", methods=["GET", "POST"])
def soc_login():
    if request.method == "POST":
        admin_id = request.form["admin_id"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE admin_id=? AND username=? AND password=?",
            (admin_id, username, password)
        )
        admin = cursor.fetchone()

        conn.close()

        if admin:
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

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
        user = cursor.fetchone()

        if user:
            conn.close()
            return redirect("/login?msg=exists")

        cursor.execute("""
        INSERT INTO users (account_number, password, email, security_question, security_answer)
        VALUES (?, ?, ?, ?, ?)
        """, (acc, pwd, email, ques, ans))

        conn.commit()
        conn.close()

        return redirect("/login?msg=registered")

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        acc = request.form["account_number"]
        pwd = request.form["password"]

        if acc not in failed_attempts:
            failed_attempts[acc] = 0

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE account_number=?",
            (acc,)
        )
        user = cursor.fetchone()
        conn.close()

        # ✅ correct login
        if user and user["password"] == pwd:
            failed_attempts[acc] = 0
            session["user"] = acc
            return redirect("/dashboard")

        # ❌ wrong login
        else:
            failed_attempts[acc] += 1

            if failed_attempts[acc] >= 3:
                print("🚨 Attack detected for:", acc)

                attack_logs.append({
        "account": acc,
        "type": "Brute Force Attack"
    })
                try:
                    send_email_alert(acc)
                except Exception as e:
                    print("Email error:", e)
                    pass

                return redirect("/login?msg=attack")

            return redirect("/login?msg=invalid")

    # 🔥 THIS MUST BE OUTSIDE IF
    return render_template("login.html")
# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE account_number=?", (session["user"],))
    user = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html", user=user)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= IDS =================
@app.route("/predict/<mode>")
def predict(mode):
    if df.empty or model is None:
        return jsonify({"result": 0, "attack": "None", "confidence": 50})

    sample = df.sample(1)

    if mode == "normal":
        prediction = model.predict(sample)
        probabilities = model.predict_proba(sample)
        result = int(prediction[0])
        confidence = float(np.max(probabilities)) * 100
        attack_name = "None"
    else:
        result = 1
        attack_name = random.choice(attack_types)
        confidence = random.uniform(80, 99)

    return jsonify({
        "result": result,
        "attack": attack_name,
        "confidence": round(confidence, 2)
    })

# ================= ATTACKS =================
@app.route("/bank-attacks")
def bank_attacks():
    return jsonify(attack_logs)

@app.route("/attacks")
def attacks():
    return jsonify(attack_logs)
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        acc = request.form["account_number"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return render_template("verify.html", user=user)
        else:
            return redirect("/forgot?msg=notfound")

    return render_template("forgot.html")
@app.route("/verify", methods=["POST"])
def verify():
    acc = request.form["account_number"]
    answer = request.form["answer"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
    user = cursor.fetchone()
    conn.close()

    if user and user["security_answer"] == answer:
        return render_template("reset.html", acc=acc)
    else:
        return redirect("/forgot?msg=wronganswer")
@app.route("/reset", methods=["POST"])
def reset():
    acc = request.form["account_number"]
    new_password = request.form["password"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET password=? WHERE account_number=?",
        (new_password, acc)
    )

    conn.commit()
    conn.close()

    return redirect("/login?msg=reset")
def send_email_alert(account):
    sender = "mulavagilahemasrirenuka@gmail.com"
    password = "lykffshjdsmgbzhk"
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

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
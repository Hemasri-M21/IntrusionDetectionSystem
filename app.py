from flask import Flask, jsonify, render_template
import joblib
from flask_cors import CORS
import pandas as pd
import random

# Create Flask app
app = Flask(__name__)
CORS(app)

# Load trained model
model, input_columns = joblib.load("ids_model.pkl")

# Load processed numeric dataset
df = pd.read_csv("processed_input.csv")

# Attack names
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

# Home route → show dashboard
@app.route("/")
def home():
    return render_template("index.html")

# Prediction API
@app.route("/predict/<mode>")
def predict(mode):

    # pick random row from dataset
    sample = df.sample(1)

    # NORMAL MODE → real ML prediction
    if mode == "normal":
        prediction = model.predict(sample)
        result = int(prediction[0])
        attack_name = "None"

    # ATTACK MODE → simulate attack for demo
    elif mode == "attack":
        result = 1
        attack_name = random.choice(attack_types)

    return jsonify({
        "result": result,
        "attack": attack_name
    })

# Run locally
if __name__ == "__main__":
    app.run(debug=True)
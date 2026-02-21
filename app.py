from flask import Flask, jsonify, render_template
import joblib
from flask_cors import CORS
import pandas as pd
import random   # 👈 needed for random attack names

# Create Flask app
app = Flask(__name__)
CORS(app)

# Load trained model
model, input_columns = joblib.load("ids_model.pkl")

# Load PROCESSED numeric dataset
df = pd.read_csv("processed_input.csv")

# Realistic IDS attack names (from KDD dataset categories)
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

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Predict route
@app.route("/predict/<mode>")
def predict(mode):

    # pick random traffic row
    sample = df.sample(1)
    prediction = model.predict(sample)

    # Decide result
    if mode == "attack":
        result = 1
        attack_name = random.choice(attack_types)
    else:
        result = int(prediction[0])
        attack_name = "None"

    # Send BOTH result and attack name to frontend
    return jsonify({
        "result": result,
        "attack": attack_name
    })

# Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

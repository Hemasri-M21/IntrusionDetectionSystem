from flask import Flask, jsonify
import joblib
import pandas as pd
import random

app = Flask(__name__)

# Load trained model
model = joblib.load("ids_model.pkl")

# TEMPORARY simulated traffic (just for testing)
sample_data = [
    {"duration": 0, "src_bytes": 181, "dst_bytes": 5450},
    {"duration": 2, "src_bytes": 239, "dst_bytes": 486},
    {"duration": 0, "src_bytes": 0, "dst_bytes": 0}
]

@app.route("/predict")
def predict():

    data = random.choice(sample_data)

    df = pd.DataFrame([data])

    prediction = model.predict(df)

    return jsonify({"result": int(prediction[0])})

if __name__ == "__main__":
    app.run(debug=True)

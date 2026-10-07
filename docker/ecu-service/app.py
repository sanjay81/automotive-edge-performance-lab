from flask import Flask
import time

app = Flask(__name__)

@app.route("/health")
def health():
    return {
        "status": "ok",
        "component": "ecu-service"
    }

@app.route("/calculate")
def calculate():

    result = 0

    for i in range(500000):
        result += i * i

    return {
        "status": "completed",
        "result": result
    }

@app.route("/startup")
def startup():

    return {
        "startup_time": time.time()
    }

app.run(
    host="0.0.0.0",
    port=8080
)
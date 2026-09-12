from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "genai-poc-app"
    }), 500


@app.route("/")
def index():
    return jsonify({"message": "GitHub Actions CI/CD with GenAI POC"})
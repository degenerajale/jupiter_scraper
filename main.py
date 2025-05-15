from flask import Flask
from scraper import fetch_and_send_proposals  # Put your logic in your_script.py

app = Flask(__name__)


@app.route("/run", methods=["GET"])
def run_task():
    try:
        fetch_and_send_proposals()
        return "✅ Script ran successfully", 200
    except Exception as e:
        return f"❌ Error: {e}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

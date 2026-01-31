from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "figueira34/bot_cartola"
WORKFLOW_FILE = "mercado.yml"   # 🔥 nome correto


@app.route("/run", methods=["POST"])
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 🔥 Informa que é execução manual (vem do botão)
    data = {
        "ref": "main",
        "inputs": {
            "manual": "true"
        }
    }

    r = requests.post(url, headers=headers, json=data)

    print("🚀 GitHub response:", r.status_code, r.text)

    if r.status_code == 204:
        return jsonify({"status": "workflow started"}), 200
    else:
        return jsonify({"error": r.text}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

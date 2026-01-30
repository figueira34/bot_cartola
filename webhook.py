from flask import Flask, request
import requests
import os

app = Flask(__name__)

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "figueira34/bot_cartola"

@app.route("/run", methods=["POST"])
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/monitor.yml/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"ref": "main"}

    r = requests.post(url, headers=headers, json=data)

    return {"status": "workflow started"}, 200


if __name__ == "__main__":
    app.run()

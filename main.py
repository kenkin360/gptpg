from flask import Flask, request, jsonify, send_from_directory
import os, base64, requests

app = Flask(__name__, static_folder='.')

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = "main"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    filename = data["filename"]
    content = data["content"]

    encoded = base64.b64encode(content.encode()).decode("utf-8")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    sha = None
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        sha = res.json().get("sha")

    payload = {
        "message": f"Upload {filename} via webhook",
        "content": encoded,
        "branch": BRANCH
    }

    if sha:
        payload["sha"] = sha

    result = requests.put(url, headers=headers, json=payload)
    return jsonify(result.json()), result.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5678)

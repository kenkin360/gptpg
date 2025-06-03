
from flask import Flask, request, jsonify, send_file
import os, base64, requests, re

app = Flask(__name__, static_folder=".")

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

def upload_to_github(path, content, message):
    encoded = base64.b64encode(content.encode()).decode("utf-8")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    sha = None
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        sha = res.json().get("sha")

    payload = {
        "message": message,
        "content": encoded,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    result = requests.put(url, headers=headers, json=payload)
    return result

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/chat_ui")
def chat_ui():
    return send_file("chat_ui.html")

@app.route("/chat", methods=["POST"])
def chat_post():
    data = request.json
    content = data.get("content", "")
    match = re.search(r"```commit\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        try:
            args = eval(match.group(1))
            res = upload_to_github(args["filename"], args["content"], args["message"])
            if res.ok:
                return jsonify({"status": "committed", "path": args["filename"]})
            else:
                return jsonify({"error": "GitHub API failed", "details": res.text}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No valid commit block found"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

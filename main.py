from flask import Flask, request, jsonify, send_from_directory, send_file
import os, base64, requests, re

app = Flask(__name__, static_folder='.')

# GitHub 環境變數
GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

# 偵測格式 @@FILE{ path: "index.html", content: "<html>...</html>" }@@
file_pattern = re.compile(r'@@FILE\{\s*path:\s*"([^"]+)",\s*content:\s*"([^"]+?)"\s*\}@@', re.DOTALL)

@app.route("/chat")
def index():
    return send_from_directory(app.static_folder, "chat.html")

@app.route("/intercept", methods=["POST"])
def intercept():
    data = request.json
    gpt_reply = data.get("reply", "")

    match = file_pattern.search(gpt_reply)
    if not match:
        return jsonify({"status": "skipped", "reason": "No file pattern found."}), 200

    path, content = match.group(1), match.group(2)

    result = upload_to_github(path, content, "Auto commit via GPT reply")
    if result.ok:
        return jsonify({"status": "success", "path": path})
    else:
        return jsonify({"status": "error", "details": result.text}), 500

def upload_to_github(filename, content, commit_msg):
    encoded = base64.b64encode(content.encode()).decode("utf-8")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    sha = None
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        sha = res.json().get("sha")

    payload = {
        "message": commit_msg,
        "content": encoded,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    result = requests.put(url, headers=headers, json=payload)
    return result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

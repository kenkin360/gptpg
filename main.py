from flask import Flask, request, jsonify, send_from_directory, send_file
import os, base64, requests, re

app = Flask(__name__, static_folder='.')

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

# 偵測 @@FILE{ path: "index.html", content: "<html>..." }@@
file_pattern = re.compile(r'@@FILE\{\s*path:\s*"([^"]+)",\s*content:\s*"([^"]+?)"\s*\}@@', re.DOTALL)

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/chat")
def serve_chat_ui():
    return send_file("chat.html")

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.json
    messages = data.get("messages", [])

    last = messages[-1]["content"] if messages else ""

    match = file_pattern.search(last)
    if match:
        path, content = match.group(1), match.group(2)
        commit_msg = f"Auto commit from chat to {path}"
        upload_result = upload_to_github(path, content, commit_msg)
        if upload_result.ok:
            return jsonify({"reply": f"✅ `{path}` 已更新，請前往查看"})
        else:
            return jsonify({"reply": f"❌ commit 失敗：{upload_result.text}"}), 500
    else:
        return jsonify({"reply": last})

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

    return requests.put(url, headers=headers, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

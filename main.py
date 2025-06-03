
from flask import Flask, request, jsonify, send_file, send_from_directory
import os, base64, requests, threading, time, re

app = Flask(__name__, static_folder=".")

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")
CHAT_FILE = "chat_latest.txt"

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
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"status": "received"})

def background_commit_checker():
    while True:
        if os.path.exists(CHAT_FILE):
            with open(CHAT_FILE, encoding="utf-8") as f:
                text = f.read()
            match = re.search(r"```commit\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                try:
                    data = eval(match.group(1))
                    res = upload_to_github(data["filename"], data["content"], data["message"])
                    if res.ok:
                        print(f"✅ {data['filename']} committed.")
                        os.remove(CHAT_FILE)
                    else:
                        print("❌ Commit failed:", res.text)
                except Exception as e:
                    print("❌ Error during commit:", e)
        time.sleep(10)

threading.Thread(target=background_commit_checker, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, request, jsonify, send_file
import os, base64, requests, threading, time, json

app = Flask(__name__, static_folder='.')

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

CHAT_LOG = "chat_latest.txt"

@app.route("/")
def index():
    return send_file("_index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    content = data.get("content", "")
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"status": "saved"})

def check_for_commit():
    while True:
        if os.path.exists(CHAT_LOG):
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                content = f.read()

            if "```commit" in content:
                try:
                    payload_block = content.split("```commit")[1].split("```")[0]
                    payload = json.loads(payload_block.strip())

                    filename = payload["filename"]
                    file_content = payload["content"]
                    commit_message = payload["message"]

                    encoded = base64.b64encode(file_content.encode()).decode("utf-8")
                    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"
                    headers = {
                        "Authorization": f"Bearer {GH_TOKEN}",
                        "Accept": "application/vnd.github.v3+json"
                    }

                    sha = None
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        sha = res.json().get("sha")

                    commit_payload = {
                        "message": commit_message,
                        "content": encoded,
                        "branch": BRANCH
                    }
                    if sha:
                        commit_payload["sha"] = sha

                    res = requests.put(url, headers=headers, json=commit_payload)
                    print("✅ Committed:", res.status_code, res.json())
                    os.remove(CHAT_LOG)

                except Exception as e:
                    print("❌ Commit error:", str(e))
        time.sleep(10)

threading.Thread(target=check_for_commit, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

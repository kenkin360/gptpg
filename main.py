<<<<<<< HEAD
from flask import Flask, request, jsonify, send_from_directory, send_file
import os, base64, requests, openai

app = Flask(__name__, static_folder='.')

# === 環境設定 ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ["GH_TOKEN"]
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = "main"
UPLOAD_URL = "https://gptpg-production.up.railway.app/upload"
=======
from flask import Flask, request, jsonify, send_file
import os, base64, requests, threading, time, json

app = Flask(__name__, static_folder='.')

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

CHAT_LOG = "chat_latest.txt"
>>>>>>> 02ebc84 ( Changes to be committed:)

# === 首頁 ===
@app.route("/")
def index():
    return send_file("index.html")

<<<<<<< HEAD
# === GPT 專用 chat 頁面 ===
@app.route("/chat")
def serve_chat():
    return send_file("chat.html")

# === 用來接收 GPT 上傳檔案 ===
@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    filename = data["path"] if "path" in data else data["filename"]
    content = data["content"]
    message = data.get("message", f"Upload {filename} via webhook")
=======
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    content = data.get("content", "")
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"status": "saved"})
>>>>>>> 02ebc84 ( Changes to be committed:)

def check_for_commit():
    while True:
        if os.path.exists(CHAT_LOG):
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                content = f.read()

<<<<<<< HEAD
    # 取得原本 sha（若有）
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
=======
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
>>>>>>> 02ebc84 ( Changes to be committed:)

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

# === Chat API：對話 + GPT function calling ===
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_input = request.json.get("prompt", "")
    if not user_input:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "You help generate files to be committed to a GitHub repository."},
                {"role": "user", "content": user_input}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "upload_file_to_repo",
                    "description": "Upload a file to a GitHub repo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["path", "content", "message"]
                    }
                }
            }],
            tool_choice="auto"
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            args = eval(tool_call.function.arguments)
            upload_res = requests.post(UPLOAD_URL, json=args, headers={"Authorization": f"Bearer {GH_TOKEN}"})
            if upload_res.status_code == 200:
                return jsonify({"reply": f"✅ `{args['path']}` committed with message `{args['message']}`."})
            else:
                return jsonify({"reply": f"❌ Upload failed: {upload_res.text}"}), 500
        else:
            return jsonify({"reply": message.content or "[No reply]"})

    except Exception as e:
        return jsonify({"reply": f"❌ Error: {str(e)}"}), 500


# === 啟動應用 ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
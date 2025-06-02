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

# === 首頁 ===
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

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

    encoded = base64.b64encode(content.encode()).decode("utf-8")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

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

    result = requests.put(url, headers=headers, json=payload)
    return jsonify(result.json()), result.status_code

# === Chat API：對話 + GPT function calling ===
@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_input = request.json.get("prompt", "")
    if not user_input:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            api_key=OPENAI_API_KEY,
            messages=[
                {"role": "system", "content": "You help generate files to be committed to a GitHub repository."},
                {"role": "user", "content": user_input}
            ],
            functions=[{
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
            }],
            function_call="auto"
        )

        message = response["choices"][0]["message"]

        if "function_call" in message:
            args = eval(message["function_call"]["arguments"])
            upload_res = requests.post(UPLOAD_URL, json=args, headers={"Authorization": f"Bearer {GH_TOKEN}"})
            if upload_res.status_code == 200:
                return jsonify({"reply": f"✅ `{args['path']}` committed with message `{args['message']}`."})
            else:
                return jsonify({"reply": f"❌ Upload failed: {upload_res.text}"}), 500
        else:
            return jsonify({"reply": message.get("content", "[No reply]")})

    except Exception as e:
        return jsonify({"reply": f"❌ Error: {str(e)}"}), 500

# === 啟動應用 ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

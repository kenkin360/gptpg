from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import requests, os, base64, json, re, uuid

app = Flask(__name__, static_folder=".", template_folder=".")

GH_TOKEN = os.environ.get("GH_TOKEN")
CHATGPT_SESSION_TOKEN = os.environ.get("CHATGPT_SESSION_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")    

@app.route("/chat")
def serve_chat():
    return render_template("chat.html")

@app.route("/chat_api", methods=["POST"])
def chat_api():
    try:
        user_input = request.json.get("prompt", "")
        headers = {
            "Authorization": f"Bearer {CHATGPT_SESSION_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://chat.openai.com/",
            "Origin": "https://chat.openai.com",
            "Accept": "text/event-stream"
        }
        payload = {
            "action": "next",
            "messages": [{
                "role": "user",
                "content": {"content_type": "text", "parts": [user_input]}
            }],
            "model": "text-davinci-002-render-sha",
            "parent_message_id": str(uuid.uuid4())
        }
        response = requests.post("https://chat.openai.com/backend-api/conversation", headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({
                "error": f"ChatGPT 回應失敗（HTTP {response.status_code}）",
                "raw": response.text
            }), 500

        reply_text = response.text
        try:
            reply_json = response.json()
            reply_text = json.dumps(reply_json)
        except json.JSONDecodeError:
            return jsonify({
                "error": "無法解析 ChatGPT 回應為 JSON",
                "raw": reply_text
            }), 500

        matches = re.findall(r"@@FILE\{(.*?)\}@@", reply_text, re.DOTALL)
        if matches:
            for m in matches:
                file_data = json.loads("{" + m + "}")
                upload_to_github(file_data["path"], file_data["content"], file_data["message"])
            return jsonify({"reply": "✅ 檔案已更新並上傳至 GitHub。"})

        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def upload_to_github(filename, content, message):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    encoded = base64.b64encode(content.encode()).decode("utf-8")
    payload = {
        "message": message,
        "content": encoded,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

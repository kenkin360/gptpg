from flask import Flask, request, jsonify, render_template, send_from_directory
import requests, re, os, base64

app = Flask(__name__, static_folder='public', template_folder='templates')

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")
UPLOAD_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/chat")
def serve_chat():
    return render_template("proxy_chat.html")

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_prompt = request.json.get("prompt", "")
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GH_TOKEN}"
        }

        # 向 ChatGPT 發送使用者輸入 (需手動在 browser 端觸發)
        # 此處僅為無 API key 下的模擬架構
        content = f"{user_prompt}\n@@FILE{{ path: 'index.html', content: '<html><body>{user_prompt}</body></html>' }}@@"

        match = re.search(r"@@FILE\{(.+?)\}@@", content, re.DOTALL)
        if match:
            args_text = match.group(1)
            args = eval(f"dict({args_text})")
            path = args["path"]
            file_content = args["content"]
            commit_msg = args.get("message", f"Auto commit {path}")

            encoded = base64.b64encode(file_content.encode()).decode()
            file_url = f"{UPLOAD_URL}{path}"
            get_res = requests.get(file_url, headers={
                "Authorization": f"Bearer {GH_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            })

            sha = get_res.json().get("sha") if get_res.status_code == 200 else None
            payload = {
                "message": commit_msg,
                "content": encoded,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            put_res = requests.put(file_url, headers={
                "Authorization": f"Bearer {GH_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }, json=payload)

            if put_res.status_code in [200, 201]:
                return jsonify({ "reply": f"✅ `{path}` 已更新，請至 repo 測試結果。" })
            else:
                return jsonify({ "reply": f"❌ GitHub 更新失敗: {put_res.text}" })

        return jsonify({ "reply": content })

    except Exception as e:
        return jsonify({ "reply": f"❌ 錯誤: {str(e)}" })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

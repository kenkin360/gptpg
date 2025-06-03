from flask import Flask, request, jsonify, send_from_directory, render_template
import requests, os, base64, json, re

app = Flask(__name__, static_folder=".", template_folder=".")

GH_TOKEN = os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER", "kenkin360")
REPO_NAME = os.environ.get("REPO_NAME", "gptpg")
BRANCH = os.environ.get("BRANCH", "main")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat")
def serve_chat():
    return render_template("chat.html")

@app.route("/chat_api", methods=["POST"])
def chat_api():
    try:
        payload = request.get_json()
        headers = {
            "Content-Type": "application/json",
            "Authorization": request.headers.get("Authorization", "")
        }

        response = requests.post("https://chat.openai.com/backend-api/conversation", headers=headers, json=payload)

        try:
            reply = response.json()
        except Exception:
            return jsonify({"error": "非 JSON 回應", "raw": response.text}), 500

        matches = re.findall(r"@@FILE\\{(.*?)\\}@@", json.dumps(reply), re.DOTALL)
        if matches:
            for m in matches:
                file_data = json.loads("{" + m + "}")
                filename = file_data["path"]
                content = file_data["content"]
                commit_msg = file_data["message"]
                upload_to_github(filename, content, commit_msg)
            return jsonify({"reply": "✅ 檔案已更新並上傳至 GitHub。"})

        return jsonify(reply)
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
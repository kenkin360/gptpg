
from flask import request, jsonify
import openai
import os
import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")
UPLOAD_URL = "https://gptpg-production.up.railway.app/upload"

upload_file_function = {
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

def register_chat_api(app):
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
                functions=[upload_file_function],
                function_call="auto"
            )
            message = response["choices"][0]["message"]

            if "function_call" in message:
                args = eval(message["function_call"]["arguments"])
                upload_res = requests.post(UPLOAD_URL, json=args, headers={"Authorization": f"Bearer {GH_TOKEN}"})
                if upload_res.status_code == 200:
                    return jsonify({"reply": f"✅ File `{args['path']}` uploaded with commit message: `{args['message']}`."})
                else:
                    return jsonify({"reply": f"❌ Upload failed: {upload_res.text}"}), 500
            else:
                return jsonify({"reply": message.get("content", "[No reply]")})

        except Exception as e:
            return jsonify({"reply": f"❌ Error: {str(e)}"}), 500

from flask import send_file
from chat_api import register_chat_api

@app.route("/chat")
def serve_chat():
    return send_file("chat.html")

register_chat_api(app)

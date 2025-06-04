import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright
import nest_asyncio

nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret')
CORS(app, supports_credentials=True)

@app.route("/api/render", methods=["POST"])
async def render():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
        except Exception as e:
            html = f"<pre style='color:red;'>Error loading page: {e}</pre>"
        finally:
            await browser.close()

    return jsonify({ "html": html, "console": console_logs })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

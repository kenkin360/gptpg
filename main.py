import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from playwright.async_api import async_playwright
import nest_asyncio

nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret')
CORS(app, supports_credentials=True)

@app.route("/api/render", methods=["POST"])
def render():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    result = asyncio.run(handle_render(url))
    return jsonify(result)

async def handle_render(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
            java_script_enabled=True,
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 800}
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            await page.goto(url, timeout=60000, wait_until="networkidle")
            html = await page.content()
        except Exception as e:
            html = f"<pre style='color:red;'>Error loading page: {e}</pre>"
        finally:
            await browser.close()

    return { "html": html, "console": console_logs }

@app.route("/browser")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("frontend", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

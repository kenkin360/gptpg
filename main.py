
import os
import asyncio
import nest_asyncio
from flask import Flask, request, session, redirect, url_for, render_template_string, make_response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import async_playwright

nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

def get_user_session():
    if 'proxy_session' not in session:
        session['proxy_session'] = {}
    if 'cookies' not in session['proxy_session']:
        session['proxy_session']['cookies'] = {}
    s = requests.Session()
    s.cookies.update(session['proxy_session']['cookies'])
    return s

def save_cookies(s):
    session['proxy_session']['cookies'] = s.cookies.get_dict()

def rewrite_html(soup, base_url):
    for tag, attr in [('img','src'),('script','src'),('link','href'),('video','src'),('audio','src'),('source','src'),('iframe','src')]:
        for t in soup.find_all(tag):
            if t.has_attr(attr):
                orig = t[attr]
                if orig.startswith('data:'):
                    continue
                t[attr] = url_for('resource_proxy') + '?url=' + urljoin(base_url, orig)
    for a in soup.find_all('a'):
        if a.has_attr('href'):
            href = a['href']
            if href.startswith('mailto:') or href.startswith('javascript:') or href.startswith('#'):
                continue
            link = urljoin(base_url, href)
            a['href'] = url_for('browser') + '?url=' + link
    for form in soup.find_all('form'):
        action = form.get('action')
        if action:
            target = urljoin(base_url, action)
        else:
            target = base_url
        method = form.get('method', 'get').lower()
        form['action'] = url_for('form_proxy') + '?url=' + target + '&method=' + method
    return soup

async def render_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        await browser.close()
        return content

@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url', 'https://www.example.com')
    return render_template_string("""
        <form action="/browse" method="get">
            <input name="url" value="{{url}}" style="width:60vw">
            <button type="submit">Go</button>
        </form>
        <div style="border:1px solid #888;min-height:80vh;padding:1em;margin-top:8px;">
            請輸入網址
        </div>
    """, url=url)

@app.route('/browse', methods=['GET'])
def browser():
    target_url = request.args.get('url')
    if not target_url:
        return redirect(url_for('index'))
    try:
        html = asyncio.get_event_loop().run_until_complete(render_with_playwright(target_url))
        soup = BeautifulSoup(html, 'html.parser')
        soup = rewrite_html(soup, target_url)
        return render_template_string("""
            <form action="/browse" method="get">
                <input name="url" value="{{url}}" style="width:60vw">
                <button type="submit">Go</button>
            </form>
            <div style="border:1px solid #888;min-height:80vh;padding:1em;margin-top:8px;">
                {{content|safe}}
            </div>
        """, url=target_url, content=str(soup))
    except Exception as e:
        return f'Error: {e}'

@app.route('/resource')
def resource_proxy():
    url = request.args.get('url')
    if not url:
        return 'Missing url', 400
    try:
        resp = requests.get(url, stream=True, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        headers = {}
        for key, value in resp.headers.items():
            if key.lower() in ['content-encoding','content-length','transfer-encoding','connection']:
                continue
            headers[key] = value
        data = resp.content
        response = make_response(data)
        for key, value in headers.items():
            response.headers[key] = value
        return response
    except Exception as e:
        return f'Error loading resource: {e}', 502

@app.route('/form', methods=['POST', 'GET'])
def form_proxy():
    return redirect(url_for('browser') + '?url=' + request.args.get('url'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)

import os
import re
import asyncio
import nest_asyncio
from flask import Flask, request, session, Response, redirect, url_for, render_template_string, make_response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pyppeteer import launch

nest_asyncio.apply()  # 讓pyppeteer能跑在Flask主線程

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
USE_PYPPETEER = True   # 若遇動態網站會自動開啟

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

async def render_with_pyppeteer(url):
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 20000})
    html = await page.content()
    await browser.close()
    return html

@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url', 'https://www.example.com')
    return render_template_string('''
        <form action="/browse" method="get">
            <input name="url" value="{{url}}" style="width:60vw">
            <button type="submit">Go</button>
        </form>
        <div style="border:1px solid #888;min-height:80vh;padding:1em;margin-top:8px;">
            請輸入網址
        </div>
    ''', url=url)

@app.route('/browse', methods=['GET'])
def browser():
    target_url = request.args.get('url')
    if not target_url:
        return redirect(url_for('index'))
    s = get_user_session()
    try:
        # 先用requests測試是不是靜態頁
        resp = s.get(target_url, stream=True, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        save_cookies(s)
        content_type = resp.headers.get('Content-Type', '').lower()
        html = resp.content
        # 只要不是text/html，直接當資源下載
        if 'text/html' not in content_type:
            return redirect(url_for('resource_proxy') + '?url=' + target_url)
        # 判斷有沒有javascript重導/動態內容（太簡單，真需求可再強化）
        if USE_PYPPETEER and (b'<script' in html or b'window.location' in html):
            html = asyncio.get_event_loop().run_until_complete(render_with_pyppeteer(target_url)).encode('utf-8')
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception:
            soup = BeautifulSoup(html, 'lxml')
        soup = rewrite_html(soup, target_url)
        page = render_template_string('''
            <form action="/browse" method="get">
                <input name="url" value="{{url}}" style="width:60vw">
                <button type="submit">Go</button>
            </form>
            <div style="border:1px solid #888;min-height:80vh;padding:1em;margin-top:8px;">
                {{content|safe}}
            </div>
        ''', url=target_url, content=str(soup))
        return page
    except Exception as e:
        return f'Error: {e}'

@app.route('/resource')
def resource_proxy():
    url = request.args.get('url')
    if not url:
        return 'Missing url', 400
    s = get_user_session()
    try:
        resp = s.get(url, stream=True, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        save_cookies(s)
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
    target_url = request.args.get('url')
    method = request.args.get('method','get').lower()
    s = get_user_session()
    try:
        if method == 'post':
            resp = s.post(target_url, data=request.form, files=request.files, headers={'User-Agent': 'Mozilla/5.0'})
        else:
            resp = s.get(target_url, params=request.args, headers={'User-Agent': 'Mozilla/5.0'})
        save_cookies(s)
        content_type = resp.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            return redirect(url_for('resource_proxy') + '?url=' + target_url)
        html = resp.content
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception:
            soup = BeautifulSoup(html, 'lxml')
        soup = rewrite_html(soup, target_url)
        return render_template_string('''
            <form action="/browse" method="get">
                <input name="url" value="{{url}}" style="width:60vw">
                <button type="submit">Go</button>
            </form>
            <div style="border:1px solid #888;min-height:80vh;padding:1em;margin-top:8px;">
                {{content|safe}}
            </div>
        ''', url=target_url, content=str(soup))
    except Exception as e:
        return f'Error in form submission: {e}'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)

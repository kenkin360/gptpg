# gptpg

# ChatGPT Commit Interceptor

## 使用方式

1. 在 ChatGPT 回覆中包含格式：
   @@FILE{ path: "index.html", content: "<h1>Hello</h1>" }@@

2. 此 webhook 於 /intercept 端點接收 JSON：
   { "reply": "ChatGPT 的完整回覆含 @@FILE{...}@@" }

3. 伺服器會擷取內容，自動 commit 到 GitHub

## 必要環境變數

- GH_TOKEN：GitHub Personal Access Token
- REPO_OWNER：預設 kenkin360
- REPO_NAME：預設 gptpg
- BRANCH：預設 main

## Railway 部署

部署後將 /intercept 作為目標，用於 ChatGPT 回覆的攔截與上傳。

# gptpg

# ChatGPT WebApp Commit Interceptor

## 使用流程

1. ChatGPT 回覆範例如下：
   ✅ 檔案已更新
   @@FILE{ path: "index.html", content: "<!DOCTYPE html><html>...</html>" }@@

2. 將整段回應貼入 Web App 頁面 `/` 提交

3. 伺服器於 /intercept 端點解析後自動 commit 至 GitHub

## 環境變數（於 Railway 設定）

- GH_TOKEN
- REPO_OWNER（預設 kenkin360）
- REPO_NAME（預設 gptpg）
- BRANCH（預設 main）


# ChatGPT Commit 自動化對話應用

## 使用方式
1. 開啟 `/chat` 頁面，與 ChatGPT 以自然語言對話。
2. 若 ChatGPT 的回覆包含：
   @@FILE{ path: "index.html", content: "<html>...</html>" }@@
   系統會自動 commit 至指定 GitHub repo。
3. 你只會看到簡短提示「✅ 檔案已更新，請測試」。

## 運作條件
- 已設定環境變數 GH_TOKEN、REPO_OWNER、REPO_NAME
- 此系統不依賴 OpenAI API，而是從 ChatGPT Web 回應中擷取


import { createApp, ref } from "vue"

const App = {
  setup() {
    const url = ref("https://example.com")
    const html = ref("")
    const consoleLog = ref("")

    const load = async () => {
      const res = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.value })
      })
      const data = await res.json()
      html.value = data.html
      consoleLog.value = data.console.join("\n")
    }

    return { url, html, consoleLog, load }
  },
  template: `
    <div class="browser">
      <div class="toolbar">
        <input v-model="url" @keyup.enter="load" class="url-input">
        <button @click="load">Go</button>
      </div>
      <div class="content" v-html="html"></div>
      <pre class="console">{{ consoleLog }}</pre>
    </div>
  `
}

createApp(App).mount("#app")

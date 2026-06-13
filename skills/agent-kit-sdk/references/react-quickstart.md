# React 快速开始

本文是 React 前端接入 Agent Kit 的最小可复制模板。新建 React 应用时先按本文做，再按需阅读 `chat-ui.md`、`file-upload.md`、`session-runtime.md`。

## 依赖版本

React 应用必须使用 `@blade-hq/agent-kit@0.5.11` 和它声明的 peer dependencies。不要使用 React 18，不要写不存在的 `@blade-hq/agent-kit@^1.0.0`。

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-kit": "0.5.11",
    "@tanstack/react-query": "^5.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "sonner": "^2.0.7"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.0.0"
  }
}
```

或直接安装：

```bash
npm install @blade-hq/agent-kit@0.5.11 react@^19.0.0 react-dom@^19.0.0 @tanstack/react-query@^5.0.0 sonner@^2.0.7
```

## 公开入口

只使用这些入口：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"
import { BladeClientProvider, useSessionStore } from "@blade-hq/agent-kit/react"
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"
```

不要从 `@blade-hq/agent-kit` 包根入口导入 `AgentProvider`、`useAgent`、`ChatView`。不要假设存在 `client.execute()`、`client.workspace.write()` 这类未在 public-skills 说明的方法。

## 最小 App

```tsx
import { useMemo, useState } from "react"
import { BladeClient } from "@blade-hq/agent-kit/client"
import { BladeClientProvider, useSessionStore } from "@blade-hq/agent-kit/react"
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"

export function App() {
  const [baseUrl, setBaseUrl] = useState("http://localhost:8020")
  const [token, setToken] = useState("")
  const [sessionId, setSessionId] = useState<string | null>(null)

  const client = useMemo(
    () => new BladeClient({ baseUrl, token: () => token }),
    [baseUrl, token],
  )

  async function createSession() {
    const { session_id } = await client.sessions.createSession("发布文档评审")
    setSessionId(session_id)
    useSessionStore.getState().setActiveSession(session_id)
  }

  async function uploadFile(file: File) {
    if (!sessionId) throw new Error("请先创建 session")
    const form = new FormData()
    form.append("files", file)
    form.append("paths", JSON.stringify([file.name]))
    const response = await fetch(
      `${baseUrl.replace(/\/$/, "")}/api/sessions/${sessionId}/upload/${encodeURIComponent(".")}`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      },
    )
    const body = await response.json()
    if (!response.ok || body.failed?.length) {
      throw new Error(`上传失败: ${JSON.stringify(body)}`)
    }
    return file.name
  }

  async function analyzeFile(fileName: string) {
    if (!sessionId) throw new Error("请先创建 session")
    const socket = client.socket()
    socket.connect()
    socket.emit("session:subscribe", { session_id: sessionId })
    socket.emit("chat:send", {
      session_id: sessionId,
      mode: "executing",
      message: `请读取工作区里的 ${fileName}，提取标题、owner、category、所有二级标题、风险列表，并判断这份文档是否适合进入发布评审。请返回结构化结果，并说明依据。`,
    })
  }

  return (
    <BladeClientProvider baseUrl={baseUrl} token={() => token}>
      <main style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
        <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
        <input value={token} onChange={(event) => setToken(event.target.value)} type="password" />
        <button onClick={createSession}>新建 Session</button>
        <input
          type="file"
          accept=".md,.markdown,.txt"
          onChange={async (event) => {
            const file = event.target.files?.[0]
            if (!file) return
            const fileName = await uploadFile(file)
            await analyzeFile(fileName)
          }}
        />
        {sessionId ? <ChatView sessionId={sessionId} /> : null}
      </main>
    </BladeClientProvider>
  )
}
```

## 不要这样写

以下写法都不是 public-skills 支持的前端接入方式：

```ts
import { AgentProvider, useAgent, ChatView } from "@blade-hq/agent-kit"
```

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@blade-hq/agent-kit": "^1.0.0"
  }
}
```

```ts
await fetch("/api/chat")
await fetch("/sessions")
await fetch(`/sessions/${sessionId}/messages`)
await client.execute(...)
await client.workspace.write(...)
```

正确方式：

- 创建 session：`client.sessions.createSession(...)`，读取返回的 `session_id`。
- 上传普通文件：`POST /api/sessions/{session_id}/upload/{dir_path}`。
- 发送任务：Socket.IO `chat:send`，并显式传 `mode: "executing"`。
- 展示聊天：React 使用 `ChatView`。

# 后端快速开始

本文是 Node.js 后端接入 Agent Kit 的最小可复制模板。新建 Express/Fastify/Koa 后端时先按本文做，再按需阅读 `backend.md`、`file-upload.md`、`session-runtime.md`。

Node.js 后端默认必须使用 Agent Kit Node SDK。`docs/rest-api.md` 和 `docs/websocket-api.md` 是底层协议参考，只用来确认公开路径和事件，不得作为绕过 `@blade-hq/agent-kit/client` 的理由。除非用户明确要求“不要使用 SDK，直接协议接入”，否则不要写裸 `axios`/`fetch` + `socket.io-client` 实现。

## 必须先满足的红线

如果生成的 Node.js 后端不满足下面任一项，就不是正确的 Agent Kit 后端集成：

- `package.json` 必须包含 `@blade-hq/agent-kit@0.5.11`。
- Node.js 项目必须使用 ESM：`package.json` 设置 `"type": "module"`，并从 `@blade-hq/agent-kit/client` 导入。
- 创建 client 必须使用 `new BladeClient({ baseUrl, token })`。
- 创建 session 必须使用 `new BladeClient(...).sessions.createSession(...)`。
- 发送业务任务必须使用 `client.socket()` + Socket.IO `chat:send`。
- 普通文件上传优先使用 `client.sessions.uploadFiles(session_id, ".", files)`；直接 REST 时才使用 `POST /api/sessions/{session_id}/upload/{dir_path}` multipart。
- `DOCS_AUDIT.md` 的 SDK 包入口必须写 `@blade-hq/agent-kit/client`，不能写“无特定 SDK”或“直接 HTTP + Socket.IO”。

不要用 `axios`、`fetch` 或裸 `socket.io-client` 自己调用 Blade 的 session/task/workspace/chat API 来替代 SDK。下面这些写法都不是本文支持的 Node 后端集成：

- `require("@blade-hq/agent-kit")` 或 `import ... from "@blade-hq/agent-kit"` 包根入口
- `createClient(...)`
- `package.json` 不安装 `@blade-hq/agent-kit`
- `DOCS_AUDIT.md` 写“无特定 SDK”
- `client.uploadFile(...)`
- `client.workspaces.uploadFile(...)`
- 直接用 `axios`/`fetch` 调 `/api/sessions` 来创建 session，替代 `client.sessions.createSession(...)`
- 直接用裸 `socket.io-client` 连接 Blade，替代 `client.socket()`
- `/api/v1/sessions`
- `/api/v1/sessions/{id}/workspace`
- `/api/v1/sessions/{id}/tasks`
- `/api/sessions/{id}/workspace`
- `/api/sessions/{id}/tasks`
- `/api/tasks/{task_id}`
- `/api/tasks/{task_id}/stream`

如果需要把运行过程转成 HTTP SSE，SSE 端点只负责把 Socket.IO 事件转发给你的调用方；不要创建 task、不要轮询 task、不要调用 task stream。

## 依赖版本

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-kit": "0.5.11",
    "express": "^4.18.2",
    "multer": "^2.0.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/multer": "^2.0.0",
    "typescript": "^5.0.0"
  }
}
```

或直接安装：

```bash
npm install @blade-hq/agent-kit@0.5.11 express@^4.18.2 multer@^2.0.0
```

## 公开后端链路

后端调用 Blade Agent 时只使用这些公开入口：

1. 创建 session：`client.sessions.createSession(...)`
2. 上传普通业务文件：Node SDK 用 `client.sessions.uploadFiles(session_id, ".", files)`；直接 REST 用 `POST /api/sessions/{session_id}/upload/{dir_path}`，multipart 字段为 `files` 和 `paths`
3. 发送任务：Socket.IO `chat:send`，显式传 `mode: "executing"`
4. 监听结果：`turn:start`、`turn:patch`、`turn:end`、`chat:end`、`system:error`

不要使用：

- `require("@blade-hq/agent-kit")`
- `import { BladeClient } from "@blade-hq/agent-kit"`
- `import { createClient } from "@blade-hq/agent-kit/client"`
- `createClient(...)`
- `client.uploadFile(...)`
- `client.workspaces.uploadFile(...)`
- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{id}/workspace`
- `POST /api/v1/sessions/{id}/tasks`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/sessions/{id}/workspace`
- `POST /api/sessions/{id}/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/stream`
- JSON workspace 上传
- task polling
- `axios`/`fetch` session/task/workspace/chat 调用替代 `BladeClient`

## Express 最小模板

```ts
import express from "express"
import multer from "multer"
import { BladeClient } from "@blade-hq/agent-kit/client"

const app = express()
const upload = multer({ storage: multer.memoryStorage() })

app.use(express.json())

function getConfig() {
  const baseUrl = process.env.BLADE_AGENT_URL
  const token = process.env.BLADE_AGENT_TOKEN
  if (!baseUrl || !token) {
    throw new Error("BLADE_AGENT_URL and BLADE_AGENT_TOKEN are required")
  }
  return { baseUrl: baseUrl.replace(/\/$/, ""), token }
}

function getClient() {
  const { baseUrl, token } = getConfig()
  return new BladeClient({ baseUrl, token })
}

app.get("/health", (_req, res) => {
  res.json({ status: "healthy" })
})

app.post("/api/sessions", async (req, res, next) => {
  try {
    const client = getClient()
    const created = await client.sessions.createSession(req.body.intent ?? "文档分析")
    res.json(created) // Node SDK returns { session_id }
  } catch (err) {
    next(err)
  }
})

app.post("/api/sessions/:session_id/upload", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "missing file" })
    }

    const client = getClient()
    const { session_id } = req.params
    const remotePath = req.body.remotePath || req.file.originalname

    const result = await client.sessions.uploadFiles(session_id, ".", [
      {
        file: new File([req.file.buffer], req.file.originalname, {
          type: req.file.mimetype || "application/octet-stream",
        }),
        name: remotePath,
      },
    ])

    if (result.failed?.length) {
      return res.status(502).json({ error: "upload failed", detail: result })
    }
    res.json(result)
  } catch (err) {
    next(err)
  }
})

app.post("/api/sessions/:session_id/analyze", async (req, res) => {
  const { session_id } = req.params
  const filePath = req.body.filePath
  const message =
    req.body.message ||
    `请读取工作区里的 ${filePath}，提取标题、owner、category、所有二级标题、风险列表，并判断这份文档是否适合进入发布评审。请返回结构化结果，并说明依据。`

  const client = getClient()
  const socket = client.socket()

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
  })

  const send = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  }
  const heartbeat = setInterval(() => send("heartbeat", { ts: Date.now() }), 15000)
  const cleanup = () => {
    clearInterval(heartbeat)
    socket.emit("session:unsubscribe", { session_id })
    socket.disconnect()
  }
  const finish = () => {
    cleanup()
    if (!res.writableEnded) {
      res.end()
    }
  }

  res.on("close", cleanup)
  send("connected", { ok: true })

  socket.on("connect", () => {
    socket.emit("session:subscribe", { session_id })
    socket.emit("chat:send", { session_id, message, mode: "executing" })
  })
  socket.on("connect_error", (err) => {
    send("error", { message: err.message })
    finish()
  })
  socket.on("turn:start", (payload) => send("turn:start", payload))
  socket.on("turn:patch", (payload) => send("turn:patch", payload))
  socket.on("turn:end", (payload) => send("turn:end", payload))
  socket.on("chat:end", (payload) => {
    send("chat:end", payload)
    finish()
  })
  socket.on("system:error", (payload) => {
    send("error", payload)
    finish()
  })
  socket.connect()
})
```

## 验收检查

- `POST /api/sessions` 返回真实 `{ session_id }`。
- 上传接口使用 `client.sessions.uploadFiles(session_id, ".", files)`，或显式转发到 `/api/sessions/{session_id}/upload/{dir_path}`；不是 `/api/v1/...`、不是 workspace JSON、不是 `client.uploadFile()`。
- 分析接口通过 Socket.IO `chat:send` 发送任务，不创建 task、不轮询 task。
- SSE 连接后立即返回 `connected`。
- `connect_error`、`system:error`、`chat:end` 都会清理 socket/heartbeat 并结束响应。

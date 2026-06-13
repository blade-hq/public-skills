# Node.js 后端接入

## 安装

```bash
npm install @blade-hq/agent-kit@0.5.11
```

Node.js 项目必须使用 ESM：`package.json` 设置 `"type": "module"`。只用 `/client` 入口，不需要 React。

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-kit": "0.5.11"
  }
}
```

::: danger 常见错误
```ts
// 错误：不要从包根导入
import { BladeClient } from "@blade-hq/agent-kit"
// 错误：不要用 require
const { BladeClient } = require("@blade-hq/agent-kit")
// 错误：不存在 createClient
import { createClient } from "@blade-hq/agent-kit/client"
```
:::

## 创建 Client

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL,  // 后端 origin，不带 pathname
  token: process.env.BLADE_AGENT_TOKEN,  // sk-blade-v2-...
})
```

## 创建会话与发送消息

```ts
const { session_id } = await client.sessions.createSession("用户任务")

const socket = client.socket()
socket.on("turn:start", (p) => console.log("开始:", p.role))
socket.on("turn:patch", (p) => { /* 增量更新 */ })
socket.on("turn:end", (p) => console.log("结束:", p.role))
socket.on("chat:end", (p) => {
  console.log("完成:", p.status) // completed / failed
  socket.disconnect()
})
socket.on("system:error", (p) => console.error(p.message))

socket.connect()
socket.emit("session:subscribe", { session_id })
socket.emit("chat:send", { session_id, message: "你好", mode: "executing" })
```

离开时清理：

```ts
socket.emit("session:unsubscribe", { session_id })
socket.disconnect()
```

## Headless 一次性问答

最省事的后端入口，自动建会话、跑完、返回结果：

```ts
// 纯文本
const reply = await client.headless.run("用一句话介绍你自己")
console.log(reply) // string

// 结构化结果
const data = await client.headless.run("提取公司名和金额：...", {
  schema: {
    type: "object",
    properties: {
      company: { type: "string" },
      amount: { type: "number" },
    },
    required: ["company", "amount"],
  },
})
console.log(data.company, data.amount)

// 必须断开 socket，否则 Node 进程不会退出
client.socket().disconnect()
```

::: warning
`headless.run` 内部会建立 Socket.IO 长连接。Node 脚本拿到结果后，**必须**调用 `client.socket().disconnect()` 或 `process.exit(0)`，否则进程会一直挂住。
:::

`headless.run(prompt, options)` 的 options：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `schema` | JSON Schema 对象 | 返回结构化数据 |
| `model` | string | 模型 ID |
| `timeoutMs` | number | 超时，默认 300000 |

## 会话管理（REST）

```ts
const { session_id } = await client.sessions.createSession("用户任务")
const detail = await client.sessions.getSession(session_id)
const sessions = await client.sessions.listSessions()
const turns = await client.sessions.getSessionTurns(session_id)   // 渲染用的投影
const history = await client.sessions.getSessionHistory(session_id) // 原始历史树
await client.sessions.deleteSession(session_id)
```

## Express SSE 包装示例

将 Socket.IO 事件转为 HTTP SSE 流：

```ts
import express from "express"
import { BladeClient } from "@blade-hq/agent-kit/client"

const app = express()
app.use(express.json())

app.post("/api/sessions/:session_id/chat", async (req, res) => {
  const { session_id } = req.params
  const { message } = req.body
  const client = new BladeClient({
    baseUrl: process.env.BLADE_AGENT_URL!,
    token: process.env.BLADE_AGENT_TOKEN!,
  })
  const socket = client.socket()

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
  })
  res.write(`event: connected\ndata: {"ok":true}\n\n`)

  const send = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  }
  const heartbeat = setInterval(() => send("heartbeat", { ts: Date.now() }), 15000)
  const cleanup = () => {
    clearInterval(heartbeat)
    socket.emit("session:unsubscribe", { session_id })
    socket.disconnect()
  }
  const finish = () => { cleanup(); if (!res.writableEnded) res.end() }

  res.on("close", cleanup)
  socket.on("connect", () => {
    socket.emit("session:subscribe", { session_id })
    socket.emit("chat:send", { session_id, message, mode: "executing" })
  })
  socket.on("connect_error", (err) => { send("error", { message: err.message }); finish() })
  socket.on("turn:start", (p) => send("turn:start", p))
  socket.on("turn:patch", (p) => send("turn:patch", p))
  socket.on("turn:end", (p) => send("turn:end", p))
  socket.on("chat:end", (p) => { send("chat:end", p); finish() })
  socket.on("system:error", (p) => { send("error", p); finish() })
  socket.connect()
})
```

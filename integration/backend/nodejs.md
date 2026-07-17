# Node.js 后端接入

后端只需要框架无关的核心包 `@blade-hq/agent-client`（Node.js 18+ 直接可用，内置 fetch）。

## 安装

```bash
npm install @blade-hq/agent-client
```

项目必须是 ESM：`package.json` 里设置 `"type": "module"`。

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-client": "^0.1.0"
  }
}
```

## 创建 Client

后端场景用访问令牌鉴权（不能用弹窗登录，那是浏览器专用的）：

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL,   // 后端 origin，不带路径
  token: process.env.BLADE_AGENT_TOKEN,   // sk-blade-xxx，见"鉴权与 Token"
})
```

## Headless 一次性问答

最省事的后端入口：自动建会话、跑完、返回最终结果。

```ts
// 纯文本
const reply = await client.headless.run("用一句话介绍你自己")
console.log(reply) // string

// 结构化结果：传 JSON Schema，返回符合 schema 的对象
const data = await client.headless.run<{ company: string; amount: number }>(
  "提取公司名和金额：...",
  {
    schema: {
      type: "object",
      properties: {
        company: { type: "string" },
        amount: { type: "number" },
      },
      required: ["company", "amount"],
    },
  },
)
console.log(data.company, data.amount)

// 必须断开实时连接，否则 Node 进程不会退出
client.socket().disconnect()
```

`headless.run(prompt, options)` 的 options：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `schema` | JSON Schema 对象 | 返回结构化数据 |
| `model` | string | 模型 ID |
| `timeoutMs` | number | 超时，默认 300000 |

变体：

```ts
await client.headless.runInSession(sessionId, prompt, options)  // 在已有会话里跑
// 返回 { session_id, chat_run_id, result }，chat_run_id 用于事后追溯这次运行
await client.headless.runWithSession(prompt, options)
```

失败时抛出 `HeadlessError`（超时、运行失败、智能体报告的业务错误）。

::: warning headless 会自动审批工具
headless 模式下智能体的 Bash、文件写入等工具会被自动批准执行，只应对可信输入开放。不要把不可控的用户输入直接拼进 prompt。
:::

::: warning 进程不退出
`headless.run` 内部会建立实时长连接。Node 脚本拿到结果后**必须**调用 `client.socket().disconnect()` 或 `process.exit(0)`，否则进程会一直挂住。
:::

## 流式对话（要中间过程时）

Node 里同样可以用会话对象，API 与浏览器完全一致：

```ts
const chat = await client.sessions.create({ intent: "数据分析" })

chat.on("toolCall", ({ toolCall }) => console.log("工具:", toolCall.name))
chat.on("message", ({ message }) => console.log("消息:", message.content))
chat.on("chatEnd", ({ status }) => {
  console.log("完成:", status)   // completed / failed / interrupted / paused
  chat.dispose()
  client.socket().disconnect()
})
chat.on("error", ({ message }) => console.error(message))

await chat.send("统计工作区里 CSV 的行数", { mode: "executing" })
```

## 会话管理（REST）

```ts
const { session_id } = await client.sessions.createSessionWithRequest({ intent: "用户任务" })
const detail = await client.sessions.getSession(session_id)
const sessions = await client.sessions.listSessions()
const turns = await client.sessions.getSessionTurns(session_id)     // 渲染用的结构化消息
const history = await client.sessions.getSessionHistory(session_id) // 原始历史树
await client.sessions.deleteSession(session_id)
```

SDK 未类型化的其余不常用的接口用通用通道，路径对照后端 Swagger（`<后端地址>/docs`）：

```ts
const skills = await client.api.get("/api/skills")
await client.api.post("/api/sessions", { intent: "..." })
```

## Express SSE 包装示例

把会话事件转成 HTTP SSE 流交给自己的前端：

```ts
import express from "express"
import { BladeClient } from "@blade-hq/agent-client"

const app = express()
app.use(express.json())

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL!,
  token: process.env.BLADE_AGENT_TOKEN!,
})

app.post("/api/sessions/:session_id/chat", async (req, res) => {
  const { session_id } = req.params
  const { message } = req.body

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
  })
  const send = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  }
  res.write(`event: connected\ndata: {"ok":true}\n\n`)   // 立刻写出，避免网关超时

  let finished = false
  let heartbeat: ReturnType<typeof setInterval> | undefined
  const offs: Array<() => void> = []

  function finish() {
    if (finished) return
    finished = true
    if (heartbeat) clearInterval(heartbeat)
    for (const off of offs) off()
    if (!res.writableEnded) res.end()
  }
  res.on("close", finish)

  try {
    const chat = await client.sessions.connect(session_id)
    if (finished) return
    heartbeat = setInterval(() => send("heartbeat", { ts: Date.now() }), 15000)
    offs.push(
      chat.on("message", (e) => send("message", e.message)),
      chat.on("toolCall", (e) => send("toolCall", e.toolCall)),
      chat.on("toolResult", (e) => send("toolResult", e.toolCall)),
      chat.on("error", (e) => { send("error", e); finish() }),
      chat.on("chatEnd", (e) => { send("chatEnd", e); finish() }),
    )
    await chat.send(message, { mode: "executing" })
  } catch (error) {
    if (!finished) {
      send("error", { message: error instanceof Error ? error.message : String(error) })
    }
    finish()
  }
})
```

要点：`res.writeHead` 后立刻写出第一个事件；至少转发 `message` / `toolCall` / `chatEnd` / `error`；用 heartbeat 保活；在 `chatEnd`、错误路径、`res.close` 里都要移除**当前请求**注册的监听器。`connect(session_id)` 会复用同一 client 缓存的会话实例，因此单个 SSE 请求结束时不要调用 `chat.dispose()`，否则会同时中断仍在使用该会话的其他请求。

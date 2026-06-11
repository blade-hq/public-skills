# 后端集成（Node.js / Python）

后端场景不渲染 UI，只通过网络调用 Blade Agent：建会话、上传普通业务文件、发消息拿结果、读历史、上传 session skill。两套后端 SDK：

- **Node.js**：`@blade-hq/agent-kit/client`（纯 client，不依赖 React）。
- **Python**：`blade-agent-kit`（异步 REST + Socket.IO client）。

两者都需要先拿到 Bearer token，见 [auth-token.md](auth-token.md)。

后端代用户发起真实任务时，通常显式使用干活模式：`mode: "executing"`。模式说明见 [work-modes.md](work-modes.md)。

如果后端要接收用户上传的 Markdown、文本、CSV 等业务文件，并让 Agent 读取分析，先读 [file-upload.md](file-upload.md)。普通文件上传和 session skill 上传不同，不要用 `uploadSessionSkill()` 上传业务文档。

---

## Node.js（`@blade-hq/agent-kit/client`）

### 安装

```bash
npm install @blade-hq/agent-kit
```

只用 `/client` 时不需要 React、不需要导入样式。包是 ESM，脚本用 `.mjs` 或在 `package.json` 设 `"type": "module"`。

### 创建 client

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL, // 后端 origin，不带 pathname
  token: process.env.BLADE_AGENT_TOKEN, // sk-blade-v2-...
})
```

### 一次性问答（headless，最简单）

`headless.run` 内部自动建会话、跑完、返回结果，是后端最省事的入口。

```ts
// 纯文本结果
const reply = await client.headless.run("用一句话介绍你自己")
console.log(reply) // string

// 结构化结果：传 JSON Schema，返回符合该 schema 的对象
const data = await client.headless.run("提取这段话里的公司名和金额：……", {
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

// ⚠️ 必须：headless 用完后断开 socket，否则 Node 进程会一直挂住、不会退出
client.socket().disconnect()
```

> **重要（Node 必看）**：`headless.run` 内部会建立 Socket.IO 长连接。**每个**用到 `headless` 或 `socket()` 的 Node 脚本，在拿到结果、打印完之后，结尾都必须显式 `client.socket().disconnect()`（或 `process.exit(0)`）。漏掉这一步脚本能打印出结果，但进程不退出、命令一直卡住。上面示例最后一行就是这个收尾，照抄时不要删。

`headless.run(prompt, options)` 的 `options`：`schema?`（JSON Schema 对象）、`model?`（模型 id）、`timeoutMs?`（默认 300000）。

### 会话与历史（REST）

```ts
const { session_id } = await client.sessions.createSession("用户任务")
const detail = await client.sessions.getSession(session_id)
const sessions = await client.sessions.listSessions()
const turns = await client.sessions.getSessionTurns(session_id)   // 渲染用的投影
const history = await client.sessions.getSessionHistory(session_id) // 原始历史树
await client.sessions.deleteSession(session_id)
```

> 注意：Node 端 `createSession` 返回 `{ session_id }`（字符串字段）。Python 端 `create_session` 返回的是 `Session` 对象，用 `session.id`。

### 流式对话（底层 socket）

需要逐字 / 逐步拿到中间过程时，用底层 socket 自己监听。

```ts
const { session_id } = await client.sessions.createSession("用户任务")
const socket = client.socket()

socket.on("turn:start", (p) => {})
socket.on("turn:patch", (p) => {
  // p.patch_type / p.data：增量更新（文本片段、工具调用等）
})
socket.on("turn:end", (p) => {})
socket.on("chat:end", (p) => {
  // p.status：completed / failed；一轮对话结束
  socket.disconnect()
})
socket.on("system:error", (p) => console.error(p.message))

socket.connect()
socket.emit("session:subscribe", { session_id })
socket.emit("chat:send", { session_id, message: "你好", mode: "executing" })
```

离开时 `socket.emit("session:unsubscribe", { session_id })` 并 `socket.disconnect()`。

### 上传普通文件后执行分析

Node.js 后端可用公开 REST 接口把普通文件上传到 session workspace，再用 socket 发送 `mode: "executing"` 的业务任务。完整上传说明见 [file-upload.md](file-upload.md)。

```ts
import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { BladeClient } from "@blade-hq/agent-kit/client"

const baseUrl = process.env.BLADE_AGENT_URL!
const token = process.env.BLADE_AGENT_TOKEN!
const client = new BladeClient({ baseUrl, token })
const { session_id } = await client.sessions.createSession("文档分析")

const localPath = "q2-launch-notes.md"
const remotePath = basename(localPath)
const form = new FormData()
form.append("files", new Blob([await readFile(localPath)]), remotePath)
form.append("paths", JSON.stringify([remotePath]))

const uploadResponse = await fetch(
  `${baseUrl.replace(/\/$/, "")}/api/sessions/${session_id}/upload/${encodeURIComponent(".")}`,
  {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  },
)
const uploadResult = await uploadResponse.json()
if (!uploadResponse.ok || uploadResult.failed?.length) {
  throw new Error(`上传失败: ${JSON.stringify(uploadResult)}`)
}

const socket = client.socket()
socket.on("chat:end", (p) => {
  console.log("done", p.status)
  socket.disconnect()
})
socket.on("system:error", (p) => {
  console.error(p.message)
  socket.disconnect()
})

socket.connect()
socket.emit("session:subscribe", { session_id })
socket.emit("chat:send", {
  session_id,
  message: `请读取工作区里的 ${remotePath}，提取标题、owner、category、二级标题和风险列表。`,
  mode: "executing",
})
```

### Express API 包装层最小检查

如果用 Express 把 Blade 能力包装成业务 API，先满足这些最小要求，再写上传和聊天逻辑：

- JSON API 前必须注册 `app.use(express.json())`；否则 `POST` 请求的 `req.body` 会是 `undefined`。
- 文件上传接口使用 `multer`、`busboy` 或同类 multipart 中间件；不要用 `express.json()` 解析文件。
- SSE 接口要立即写出一个事件，避免客户端等不到 headers/body 超时。
- SSE 接口要设置 heartbeat，并在上游 socket 错误、`chat:end`、浏览器断开时清理 socket。
- 端到端测试不要只检查 HTTP 200；必须确认收到 `chat:end`，且 `status` 是 `completed`。

Express SSE 包装层示例：

```ts
import express from "express"
import { BladeClient } from "@blade-hq/agent-kit/client"

const app = express()
app.use(express.json())

app.post("/api/sessions", async (req, res, next) => {
  try {
    const client = new BladeClient({
      baseUrl: process.env.BLADE_AGENT_URL!,
      token: process.env.BLADE_AGENT_TOKEN!,
    })
    const created = await client.sessions.createSession(req.body.intent ?? "用户任务")
    res.json(created)
  } catch (err) {
    next(err)
  }
})

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
  const finish = () => {
    cleanup()
    if (!res.writableEnded) {
      res.end()
    }
  }

  res.on("close", cleanup)
  socket.on("connect", () => {
    socket.emit("session:subscribe", { session_id })
    socket.emit("chat:send", { session_id, message, mode: "executing" })
  })
  socket.on("connect_error", (err) => {
    send("error", { message: err.message })
    finish()
  })
  socket.on("turn:start", (p) => send("turn:start", p))
  socket.on("turn:patch", (p) => send("turn:patch", p))
  socket.on("turn:end", (p) => send("turn:end", p))
  socket.on("chat:end", (p) => {
    send("chat:end", p)
    finish()
  })
  socket.on("system:error", (p) => {
    send("error", p)
    finish()
  })
  socket.connect()
})
```

---

## Python（`blade-agent-kit`）

### 安装

```bash
pip install blade-agent-kit
# 或 uv：uv add blade-agent-kit
```

import 名是 `blade_agent_kit`。客户端是**异步**的，所有网络方法都要 `await`，建议用 `async with`。

### 创建 client

```python
from blade_agent_kit import BladeAgentClient

async with BladeAgentClient(
    "http://127.0.0.1:8020",          # 后端 origin
    token="sk-blade-v2-...",          # 不传则读环境变量 BLADE_AGENT_TOKEN
) as client:
    print(await client.health())
```

### 会话与历史（REST）

```python
created = await client.create_session(intent="用户任务")
session_id = created.id                       # 注意：用 .id

sessions = await client.list_sessions()        # list[Session]
detail = await client.get_session(session_id)
history = await client.get_history(session_id)
files = await client.list_dir(session_id, ".") # 工作区目录
checkpoints = await client.get_checkpoints(session_id)
await client.delete_session(session_id)
```

### 上传普通文件后执行分析

Python SDK 可直接使用 `upload_file()`。完整说明见 [file-upload.md](file-upload.md)。

```python
from pathlib import Path

created = await client.create_session(intent="文档分析")
session_id = created.id

upload_result = await client.upload_file(
    session_id,
    Path("q2-launch-notes.md"),
    dir_path=".",
    remote_path="q2-launch-notes.md",
)
if upload_result.get("failed"):
    raise RuntimeError(f"上传失败: {upload_result['failed']}")

async for event in client.chat(
    session_id,
    message="请读取工作区里的 q2-launch-notes.md，提取标题、owner、category、二级标题和风险列表。",
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.status)
```

### 流式对话（chat 迭代器）

`client.chat(...)` 返回一个异步事件迭代器，事件类型为 `TurnStart / TurnPatch / TurnEnd / ChatEnd / SystemError`，用 `event.kind` 区分。

```python
def extract_text(blocks) -> str:
    if not isinstance(blocks, list):
        return ""
    return "".join(
        b.get("content", "")
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    )

final_reply = ""
async for event in client.chat(
    session_id,
    message="用一句话介绍你自己",
    mode="executing",
):
    if event.kind == "turn:end" and event.raw.get("role") == "assistant":
        text = extract_text(event.raw.get("blocks"))
        if text:
            final_reply = text
    elif event.kind == "chat:end":
        print("done:", event.status)  # completed / failed
print(final_reply)
```

需要时也可单独订阅：`client.subscribe(session_id)`；中途打断用 `await client.stop(session_id)`。

### 一次性问答（headless）

```python
# 纯文本结果
reply = await client.headless.run("用一句话介绍你自己")  # str

# 结构化结果
data = await client.headless.run(
    "提取公司名和金额：……",
    schema={
        "type": "object",
        "properties": {"company": {"type": "string"}, "amount": {"type": "number"}},
        "required": ["company", "amount"],
    },
)  # dict
```

`headless.run(prompt, *, schema=None, model=None, timeout_secs=300.0)`。schema 也可以传一个有 `model_json_schema()` 的 Pydantic 模型类。

如果 headless 任务必须直接调用工具、读取工作区文件或处理上传文件，可不用 `headless.run` 快捷入口，改用底层 `client.chat(..., headless=True, output_schema=..., mode="executing")`：

```python
schema = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}

async for event in client.chat(
    session_id,
    message="请读取工作区里的 report.md，并返回摘要",
    headless=True,
    output_schema=schema,
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.result)
```

### 事件类型导入

```python
from blade_agent_kit import TurnStart, TurnPatch, TurnEnd, ChatEnd, SystemError
```

---

## 选 headless 还是流式？

- 只要最终结果（问答、抽取、批处理）：用 **headless**，最少代码。
- 要展示中间过程、工具调用、逐字输出：用 **流式 socket / chat 迭代器**。
- 把对话 UI 交给浏览器、后端只做编排：后端用 REST + headless，实时流由前端 `@blade-hq/agent-kit` 负责。

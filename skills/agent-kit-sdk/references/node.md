# Node.js / 自动化接入

`@blade-hq/agent-client` 在 Node.js 18+ 直接可用（内置 fetch）。后端 / 脚本场景用访问令牌（PAT）鉴权，不能用弹窗登录。

```bash
npm install @blade-hq/agent-client
```

项目需为 ESM（`package.json` 里 `"type": "module"`）。

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_URL!,    // 如 https://blade.example.com
  token: process.env.BLADE_TOKEN!,    // sk-blade-xxx，见 auth.md
})
```

## headless.run：一次性任务

最省事的后端入口：自动建会话、跑完、返回最终结果，中间过程不落 UI。

```ts
try {
  // 纯文本结果
  const reply = await client.headless.run("用一句话总结这段话的要点：……")
  console.log(reply)  // string

  // 结构化结果：传 JSON Schema，返回符合 schema 的对象
  const data = await client.headless.run<{ company: string; amount: number }>(
    "提取公司名和合同金额：……",
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
} finally {
  // 成功、超时或失败都必须断开，否则 Node 进程不会退出
  client.socket().disconnect()
}
```

选项：`schema`（JSON Schema 对象）、`model`（模型覆盖）、`timeoutMs`（默认 300000）。

变体：

```ts
await client.headless.runInSession(sessionId, prompt, options)  // 在已有会话里跑
// 返回 { session_id, chat_run_id, result }，chat_run_id 用于事后追溯这次运行
await client.headless.runWithSession(prompt, options)
```

失败时抛出 `HeadlessError`（超时、运行失败、智能体报告的业务错误）。

::: warning headless 会自动审批工具
headless 模式下智能体的 Bash、文件写入等工具会被自动批准执行，只应对可信输入开放，不要把不可控的用户输入直接拼进 prompt。
:::

## 流式对话（要中间过程时）

Node 里同样可以用 `AgentSession`（与浏览器 API 完全一致）：

```ts
const chat = await client.sessions.create({ intent: "数据分析" })
let cleaned = false
const cleanup = () => {
  if (cleaned) return
  cleaned = true
  chat.dispose()
  client.socket().disconnect()
}

chat.on("toolCall", ({ toolCall }) => console.log("工具:", toolCall.name))
chat.on("message", ({ message }) => console.log("消息:", message.content))
chat.on("chatEnd", ({ status }) => {
  console.log("完成:", status)
  cleanup()
})
chat.on("error", ({ message }) => {
  console.error(message)
  cleanup()
})

try {
  await chat.send("统计工作区里 CSV 的行数", { mode: "executing" })
} catch (error) {
  console.error(error)
  cleanup()
}
```

## 会话管理与文件

```ts
const { session_id } = await client.sessions.createSessionWithRequest({
  intent: "文档分析",
  solution_id: "my-solution",   // 可选：指定解决方案
  biz_role_id: "analyst",       // 可选：指定业务角色
})

const detail = await client.sessions.getSession(session_id)
const sessions = await client.sessions.listSessions()
const turns = await client.sessions.getSessionTurns(session_id)   // 渲染用的结构化消息
await client.sessions.deleteSession(session_id)

// 上传业务文件到会话工作区（Node 18 需要从 node:buffer 导入 File）
import { File } from "node:buffer"
import { readFile } from "node:fs/promises"
const result = await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([await readFile("report.md")], "report.md"), name: "report.md" },
])
if (result.failed?.length) throw new Error(`上传失败: ${result.failed}`)
```

上传后在消息里写清文件路径，让智能体读取处理：

```ts
await client.headless.runInSession(session_id, "请读取工作区里的 report.md，提取标题和风险列表。")
client.socket().disconnect()
```

其余 REST 接口（技能、模型、其余不常用的接口）见 [rest-api.md](rest-api.md)。

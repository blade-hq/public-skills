# SDK 入口

本文只说明 `@blade-hq/agent-kit` 对外暴露的 JS 包入口和最小配置。

## 包名

```bash
npm install @blade-hq/agent-kit
```

React 应用通常还需要：

```bash
npm install react react-dom @tanstack/react-query sonner
```

## 导出入口

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"
```

纯 JS client。React、Vue、Node.js 都可以使用。

```ts
import { BladeClientProvider, useSessionStore } from "@blade-hq/agent-kit/react"
```

React provider、hooks 和 stores。只有 React 应用使用。

```ts
import { ChatView } from "@blade-hq/agent-kit/chat"
```

React 聊天组件。Vue / Node.js 不能直接使用。

```ts
import "@blade-hq/agent-kit/style.css"
```

React 组件样式。只使用 `/client` 时不需要导入。

## BladeClient

```ts
const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-xxx",
})
```

运行时 token 推荐用 getter：

```ts
const client = new BladeClient({
  baseUrl,
  token: () => localStorage.getItem("blade-token"),
})
```

`baseUrl` 必须是 Blade Agent 后端 origin，不要带 pathname。

正确：

```ts
new BladeClient({ baseUrl: "http://localhost:8020" })
```

错误：

```ts
new BladeClient({ baseUrl: "http://localhost:5173/agent-api" })
```

## 常用资源

```ts
await client.sessions.createSession("任务")
await client.sessions.getSession(sessionId)
await client.sessions.getSessionTurns(sessionId)
await client.skills.listSessionSkills(sessionId)
await client.skills.uploadSessionSkill(sessionId, payload)
await client.skills.getSkillStats(sessionId)
```

普通业务文件上传到 session workspace 见 `file-upload.md`。Python SDK 有 `upload_file()`；Node.js 可直接调用公开 REST 上传接口。

底层 socket：

```ts
const socket = client.socket()
```

Socket 事件和 session 生命周期见 `session-runtime.md`。

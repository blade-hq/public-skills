# 会话、鉴权与运行时

本文说明 session、token、Socket.IO 和运行时连接。

## baseUrl

`baseUrl` 必须是 Blade Agent 后端 origin，不要带 pathname。

正确：

```ts
const client = new BladeClient({ baseUrl: "http://localhost:8020" })
```

错误：

```ts
const client = new BladeClient({ baseUrl: "http://localhost:5173/agent-api" })
```

如果使用 Vite proxy，也可以让 SDK 使用当前页面 origin。

## Bearer Token

推荐用 getter，方便运行时切换 token：

```ts
const client = new BladeClient({
  baseUrl,
  token: () => localStorage.getItem("blade-token"),
})
```

用户保存新 token 后，应重连 socket：

```ts
const socket = client.socket()
socket.disconnect()
socket.connect()
```

## 创建 session

```ts
const { session_id } = await client.sessions.createSession("用户任务")
```

React 使用 `ChatView` 时，同步 active session：

```ts
import { useSessionStore } from "@blade-hq/agent-kit/react"

useSessionStore.getState().setActiveSession(session_id)
```

如果宿主自己创建 session，也要把 session 信息同步给 SDK store，或重新加载 session 列表。

## Socket.IO

底层 socket 适合 Vue、Node.js 或完全自渲染场景：

```ts
const socket = client.socket()
socket.connect()
socket.emit("session:subscribe", { session_id: sessionId })
socket.emit("chat:send", { session_id: sessionId, message: "你好", mode: "executing" })
```

`mode` 可选值只有 `"executing"` 和 `"planning"`。真实业务任务、文件处理、工具调用默认用 `"executing"`；只要计划不执行时用 `"planning"`。详见 [work-modes.md](work-modes.md)。

监听事件：

- `chat:start`
- `turn:start`
- `turn:patch`
- `turn:end`
- `chat:end`
- `system:error`
- `system:notification`

离开页面时：

```ts
socket.emit("session:unsubscribe", { session_id: sessionId })
```

## 历史与状态

常用 client API：

```ts
await client.sessions.getSession(sessionId)
await client.sessions.getSessionTurns(sessionId)
await client.sessions.getSessionHistory(sessionId)
await client.skills.listSessionSkills(sessionId)
await client.skills.getSkillStats(sessionId)
```

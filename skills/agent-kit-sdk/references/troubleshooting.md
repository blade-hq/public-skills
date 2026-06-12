# 故障排查

## 页面白屏或 React 无限循环

常见原因：

- Zustand selector 每次返回新的数组或对象，例如 `state.items[id] ?? []`。
- React 19 会提示 `The result of getSnapshot should be cached`。

修复：

```ts
const EMPTY_ITEMS: Item[] = []

const items = useStore((state) => state.items[id] ?? EMPTY_ITEMS)
```

## ChatView 样式异常

常见原因：

- 宿主没有导入 `@blade-hq/agent-kit/style.css`。
- 宿主写了全局 `button`、`input`、`svg`、`pre` 等样式，污染 SDK 内部 UI。

修复：

- 把宿主样式限定到自己的容器，例如 `.toolbar button`，不要写全局 `button`。
- 只用 `classNames` / `components` / `renderers.tool` 自定义 SDK。

## React 依赖安装冲突

现象：

- `npm install` 报 `ERESOLVE unable to resolve dependency tree`。
- 日志里出现 `@blade-hq/agent-kit` 需要 React 19，但项目安装了 React 18。
- 日志里出现 `No matching version found for @blade-hq/agent-kit@^1.0.0`。

修复：

```bash
npm install @blade-hq/agent-kit@0.5.11 react@^19.0.0 react-dom@^19.0.0 @tanstack/react-query@^5.0.0 sonner@^2.0.7
```

新建 React + Agent Kit 项目时不要默认选 React 18。不要用 `--force` 或 `--legacy-peer-deps` 绕过 peer dependency，绕过后 ChatView 运行时可能不稳定。

## 前端调用了不存在的 Blade API 端点

常见错误：

- `POST /api/chat`
- `GET /sessions`
- `POST /sessions`
- `POST /sessions/{id}/messages`

修复：

- 创建 session 用 SDK：`client.sessions.createSession(...)`，返回字段是 `session_id`。
- 普通文件上传用 `POST /api/sessions/{session_id}/upload/{dir_path}`。
- 发送业务任务用 Socket.IO：`socket.emit("chat:send", { session_id, message, mode: "executing" })`。
- React 聊天 UI 优先用 `ChatView`，不要自造一套未经文档确认的 REST chat API。

## 后端调用了不存在的 `/api/v1/*` 端点

常见错误：

- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{id}/workspace`
- `POST /api/v1/sessions/{id}/tasks`
- `GET /api/v1/sessions/{id}/tasks/{task_id}`
- `POST /api/sessions/{id}/workspace`
- `POST /api/sessions/{id}/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/stream`
- 把文件 JSON 内容发到 workspace 接口
- 创建 task 后轮询 task 状态来代替聊天流
- `package.json` 没有安装 `@blade-hq/agent-kit`
- `require("@blade-hq/agent-kit")` 或 `import ... from "@blade-hq/agent-kit"` 包根入口
- `import { createClient } from "@blade-hq/agent-kit/client"` 或 `createClient(...)`
- `client.uploadFile(...)`
- `client.workspaces.uploadFile(...)`

修复：

- 创建 session 用 SDK：`client.sessions.createSession(...)`；如果直接 REST，使用 `POST /api/sessions`。
- Node.js 后端从 `@blade-hq/agent-kit/client` 导入：`import { BladeClient } from "@blade-hq/agent-kit/client"`。
- 创建 client 用 `new BladeClient({ baseUrl, token })`，不是 `createClient(...)`。
- 普通文件上传优先使用 SDK：`client.sessions.uploadFiles(session_id, ".", files)`。
- 直接 REST 上传时使用 `POST /api/sessions/{session_id}/upload/{dir_path}`，请求体必须是 `multipart/form-data`，字段是 `files` 和 `paths`。
- 发送业务任务用 Socket.IO：`socket.emit("chat:send", { session_id, message, mode: "executing" })`。
- 后端 SSE 包装层只是把 Socket.IO 事件转发给调用方，不要臆造 task REST API。
- Node.js 后端的 `package.json` 必须安装 `@blade-hq/agent-kit@0.5.11`；不要只用 `axios` 调 Blade。

## Node 后端导入 SDK 时报 `ERR_PACKAGE_PATH_NOT_EXPORTED`

常见原因：

- 在 Node 22 / `@blade-hq/agent-kit@0.5.11` 下写了 `require("@blade-hq/agent-kit")`。
- 从包根导入：`import { BladeClient } from "@blade-hq/agent-kit"`。
- `package.json` 没有设置 `"type": "module"`，但代码使用 ESM-only SDK。

修复：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"
```

`package.json` 至少包含：

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-kit": "0.5.11"
  }
}
```

## Node 后端上传时报 `client.uploadFile is not a function`

原因：

- 0.5.11 的 Node client 没有 `client.uploadFile(...)`。

修复：

```ts
const result = await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([buffer], "report.md"), name: "report.md" },
])
```

如果不用 SDK 上传，才直接调用公开 REST multipart：`POST /api/sessions/{session_id}/upload/{dir_path}`。

## Node 后端上传时报 `client.workspaces` 是 undefined

原因：

- 0.5.11 的普通文件上传方法不在 `client.workspaces` 下。
- 不要猜 `client.workspaces.uploadFile(...)`。

修复：

```ts
const result = await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([buffer], "report.md"), name: "report.md" },
])
```

## Socket 连接失败

现象：

- REST API 返回 200，但 ChatView 显示“暂时无法建立连接”。
- network 里只有 `/api/...` 成功，Socket.IO 一直断开或没有启动。

排查：

- `baseUrl` 是否是后端 origin，且不带 pathname。
- Bearer token 是否同时能用于 REST 和 Socket.IO。
- 保存运行时 token 后是否触发 socket reconnect。
- 后端 CORS 是否放行宿主 origin。

运行时 token 示例：

```ts
const client = new BladeClient({
  baseUrl,
  token: () => localStorage.getItem("blade-token"),
})

// 用户保存新 token 后，通过 client 实例获取 socket 并重连
const socket = client.socket()
socket.disconnect()
socket.connect()
```

## ChatView 能看历史但发不出消息

常见原因：

- 宿主切换 session 后没有调用 `useSessionStore.getState().setActiveSession(sessionId)`。
- Socket 没有订阅当前 session room。

修复：

```ts
useSessionStore.getState().setActiveSession(sessionId)
```

## 上传到 session 的 skill 看不到或不能用

排查：

- session skill 名称是否符合 `org/skill-name`。
- payload 是否包含 `SKILL.md`。
- 上传 API 是否返回成功。
- `client.skills.listSessionSkills(sessionId)` 是否能看到新 skill。
- `client.skills.getSkillStats(sessionId)` 里的 loaded skill 是否包含目标 skill。

## 上传普通文件后 Agent 找不到文件

普通业务文件上传见 [file-upload.md](file-upload.md)，不要使用 session skill 上传接口。

排查：

- 上传接口返回的 `uploaded` 是否包含目标文件路径。
- `failed` 是否为空；非空时不要继续发送分析任务。
- 发送给 Agent 的消息里是否写了同一个 workspace 相对路径，例如 `uploads/report.md`。
- 发送分析任务时是否显式传 `mode: "executing"`。
- `dir_path` 和 `remote_path` 是否组合出了预期路径；例如 `dir_path="uploads"`、`remote_path="report.md"` 后，消息里应写 `uploads/report.md`。
- Node.js 直接调用 REST 上传时，是否使用 `multipart/form-data` 的 `files` 字段，并把 `paths` 写成 JSON 字符串数组。
- Node.js 不要手动设置 `Content-Type`，否则 multipart boundary 可能丢失。

## Express 后端 JSON 请求体是 undefined

常见原因：

- 注册路由前没有调用 `app.use(express.json())`。
- 客户端没有发送 `Content-Type: application/json`。
- 文件上传接口和 JSON 接口混用了同一个解析中间件。

修复：

```ts
const app = express()
app.use(express.json())

app.post("/api/sessions", async (req, res) => {
  const intent = req.body.intent ?? "用户任务"
  // ...
})
```

文件上传接口单独使用 multipart 中间件，不要依赖 `express.json()` 读取文件内容。

## 后端 SSE 接口连接后一直超时

常见原因：

- 服务端建立上游 socket 后，没有立即向浏览器写出任何 SSE 数据。
- 没有监听 `connect_error` / `system:error`，上游失败时客户端只能等待超时。
- 没有 heartbeat，代理或客户端可能认为连接空闲。
- 收到 `chat:end` 后没有结束响应或清理 socket。

修复：

- `res.writeHead(200, { "Content-Type": "text/event-stream", ... })` 后立刻写出 `connected` 事件。
- 至少转发 `turn:start`、`turn:patch`、`turn:end`、`chat:end`、`system:error`。
- 用 `setInterval` 发送 heartbeat，并在 `res.close`、`chat:end`、错误路径中清理。
- E2E 测试必须读取 SSE，直到收到 `chat:end` 且 `status` 为 `completed`。

## 地图或宿主业务 UI 没有响应工具结果

排查：

- Python 工具是否返回 `_meta.bridge`。
- action 是否与宿主监听一致，例如 `map.highlight`。
- React 宿主是否从 `useGisStore.pendingMapCommandsBySession[sessionId]` 消费命令。
- 消费后是否调用 `consumeMapCommand(sessionId, command.id)`。

## Leaflet / 第三方 UI 在 React dev mode 下状态丢失

React StrictMode 会 mount/unmount/remount。第三方 imperative UI 要在 cleanup 中清理引用。

示例：

```ts
return () => {
  map.remove()
  mapRef.current = null
  markersRef.current.clear()
}
```

否则 marker 可能仍指向旧 map，导致新 map 上看不到点。

## 文件预览 401

使用 SDK 的 authed URL 能力，不要手写带 token 的外部 URL。普通 REST 和 Socket.IO 鉴权交给 SDK。

## 自定义组件后回答按钮失效

替换 `ToolCall` 或 `AssistantTurn` 时，要继续传递 `onAnswer`、`answerData`、`sessionStatus`。否则 `AskUserQuestion` 的回答链路会断。

# 调试与排查

## 浏览器开发者工具

- **Network 面板**：检查 REST 请求（`/api/sessions` 等）和 Socket.IO 连接状态
- **Console**：SDK 的错误和警告会输出到控制台
- **WS 面板**：查看 Socket.IO 的 `chat:send`、`turn:*`、`chat:end` 等事件

## SDK 日志

Socket.IO 事件可以在回调中打印调试信息：

```ts
const socket = client.socket()
socket.on("turn:start", (p) => console.log("[turn:start]", p))
socket.on("turn:patch", (p) => console.log("[turn:patch]", p))
socket.on("turn:end", (p) => console.log("[turn:end]", p))
socket.on("chat:end", (p) => console.log("[chat:end]", p))
socket.on("system:error", (p) => console.error("[system:error]", p))
socket.on("connect_error", (err) => console.error("[connect_error]", err.message))
```

## 常见问题

### 鉴权失败（401）

**原因**：Token 过期、被吊销或未创建。

**修复**：
- 确认 token 格式为 `sk-blade-v2-...`
- 重新在网页端或 SDK 创建 API Key
- 本地 mock 环境先访问 `/api/auth/login` 获取登录态

### WebSocket 连接失败

**现象**：REST API 返回 200，但 ChatView 显示"暂时无法建立连接"。

**排查**：
- `baseUrl` 是否是后端 origin，且不带 pathname
- Token 是否同时用于 REST 和 Socket.IO（用同一个 `BladeClient` 实例）
- 换 token 后是否重连 socket
- 后端 CORS 是否放行宿主 origin

```ts
// 换 token 后重连
const socket = client.socket()
socket.disconnect()
socket.connect()
```

### 消息无响应

**ChatView 能看历史但发不出消息**：
- 切换 session 后没调用 `useSessionStore.getState().setActiveSession(sessionId)`
- Socket 没有订阅当前 session

**Agent 不执行工具**：
- 检查是否传了 `mode: "executing"`
- 检查角色 `initial_mode` 是否为 `planning`

### 文件上传失败

- Node 报 `client.uploadFile is not a function`：改用 `client.sessions.uploadFiles(session_id, ".", files)`
- Node 报 `client.workspaces` 是 undefined：同上
- Agent 找不到文件：确认 `uploaded` 路径与消息中路径一致
- 鉴权失败：REST 上传同样需要 `Authorization: Bearer ...`

### 白屏 / 无限渲染

**原因**：Zustand selector 每次返回新的数组或对象。

**修复**：使用稳定的空值常量：

```ts
const EMPTY_ITEMS: Item[] = []
const items = useStore((state) => state.items[id] ?? EMPTY_ITEMS)
```

### 样式异常

**原因**：
- 没有导入 `@blade-hq/agent-kit/style.css`
- 宿主写了全局 `button`、`input`、`svg` 等样式，污染 SDK 内部 UI

**修复**：
- 确认导入了 `import "@blade-hq/agent-kit/style.css"`
- 宿主样式限定到自己的容器（如 `.toolbar button`），不写全局选择器
- 只用 `classNames` / `components` / `renderers.tool` 自定义 SDK 样式

### 依赖安装冲突

**现象**：`npm install` 报 `ERESOLVE unable to resolve dependency tree`。

**修复**：

```bash
npm install @blade-hq/agent-kit@0.5.11 react@^19.0.0 react-dom@^19.0.0 @tanstack/react-query@^5.0.0 sonner@^2.0.7
```

不要用 React 18，不要用 `--force` 或 `--legacy-peer-deps`。

### 后端 SSE 接口超时

**原因**：
- 建立 socket 后没有立即写出任何 SSE 数据
- 没有监听 `connect_error` / `system:error`
- 没有 heartbeat
- 收到 `chat:end` 后没有结束响应

**修复**：
- `res.writeHead(200, ...)` 后立刻写出 `connected` 事件
- 至少转发 `turn:start`、`turn:patch`、`turn:end`、`chat:end`、`system:error`
- 用 `setInterval` 发送 heartbeat
- 在 `chat:end`、错误路径、`res.close` 中清理 socket

### 前端调用了不存在的 API

| 错误写法 | 正确做法 |
| --- | --- |
| `POST /api/chat` | 用 Socket.IO `chat:send` |
| `GET /sessions` | `client.sessions.listSessions()` |
| `POST /api/v1/sessions` | `client.sessions.createSession(...)` |
| `import { createClient } from "..."` | `new BladeClient({ baseUrl, token })` |
| `import ... from "@blade-hq/agent-kit"` | `from "@blade-hq/agent-kit/client"` |

### Node 报 ERR_PACKAGE_PATH_NOT_EXPORTED

**原因**：从包根导入或用了 `require`。

**修复**：
```ts
import { BladeClient } from "@blade-hq/agent-kit/client"
```

`package.json` 必须包含 `"type": "module"`。

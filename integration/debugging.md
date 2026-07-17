# 调试与排查

## 先分清是哪一层出问题

1. 打开浏览器 **Network 面板**，看 REST 请求（如 `/api/auth/me`、`/api/sessions`）的状态码：
   - 200 → 鉴权正常，问题在实时通道或前端渲染
   - 401 → 凭证问题，见下文
   - CORS 报错 → 后端未放行你的页面来源
2. 看 **WS 面板**（Network → WS）里的 `socket.io` 请求。101 = 连接已建立；其他状态码看响应体。
3. 在代码里打日志：

```ts
chat.subscribe(() => {
  const s = chat.getState()
  console.log("[state]", s.connection, s.status, s.isStreaming)
})
chat.on("toolCall", (e) => console.log("[toolCall]", e.toolCall.name))
chat.on("chatEnd", (e) => console.log("[chatEnd]", e.status))
chat.on("error", (e) => console.error("[error]", e.message))
```

## 常见问题

### 找不到 BladeClient（React）

**报错**：`找不到 BladeClient：请在组件树外层包一个 <BladeProvider client={client}>`

**修复**：外层包 Provider，或直接给组件传 `client`：

```tsx
<BladeProvider client={client}><ChatView /></BladeProvider>
// 或
<ChatView client={client} />
```

### 找不到模块 @blade-hq/agent-kit

**原因**：用了已废弃的旧包。

**修复**：换成新包——核心用 `@blade-hq/agent-client`，React 组件与 hooks 用 `@blade-hq/agent-react`。

### 鉴权失败（401 / 403）

- 401：没有凭证或已失效。浏览器调 `await client.auth.login()`；自动化检查 `token` 是否传入且未过期（弹窗登录拿到的令牌 30 天有效）。
- 403：令牌对应的账号无权访问该资源（比如不是会话所有者）。

详见[登录配置](./frontend/login.md)。

### 登录弹窗被拦截

**报错**：`登录弹窗被浏览器拦截了。请允许本站打开弹窗后重试。`

**原因**：`login()` 不是在用户点击的回调里调用的（页面加载时自动调用会被当成弹窗广告）。

**修复**：把 `login()` 放进按钮的 click 回调；或让用户在浏览器设置里允许本站弹窗。

### 弹窗里报「来源未被允许」

**原因**：后端没把你的页面来源加入允许列表。

**修复**：管理员设置环境变量（逗号分隔多个来源，必须是不带路径的 origin）：

```bash
BLADE_SDK_AUTH_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

### CORS 报错

**现象**：控制台报 `No 'Access-Control-Allow-Origin' header`。

**修复**：管理员在后端 CORS 配置里加入你的页面来源；或把页面与后端部署到同域 / 走同域反向代理。

### 实时通道连不上

**现象**：`state.connection` 一直是 `connecting`，REST 却正常。

**排查**：

- `baseUrl` 必须是后端 origin（如 `http://<host>:8020`），不带路径，端口和协议要对
- REST 与实时通道共用同一个凭证，确认用的是同一个 `BladeClient` 实例
- 换令牌后要重连——用 `client.setToken(newToken)`，它会自动重建连接，不要手动改

### 消息无响应

**发不出消息**：看 `state.connection` 是否 `connected`、`state.isStreaming` 是否卡在 true（上一轮没结束时不能发新消息，先 `chat.stop()`）。

**智能体只说不做，不调工具**：

- 发送时显式传 `{ mode: "executing" }`
- 检查业务角色配置的初始模式是不是 `planning`

### 文件上传失败

- 报 `client.uploadFile is not a function`：改用 `client.sessions.uploadFiles(session_id, ".", files)`
- 智能体找不到文件：消息里的路径要与上传返回的 `uploaded` 路径一致
- 鉴权失败：REST 上传同样需要凭证，走 `client.sessions.*` 而不是裸 fetch

### 样式异常（React）

**原因**：

- 没有导入 `@blade-hq/agent-react/style.css`
- 宿主写了全局 `button`、`input`、`svg` 等样式，污染了组件内部 UI

**修复**：

- 确认导入了 `import "@blade-hq/agent-react/style.css"`
- 宿主样式限定到自己的容器（如 `.toolbar button`），不写全局选择器
- 只用 `classNames` / `components` / `renderers` 定制组件外观

### ChatView 高度塌陷 / 不滚动

**原因**：外层容器没有确定高度。

**修复**：外层给 `height`（如 `100vh`），且是可收缩的 flex 容器：

```css
height: 100vh;
display: flex;
flex-direction: column;
min-height: 0;
overflow: hidden;
```

### Vue 界面不更新

**原因**：用了深层 `ref` 包裹，或直接改了状态快照内部字段。

**修复**：用 `shallowRef`，在 `subscribe` 回调里整体赋值：

```ts
const state = shallowRef(chat.getState())
chat.subscribe(() => { state.value = chat.getState() })
```

### 页面协作指令收不到

- action 拼写要与技能工具返回的 `_meta.bridge.action` **完全一致**
- 确认技能工具确实返回了 `_meta.bridge`（见[页面协作](./frontend/host-integration.md)）
- 指令处理函数里报错会被 SDK 吞掉只告警，看控制台

### Node 脚本跑完不退出

**原因**：实时连接还开着。

**修复**：拿到结果后 `client.socket().disconnect()`，或显式 `process.exit(0)`。

### Node 报 ERR_REQUIRE_ESM / require is not defined

**原因**：包是 ESM，项目用了 CommonJS。

**修复**：`package.json` 加 `"type": "module"`，用 `import` 而非 `require`。

## 不要这样做

| 错误写法 | 正确做法 |
| --- | --- |
| `import { BladeClient } from "@blade-hq/agent-kit/client"` | `import { BladeClient } from "@blade-hq/agent-client"` |
| `import { ChatView } from "@blade-hq/agent-kit/chat"` | `import { ChatView } from "@blade-hq/agent-react"` |
| `fetch("/api/sessions", { headers: { Authorization: ... } })` | `client.api.post("/api/sessions", ...)` |
| 手动 `io(baseUrl)` 连 Socket.IO 自己拼事件 | `client.sessions.connect(sessionId)`，用返回的会话对象 |
| `POST /api/chat` 发消息 | `chat.send("...")` |
| `POST /api/v1/sessions` | `client.sessions.createSessionWithRequest({ intent })` |
| 在渲染期调用 `login()` | 放进按钮的 click 回调 |

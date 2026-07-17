# BladeClient 与 AgentSession 核心 API

`@blade-hq/agent-client` 是框架无关的核心包，浏览器和 Node.js 18+ 都能用。本文覆盖它的两个核心对象：`BladeClient`（连接与鉴权）和 `AgentSession`（一个会话的实时状态机）。

```bash
npm install @blade-hq/agent-client
```

## BladeClient：连接与鉴权

`BladeClient` 是与 Blade 后端的连接入口，持有鉴权凭证和一条共享的 Socket.IO 实时连接。

```ts
import { BladeClient } from "@blade-hq/agent-client"

// 方式一：浏览器，先不带凭证，之后弹窗登录
const client = new BladeClient({ baseUrl: "https://blade.example.com" })

// 登录必须由用户点击触发：浏览器会拦截非用户操作弹出的窗口
loginButton.addEventListener("click", async () => {
  await client.auth.login()   // 用户点"许可授权"后自动拿到访问令牌（30 天有效）
})

// 方式二：自动化 / Node.js，直接填访问令牌（也叫 PAT，一个 sk-blade- 开头的长期密钥，
// 代表某个用户的身份，在 Blade 账号设置页创建。浏览器里绝对不要这么用，见 auth.md）
const client2 = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-xxx",
})

// 方式三：页面与后端同域部署，直接复用浏览器 cookie
const client3 = new BladeClient({ baseUrl: "" })  // 空字符串 = 当前域名
```

构造参数（`BladeClientOptions`）：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `baseUrl` | string | 后端地址（域名+端口，不带路径）。浏览器里传空字符串则用当前域名 |
| `token` | string 或 `() => string \| null` | 访问令牌，可传 getter 支持运行时切换。不传则按 cookie 模式工作 |
| `tokenStorage` | `"local"` / `"memory"` | `login()` 取得的令牌存放位置，默认 `"local"`（localStorage，刷新不掉登录） |
| `fetchImpl` | typeof fetch | 自定义 fetch 实现（测试、代理场景） |

::: warning baseUrl 填哪个地址（最容易踩的坑）
必须是 **Blade Agent 后端**的地址，形如 `http://<主机>:8020`，只要域名和端口、不带路径。

别填成你平时打开的 **Blade OS** 地址（同一台主机的 `:80` 端口）——那是另一套接口（前缀 `/api/v1/*`），SDK 连不上。
:::

常用方法与属性：

| 成员 | 说明 |
| --- | --- |
| `client.auth.login(options?)` | 弹窗授权登录（推荐入口）。`client.login()` 是等价别名。仅浏览器可用 |
| `client.setToken(token)` | 换访问令牌，REST 与实时连接立即用上新凭证（传 `null` 表示清除） |
| `client.hasToken()` | 当前是否持有令牌（不代表一定有效） |
| `client.socket()` | 取底层实时连接。日常用不到；**Node 脚本跑完要用 `client.socket().disconnect()` 让进程退出** |
| `client.sessions` | 会话资源：连接 / 创建 / 列表 / 文件（见下文与 rest-api.md） |
| `client.skills` | 技能资源：列表 / 搜索 / 会话技能上传。**技能** = 给智能体用的一组业务工具（查 CRM、操控地图等），由技能作者编写 |
| `client.headless` | 一次性任务：`run(prompt, { schema? })`，见 node.md |
| `client.auth` | 登录态：`getMe()`、`login()`、`logout()` |
| `client.api` | 通用 REST 通道：`get/post/put/patch/del`，其余不常用的接口对照 Swagger 直接调 |

REST 请求失败会抛出 `BladeApiError`（带中文诊断信息，401/403 会附上"怎么办"指引）。

### 退出登录的三个名字

| 写法 | 做什么 |
| --- | --- |
| `client.auth.logoutToken()` | **推荐**。清除本地存的访问令牌并断开实时连接。令牌本身在服务端仍有效直到过期 |
| `client.logoutToken()` | 同上，等价别名 |
| `useAuth().logout()`（React） | 同上，外加清空 hook 里的用户状态 |
| `client.auth.logout()` | **不一样**：调后端接口结束服务端登录态（cookie 会话），返回 `{ logout_url }` 供跳转 |

一般只需要 `logoutToken()`。cookie 同域部署且要真正登出整个 Blade 时才用 `auth.logout()`。

## AgentSession：会话实时状态机

`AgentSession` 代表一个会话（一次与智能体交互的完整上下文），封装了历史加载、实时订阅、断线重连后自动补齐漏掉的消息。对外只有三样东西：**状态快照**（`getState` / `subscribe`）、**动作**（`send` / `stop` / ...）、**事件**（`on` / `onCommand`）。

**会话**（session）= 一次与智能体交互的完整上下文：消息历史、工具调用记录，以及一个专属的工作目录（智能体能在里面读写文件）。

```ts
// 连接已有会话，或创建新会话
const chat = await client.sessions.connect(sessionId)
const chat2 = await client.sessions.create({ intent: "帮我分析这份报表" })
```

`create(req)` 等价于 `createSessionWithRequest(req)` + `connect()`：**两者参数完全相同**，区别只是 `create` 直接返回可对话的 `AgentSession`，而 `createSessionWithRequest` 只返回 `{ session_id }`。

### sessionId 从哪来

后端返回的字段名是 `session_id`（蛇形），前端参数名是 `sessionId`（驼峰），指同一个东西。三种来源：

1. **不用管它** —— 首次接入最省事：`client.sessions.create()` 直接建一个新会话，用不着 ID。
2. **自己建、自己存** —— 让用户下次回来接着上次聊：

   ```ts
   const { session_id } = await client.sessions.createSessionWithRequest({ intent: "季度报表分析" })
   // 把 session_id 存进你的数据库或 URL，下次传给 connect(session_id)
   ```

3. **列出用户已有的** —— `await client.sessions.listSessions()`，让用户自己挑。

不要凭空编一个 `"your-session-id"`：会话必须真实存在，否则 `connect()` 会 404。

### 状态快照

```ts
const state = chat.getState()
// {
//   sessionId,          // 会话 ID
//   messages,           // ChatMessage[]，UI 直接渲染的消息列表（日常只用这个）
//   turns,              // 服务端下发的原始记录，见下方说明（日常渲染用不到）
//   isStreaming,        // 智能体是否正在回复
//   status,             // 会话状态，见下表；尚未取得时为 null
//   mode,               // "planning" | "executing" | null，当前工作模式
//   connection,         // "connecting" | "connected" | "reconnecting" | "disconnected"
//   errorMessage,       // 最近一次运行错误
//   askAnswers,         // 已提交的 AskUserQuestion 作答（按 tool_call_id 索引）
//   agentLoops,         // 子智能体运行状态（智能体可以派生子智能体分头干活）
//   activeCompaction,   // 进行中的上下文压缩（对话太长时系统自动把旧内容压缩成摘要）
// }
```

`status` 的取值：`created` | `running` | `completed` | `failed` | `interrupted` | `waiting_for_input`；尚未从服务端取得时为 `null`。

::: tip turns 是什么
一个 **turn** = 智能体的一轮动作记录（说了什么、调了哪些工具）。`messages` 就是由 `turns` 加工成的、可直接渲染的列表。**日常渲染用 `messages` 就够，不用碰 `turns`。**
:::

```ts
const unsubscribe = chat.subscribe(() => {
  render(chat.getState())   // 状态不可变：每次变化产生新对象，未变化时引用相同
})
```

状态对象引用不可变，天然适配 React `useSyncExternalStore` 和 Vue `shallowRef`。

::: tip 断线了会怎样
实时连接断开时 SDK 会自动重连（期间 `state.connection` 是 `"reconnecting"`），重连后自动补齐断线期间漏掉的消息，**不需要你手动处理，也不会丢消息**。你可以拿 `connection` 给用户显示一个"连接中"提示，仅此而已。
:::

### 动作

```ts
await chat.send("你好")                          // 发送消息
await chat.send("换成英文再来一遍", { mode: "executing" })  // 显式指定工作模式
await chat.send([                                 // 多模态内容
  { type: "text", text: "看看这张图" },
  { type: "image_url", image_url: { url: "data:image/png;base64,..." } },
])

chat.append("补充：金额单位是万元")                 // 智能体运行中追加说明，不打断回复
await chat.stop()                                 // 停止当前回复
await chat.compact()                              // 手动触发上下文压缩

chat.attach("选中点位", { lng: 116.4, lat: 39.9 }) // 把业务数据作为附件放进输入框（需渲染层配合）
chat.insertText("请分析这个区域")                   // 往输入框追加文字（不发送）

chat.dispose()                                    // 释放订阅与监听器，之后不再接收事件
```

`send` 的第二个参数（`SendOptions`）：

| 字段 | 说明 |
| --- | --- |
| `mode` | `"planning"`（规划：只拆需求列计划，不动手）或 `"executing"`（干活：调工具做事）。不传时使用会话所属业务角色配置的初始模式——那由配置角色的人决定，前端看不到。**要智能体真的动手干活，就显式传 `mode: "executing"`，别依赖默认值。** |
| `askUserAnswer` | 回答智能体 AskUserQuestion 提问时携带（`tool_call_id` + 选项） |
| `model` | 本次运行的模型覆盖 |
| `thinkingOverride` | 本次运行强制开/关思考 |
| `whatif` / `replayDecision` | 内部回溯与回放机制使用，第三方接入无需关心 |

### 事件监听

```ts
chat.on("toolCall", ({ toolCall }) => console.log("调用工具:", toolCall.name))
chat.on("toolResult", ({ toolCall }) => console.log("工具结果:", toolCall.result))
chat.on("message", ({ message }) => console.log("新消息:", message.content))
chat.on("chatEnd", ({ status }) => console.log("回复结束:", status))
chat.on("error", ({ message }) => console.error(message))
chat.on("modeChange", ({ mode }) => console.log("切换到", mode))
```

完整事件表（`chat.on(name, handler)`，返回取消函数）：

| 事件 | 触发时机 |
| --- | --- |
| `message` | 一条消息接收完毕（不再流式更新） |
| `toolCall` | 智能体发起一次工具调用（首次出现） |
| `toolResult` | 一次工具调用出结果（done / error / cancelled） |
| `chatEnd` | 一轮回复结束，status: completed / paused / interrupted / failed |
| `error` | 运行错误（系统错误、发送失败等） |
| `modeChange` | planning / executing 模式切换 |
| `command` | 智能体给宿主页面下发指令（一般用 `onCommand` 消费，见下） |
| `notification` | 系统通知（技能阶段提示、后台任务启动等） |
| `workspaceChanged` | 工作区文件发生变化 |
| `artifact` | 智能体产出文件成果 |
| `toolPreview` | 工具返回可视化预览（HTML / URI） |
| `taskListUpdated` | 任务清单更新 |
| `backgroundTask` | 沙盒后台命令状态更新 |
| `rewind` | 会话被回溯到某个检查点 |
| `sessionUpdated` | 会话属性（名称、状态等）被服务端更新 |
| `sandboxOom` | 沙盒内存超限自动重启 |
| `replayMismatch` | 回放输入与历史不匹配，需决定保持回放还是转自主模式。**无人监听时 SDK 自动选择 `continue_replay`** |
| `attachRequested` | `attach()` 被调用，渲染层应把它显示为输入框附件 |
| `insertTextRequested` | `insertText()` 被调用，渲染层应把文字追加到输入框 |

### 页面协作指令

```ts
// 监听智能体下发给页面的指令。action 是技能作者与页面开发者约定的字符串，
// 详见 page-collaboration.md。注册前到达的指令会被缓冲，注册后立刻补发。
const off = chat.onCommand("map.highlight", (payload) => {
  // payload 类型是 unknown（内容由技能作者决定），用前自行断言或校验
  const { cityIds } = payload as { cityIds: string[] }
  map.highlight(cityIds)
})
```

## 一个页面多个会话

状态完全归属 `AgentSession` 实例：同一 `BladeClient` 下创建多个会话互不干扰，且共享同一条 Socket.IO 连接。会话实例由 client 缓存，重复 `connect(同一 id)` 返回同一实例；需要彻底释放时调用 `dispose()`。

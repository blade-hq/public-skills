---
name: agent-kit-sdk
description: "Blade 前端 SDK 集成：@blade-hq/agent-client（框架无关核心）与 @blade-hq/agent-react（React 绑定）。按 React、Vue、Node.js、iframe 嵌入场景引导接入。"
---

# Blade 前端 SDK 集成

Blade 前端 SDK 由两个 npm 包组成：

| 包 | 定位 | 运行环境 |
| --- | --- | --- |
| `@blade-hq/agent-client` | 框架无关核心：连接、登录、实时会话状态机、REST 通道、页面协作 | 浏览器 / Node.js 18+ 通用，运行时依赖只有 socket.io-client 与 arktype |
| `@blade-hq/agent-react` | React 绑定：`BladeProvider`、`useChat` 等 hooks、现成的 `ChatView` 聊天组件 | React 18 / 19 |

旧包 `@blade-hq/agent-kit` 已废弃，所有 `@blade-hq/agent-kit/client`、`/react`、`/chat` 入口不再使用。

## 使用规则

如果你不确定某个 SDK 入口、方法名、事件名、REST 路径或返回字段，必须先回到本技能的 reference 文档查找确认；不要按常见框架经验猜测 Blade API。文档没有明确写出的 Blade 接口、SDK 方法或包入口，不要自行发明。

其余不常用的接口（SDK 未提供类型化方法的）统一用 `client.api.get/post/...` 调用，路径和请求体对照后端 Swagger（`<后端地址>/docs`）确认。

## 先跑起来（React）

React 应用嵌一个完整聊天界面，这些就够了——不用先研究鉴权：

```bash
npm install @blade-hq/agent-client @blade-hq/agent-react react react-dom
```

```tsx
import { BladeClient } from "@blade-hq/agent-client"
import { BladeProvider, ChatView } from "@blade-hq/agent-react"
import "@blade-hq/agent-react/style.css"

// 建在组件外面：写进组件里的话每次重渲染都会新建 client、重连一次，聊天会疯狂闪断
const client = new BladeClient({ baseUrl: "https://blade.example.com" })

export default function App() {
  // ChatView 会撑满父容器，父容器没高度就什么都看不见
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <BladeProvider client={client}>
        <ChatView />
      </BladeProvider>
    </div>
  )
}
```

- `baseUrl` 填 **Blade Agent 后端**地址（形如 `http://<主机>:8020`，只要域名+端口，不带路径）。别填成你平时打开的 Blade OS 地址（同主机 `:80`）——那是另一套接口，SDK 连不上。
- 不传 `sessionId` 会自动建新会话；用户没登录时 `ChatView` 自己显示登录按钮。
- 页面与后端同域时，登录不用配任何东西。**只有部署到第三方域名**才需要读 [references/auth.md](references/auth.md)。

## 选包决策树

```
你的场景是什么？
│
├─ React 应用，想直接嵌一个聊天界面
│    → @blade-hq/agent-react 的 <ChatView>（见上面"先跑起来"）
│    → 读 references/react.md
│
├─ React 应用，想自己画聊天 UI
│    → @blade-hq/agent-react 的 useChat / useAgentSession
│    → 读 references/react.md + references/client-core.md
│      + references/message-rendering.md（必读：消息结构与渲染坑）
│
├─ Vue / Svelte / 无框架页面
│    → @blade-hq/agent-client 的 AgentSession（getState/subscribe）
│    → 读 references/vue.md + references/client-core.md
│      + references/message-rendering.md（必读：消息结构与渲染坑）
│
├─ Node.js 后端 / 自动化脚本
│    → @blade-hq/agent-client（headless.run、sessions、api）
│    → 读 references/node.md
│
└─ 用 iframe 把 Blade 聊天页嵌进自己系统
     → @blade-hq/agent-client 的 connectEmbedded()
     → 读 references/embedded-iframe.md
```

## 参考文档

- [references/client-core.md](references/client-core.md)：`BladeClient` 与 `AgentSession` 完整 API——连接、sessionId 从哪来、状态订阅、发送、事件监听。所有场景的基础。
- [references/message-rendering.md](references/message-rendering.md)：**自建 UI 必读**——消息结构、多模态 content、工具调用渲染、四个 status 的区别、智能体反问时怎么作答。
- [references/react.md](references/react.md)：React 接入——`BladeProvider`、`ChatView`、`useChat`、`useAgentSession`、`useAuth`、样式与预览组件。
- [references/vue.md](references/vue.md)：Vue 接入——`useAgentSession` composable 参考实现、流式渲染、工具调用消费。
- [references/node.md](references/node.md)：Node.js / 自动化——`headless.run` 一次性问答、会话管理、文件上传。
- [references/auth.md](references/auth.md)：三种登录方式对比、访问令牌、后端 `BLADE_SDK_AUTH_ALLOWED_ORIGINS` 配置。**部署到第三方域名时才需要读。**
- [references/page-collaboration.md](references/page-collaboration.md)：页面协作——智能体驱动页面（`onCommand`）、页面反向注入（`attach` / `insertText`）、action 契约的来源。
- [references/embedded-iframe.md](references/embedded-iframe.md)：iframe 嵌入形态——`connectEmbedded` 用法与安全要求。
- [references/rest-api.md](references/rest-api.md)：REST 通道——类型化资源方法速查 + `client.api` 其余不常用的接口调用。
- [references/troubleshooting.md](references/troubleshooting.md)：常见报错 → 原因 → 修复。

## 交付自检

交付前列出你实际采用的：包名与入口、client 构造方式、鉴权方式、会话创建/连接方法、消息发送方式、事件消费方式。每一项都必须能在上述 reference 文档中找到依据；任一项找不到依据时，先查文档或改用文档中的示例，不要交付猜测实现。

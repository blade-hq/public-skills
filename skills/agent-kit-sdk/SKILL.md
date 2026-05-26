---
name: agent-kit-sdk
description: "帮助第三方开发者在自己的 React 应用中接入 Blade Agent 前端 SDK（@blade-hq/agent-kit）。当用户要安装 SDK、配置 BladeClientProvider、嵌入 ChatView、使用 useChat/headless API、自定义 ChatView 样式或渲染、接入 skills/@skill mention/SkillStatusBar 时使用本技能。"
---

# Agent Kit SDK 集成指南

本技能面向使用 `@blade-hq/agent-kit` 的第三方开发者。目标是把 Blade Agent 的聊天、会话、文件预览、skills 和流式消息能力嵌入到宿主 React 应用中，而不是修改 SDK 源码。

## 版本要求

本技能基于以下版本或以上：

- 阿里云镜像：`registry.cn-beijing.aliyuncs.com/bladeai/blade-agent:v0.4.7`
- NPM：`@blade-hq/agent-kit@0.4.7`
- PyPI：`blade-agent-kit==0.4.7`

低于上述版本时，部分 API、样式入口或 skills 行为可能不一致，请先升级再按本技能集成。

## 先确认集成目标

先问清楚或从代码中判断：

- 宿主应用是否是 React；如果不是，优先使用 `@blade-hq/agent-kit/client` 自行渲染 UI。
- 认证方式是 cookie 会话还是 Bearer Token。
- 需要完整 `ChatView`，还是只需要 `useChat(sessionId)` 的 headless 数据流。
- 是否需要让用户选择或调用 skills。
- 是否需要自定义 ChatView 的样式、消息组件、工具调用渲染或技能状态栏。

## 安装与入口

React 应用通常安装：

```bash
npm install @blade-hq/agent-kit @tanstack/react-query react react-dom sonner
```

注意：

- SDK 依赖 React 19；宿主项目仍在 React 18 时，先升级 React / React DOM / types。
- pnpm 10 可能拦截 esbuild 等依赖的 build script；如果安装后构建失败，检查 `pnpm.onlyBuiltDependencies`。
- 使用动画 Dock 或浮窗时，宿主可能还需要安装自己的动画库；不要假设 SDK 会带上宿主 UI 依赖。

应用入口导入样式：

```ts
import "@blade-hq/agent-kit/style.css"
```

如果只使用 `/client` 或 hooks 自己渲染 UI，可以不导入这份样式。

## Client 与 Provider

首方或同域 cookie 会话：

```tsx
import { BladeClient } from "@blade-hq/agent-kit/client"
import { BladeClientProvider } from "@blade-hq/agent-kit/react"

const client = new BladeClient({
  baseUrl: "https://blade.example.com",
})

export function App() {
  return (
    <BladeClientProvider client={client}>
      <YourRoutes />
    </BladeClientProvider>
  )
}
```

第三方 Bearer Token：

```tsx
const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-xxx",
})
```

不要把 token 拼进普通 API URL；SDK 会为 REST 和 Socket.IO 处理鉴权。只有文件预览这类无法设置 header 的场景才使用 SDK 提供的 authed URL 能力。

`baseUrl` 必须是 origin，不要带 pathname。错误示例：`http://localhost:5173/agent-api`。Socket.IO 客户端会把 pathname 当 namespace，容易报 `Invalid namespace`。开发环境优先直连 BA 后端 origin，例如 `http://localhost:8020`，并让 BA CORS 放行宿主应用 origin。

如果 token 来自用户自己的 BA API key，推荐用 getter 从宿主 auth store 读取，避免热更新或刷新后重建 client：

```tsx
const client = new BladeClient({
  baseUrl,
  token: () => authStore.getState().token,
})
```

## 嵌入 ChatView

完整聊天窗口：

```tsx
import { ChatView } from "@blade-hq/agent-kit/chat"

export function AgentPanel({ sessionId }: { sessionId: string }) {
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <ChatView sessionId={sessionId} />
    </div>
  )
}
```

`ChatView` 默认处理：

- 历史消息加载
- Socket.IO 流式更新
- 输入框和停止生成
- 文件附件
- `/` skill command 和 `@skill` mention
- `AskUserQuestion` 回答
- 滚动到底部和 turn navigation

布局要求：`ChatView` 外层必须是能收缩的 flex 容器，至少包含 `min-height: 0`、`display: flex`、`flex-direction: column`、`overflow: hidden`。否则消息区可能只占半高，输入框顶在中间。

多 session / 多角色场景下，只把 `sessionId` 传给 `<ChatView>` 不够。宿主自己的 session store 负责业务选择，SDK 的 `useSessionStore` 负责 socket 订阅；切换 session 后要同步 SDK active session：

```tsx
import { useSessionStore } from "@blade-hq/agent-kit/react"

useEffect(() => {
  if (sessionId) {
    useSessionStore.getState().setActiveSession(sessionId)
  }
}, [sessionId])
```

如果宿主自己创建 session，也要把返回的 session 信息写入 SDK session store，否则列表、状态和订阅可能不同步。

## 自定义样式与渲染

轻量改样式用 `classNames`：

```tsx
<ChatView
  sessionId={sessionId}
  classNames={{
    root: "bg-white text-slate-950",
    messageListContent: "max-w-4xl",
    userMessage: "text-right",
    assistantText: "text-base leading-7",
    chatInputRoot: "border-t",
  }}
/>
```

替换语义组件用 `components`：

```tsx
<ChatView
  sessionId={sessionId}
  components={{
    EmptyState: () => <div className="py-16 text-center">开始一个新任务</div>,
    SkillStatusBar: ({ sessionId }) => <div>当前会话：{sessionId}</div>,
  }}
/>
```

替换特定工具调用渲染用 `renderers.tool`：

```tsx
import type { ToolRendererProps } from "@blade-hq/agent-kit/chat"

function BashTool({ toolCall }: ToolRendererProps) {
  return <pre>{toolCall.arguments}</pre>
}

<ChatView
  sessionId={sessionId}
  renderers={{
    tool: {
      Bash: BashTool,
    },
  }}
/>
```

原则：

- 只改视觉时用 `classNames`。
- 需要替换消息、空态、技能状态栏等完整节点时用 `components`。
- 需要按 tool 名称替换内容展示时用 `renderers.tool`。
- 不要依赖 SDK 内部 DOM 层级；优先使用公开 props 和导出的类型。

## Headless 用法

如果宿主应用要完全自建聊天界面，使用 hooks / client：

```tsx
import { useChat } from "@blade-hq/agent-kit/react"

function CustomChat({ sessionId }: { sessionId: string }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)
  // 自行渲染 messages，并调用 send / stop
}
```

纯网络客户端适合非 React 或服务端脚本：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({ baseUrl, token })
const sessions = await client.sessions.listSessions()
```

如果直接使用底层 socket：

- 进入页面后 `session:subscribe`，离开时 `session:unsubscribe`。
- 监听 `turn:start` / `turn:patch` / `turn:end` 拼接消息。
- 无附件时 `chat:send` 的 `message` 用纯字符串，不要包装成 `{ content: [...] }`。

## Skills 接入

默认 `ChatView` 已包含 skills 相关体验：

- `/` 命令可触发技能相关菜单。
- `@skill` mention 可引用可用技能。
- `SkillStatusBar` 展示当前会话技能状态。
- skill 相关 tool calls 会在消息流中渲染。

宿主应用如果需要自定义 skills 入口：

- 用 `useSkills()` 或 `skillsApi` 获取/搜索 skills。
- 用 `components.SkillStatusBar` 替换默认状态栏。
- 不要在前端伪造 Blade Agent 专属 socket event；skills 的可见性和加载状态应以后端 API 和消息流为准。

## 集成顺序

推荐按这个顺序落地：

1. 先在最小 React 页面跑通 `BladeClientProvider` + 单个 `<ChatView>`，确认能发能收。
2. 再接 session 列表和创建会话。
3. 再接宿主业务的多角色 / 多席位 / 多工作区映射，并同步 SDK `activeSessionId`。
4. 最后做 Dock、动画、Tab、主题和自定义渲染。

不要先做复杂壳层再接 socket/session；排查范围会很大。

## 集成 Checklist

- [ ] React / React DOM / types 已升级到 SDK 要求的版本。
- [ ] 入口导入了 `@blade-hq/agent-kit/style.css`。
- [ ] `baseUrl` 是 BA 后端 origin，不带 pathname。
- [ ] BA 后端 CORS 放行宿主应用 origin。
- [ ] Bearer Token 来自 BA API key 或可信后端下发，没有硬编码在源码里。
- [ ] 多 session 场景调用了 SDK `useSessionStore.getState().setActiveSession(sessionId)`。
- [ ] 新建 session 后同步写入 SDK session store。
- [ ] `ChatView` 外层 flex 容器有 `min-height: 0` 和 `overflow: hidden`。
- [ ] 使用底层 socket 时，无附件 `chat:send.message` 是纯字符串。
- [ ] 没有往 BA socket 添加宿主业务专属事件；业务数据变化走宿主自己的 API / event bus。

## 常见问题

- **ChatView 没有样式**：确认入口导入了 `@blade-hq/agent-kit/style.css`。
- **Socket 连接失败 / Invalid namespace**：确认 `BladeClient` 的 `baseUrl` 只包含 origin，没有 `/agent-api` 这类 pathname，并检查 cookie/token 和后端 CORS 配置。
- **ChatView 能看历史但发不出消息**：确认宿主 session 切换时同步调用了 SDK `setActiveSession(sessionId)`。
- **ChatView 高度不对**：确认外层是 `flex flex-col min-h-0 overflow-hidden`。
- **文件预览 401**：使用 SDK 的 authed URL 能力，不要手写带 token 的外部 URL。
- **自定义组件后回答按钮失效**：替换 `ToolCall` 或 `AssistantTurn` 时，要继续传递 `onAnswer`、`answerData`、`sessionStatus`。
- **skills 看不到**：确认后端已发现/安装对应 skills，并通过 `skillsApi` 或 `useSkills()` 验证列表。

# React 接入

::: tip 完整示例工程
[下载 examples-react.zip](/public-skills/downloads/examples-react.zip) — Vite + React 19 可运行工程，填好 `.env.local` 即可 `pnpm dev`。
:::

## 安装与依赖

版本号需和 Blade Agent 后端一致（[如何查看](/integration/concepts#快速开始)）：

```bash
# 将 <version> 替换为后端版本号，如 1.0.10
pnpm add @blade-hq/agent-kit@<version> react@^19.0.0 react-dom@^19.0.0 @tanstack/react-query@^5.0.0 sonner@^2.0.7
```

::: warning 版本要求
- 必须使用 React 19，不支持 React 18
- 不要用 `--force` 或 `--legacy-peer-deps` 绕过依赖检查
:::

## 导入入口

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"
import { BladeClientProvider, useSessionStore } from "@blade-hq/agent-kit/react"
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"
```

不要从包根 `@blade-hq/agent-kit` 导入。

## BladeClientProvider 配置

用 `BladeClientProvider` 包裹应用，提供 `baseUrl` 和 `token`：

```tsx
import { BladeClientProvider } from "@blade-hq/agent-kit/react"

function App() {
  return (
    <BladeClientProvider
      baseUrl="http://<host>:8020"
      token={() => localStorage.getItem("blade-token")}
    >
      <YourApp />
    </BladeClientProvider>
  )
}
```

`baseUrl` 必须是后端 origin，不带 pathname。

也可以用 `bootstrapBladeClient` 预创建 client 实例，适合需要在 Provider 外部访问 client 的场景：

```tsx
import { bootstrapBladeClient, BladeClientProvider } from "@blade-hq/agent-kit/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const client = bootstrapBladeClient({
  baseUrl: import.meta.env.VITE_BLADE_URL,
  token: import.meta.env.VITE_BLADE_TOKEN,
})
const queryClient = new QueryClient()

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <BladeClientProvider client={client}>
      <App />
    </BladeClientProvider>
  </QueryClientProvider>,
)
```

## ChatView 最小示例

```tsx
import { useState } from "react"
import { sessionsApi, useSessionStore } from "@blade-hq/agent-kit/react"
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"

export function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)

  async function createSession() {
    const { session_id } = await sessionsApi.createSession("我的任务")
    setSessionId(session_id)
    useSessionStore.getState().setActiveSession(session_id)
  }

  return (
    <main style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <button onClick={createSession}>新建会话</button>
      {sessionId ? <ChatView sessionId={sessionId} /> : null}
    </main>
  )
}
```

::: tip 布局要求
`ChatView` 的外层容器必须是可收缩的 flex 容器，至少包含 `height`、`min-height: 0`、`display: flex`、`flex-direction: column`、`overflow: hidden`。
:::

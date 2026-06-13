# React 接入

## 安装与依赖

```bash
npm install @blade-hq/agent-kit@0.5.11 react@^19.0.0 react-dom@^19.0.0 @tanstack/react-query@^5.0.0 sonner@^2.0.7
```

对应 `package.json`：

```json
{
  "type": "module",
  "dependencies": {
    "@blade-hq/agent-kit": "0.5.11",
    "@tanstack/react-query": "^5.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "sonner": "^2.0.7"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.0.0"
  }
}
```

::: warning 版本要求
- 必须使用 React 19，不支持 React 18
- 不要写 `@blade-hq/agent-kit@^1.0.0`（不存在）
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
      baseUrl="http://localhost:8020"
      token={() => localStorage.getItem("blade-token")}
    >
      <YourApp />
    </BladeClientProvider>
  )
}
```

`baseUrl` 必须是后端 origin，不带 pathname。

## ChatView 最小示例

```tsx
import { useMemo, useState } from "react"
import { BladeClient } from "@blade-hq/agent-kit/client"
import { BladeClientProvider, useSessionStore } from "@blade-hq/agent-kit/react"
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"

export function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const client = useMemo(
    () => new BladeClient({ baseUrl: "http://localhost:8020", token: () => token }),
    [],
  )

  async function createSession() {
    const { session_id } = await client.sessions.createSession("我的任务")
    setSessionId(session_id)
    useSessionStore.getState().setActiveSession(session_id)
  }

  return (
    <BladeClientProvider baseUrl="http://localhost:8020" token={() => token}>
      <main style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
        <button onClick={createSession}>新建会话</button>
        {sessionId ? <ChatView sessionId={sessionId} /> : null}
      </main>
    </BladeClientProvider>
  )
}
```

::: tip 布局要求
`ChatView` 的外层容器必须是可收缩的 flex 容器，至少包含 `height`、`min-height: 0`、`display: flex`、`flex-direction: column`、`overflow: hidden`。
:::

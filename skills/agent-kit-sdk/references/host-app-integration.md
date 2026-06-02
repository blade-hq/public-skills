# 宿主页面联动

本文说明宿主应用如何和 Blade Agent 聊天区、工具结果互相联动。

## 宿主页面 → ChatView

React 宿主优先使用 SDK store：

```tsx
import { useEffect } from "react"
import { useSessionStore, useUiBridgeStore } from "@blade-hq/agent-kit/react"

// 在 useEffect 或事件回调中同步 active session，不要在渲染期直接调用
useEffect(() => {
  useSessionStore.getState().setActiveSession(sessionId)
}, [sessionId])

// 事件回调示例：用户在宿主页面选中地图区域后
function handleMapSelection() {
  useUiBridgeStore.getState().addPendingContext(sessionId, {
    label: "地图选区 · 2 座城市",
    content: "hangzhou, ningbo",
  })
  useUiBridgeStore.getState().addDraftAppend(sessionId, "请高亮这些城市。")
}
```

可用能力：

- `addPendingContext(sessionId, { label, content })`：在输入框上方加入上下文 pill，发送时合并进消息。
- `addDraftAppend(sessionId, text)`：向当前输入框追加文本。
- `addSendRequest(sessionId)`：请求发送当前输入框内容。

Vue / 原生页面不能直接使用 React store 时，需要自己维护输入框和上下文，并在发送时把上下文合并进消息。

## 工具结果 → 宿主页面

工具可以返回页面动作：

```json
{
  "ok": true,
  "_meta": {
    "bridge": {
      "action": "map.highlight",
      "payload": { "cityIds": ["hangzhou", "ningbo"] }
    }
  }
}
```

React 宿主可从 `useGisStore` 消费 `map.*` 命令：

```tsx
import { useEffect } from "react"
import { useGisStore } from "@blade-hq/agent-kit/react"
import type { GisMapCommand } from "@blade-hq/agent-kit/react"

const EMPTY_COMMANDS: GisMapCommand[] = []

const commands = useGisStore((state) =>
  sessionId ? state.pendingMapCommandsBySession[sessionId] ?? EMPTY_COMMANDS : EMPTY_COMMANDS,
)

// 在 useEffect 中消费命令，避免渲染期写 store
useEffect(() => {
  for (const command of commands) {
    if (command.action === "map.highlight") {
      highlightOnMap(command.payload)
    }
    useGisStore.getState().consumeMapCommand(sessionId, command.id)
  }
}, [commands, sessionId])
```

React 19 下 selector 不要每次返回新的 `[]`，要使用稳定的空数组常量。

## 工具结果 → ChatView UI

工具可以返回可视化卡片：

```json
{
  "_meta": {
    "ui": {
      "resourceHTML": "<!doctype html>...",
      "target": "inline",
      "height": 320,
      "title": "地图高亮预览"
    }
  }
}
```

字段：

- `resourceHTML`：完整 HTML 文档，用 iframe `srcdoc` 渲染。
- `resourceUri`：外部 URL，用 iframe `src` 渲染。
- `target`：`inline` 或 `preview`。
- `height`：iframe 高度。
- `title`：卡片标题。

`resourceUri` 页面需要允许被 iframe 嵌入，检查 `X-Frame-Options` 和 CSP `frame-ancestors`。

## iframe / postMessage

iframe 嵌入方案可以使用统一信封：

```ts
interface BladeBridgeEnvelope {
  __bladeBridge: true
  direction: "host-to-agent" | "agent-to-host"
  action: string
  payload?: unknown
  meta?: {
    sessionId?: string
    toolCallId?: string
    timestamp?: number
  }
}
```

宿主 → Agent 常见 action：

- `addContext`
- `appendInput`
- `sendMessage`
- `uploadSessionSkill`

React 宿主优先用 SDK store；iframe 宿主才优先用 postMessage。

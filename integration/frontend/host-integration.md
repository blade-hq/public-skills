# 宿主页面联动

宿主应用和智能助手之间可以双向通信：宿主向助手注入上下文和输入，助手通过工具结果驱动宿主页面。

## 宿主 -> 智能助手

### 注入上下文

在输入框上方添加上下文 pill，发送时自动合并进消息：

```tsx
import { useUiBridgeStore } from "@blade-hq/agent-kit/react"

function handleMapSelection() {
  useUiBridgeStore.getState().addPendingContext(sessionId, {
    label: "地图选区 - 2 座城市",
    content: "hangzhou, ningbo",
  })
}
```

### 追加输入

向当前输入框追加文本：

```tsx
useUiBridgeStore.getState().addDraftAppend(sessionId, "请高亮这些城市。")
```

### 请求发送

触发发送当前输入框内容：

```tsx
useUiBridgeStore.getState().addSendRequest(sessionId)
```

### 切换活跃会话

```tsx
import { useSessionStore } from "@blade-hq/agent-kit/react"
import { useEffect } from "react"

// 在 useEffect 或事件回调中调用，不要在渲染期直接调用
useEffect(() => {
  useSessionStore.getState().setActiveSession(sessionId)
}, [sessionId])
```

## 智能助手 -> 宿主

### Bridge Action

工具返回值中包含 `_meta.bridge` 时，SDK 会分发给宿主页面：

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

React 宿主消费 bridge 命令：

```tsx
import { useEffect } from "react"
import { useGisStore } from "@blade-hq/agent-kit/react"
import type { GisMapCommand } from "@blade-hq/agent-kit/react"

const EMPTY_COMMANDS: GisMapCommand[] = []

const commands = useGisStore((state) =>
  sessionId ? state.pendingMapCommandsBySession[sessionId] ?? EMPTY_COMMANDS : EMPTY_COMMANDS,
)

useEffect(() => {
  for (const command of commands) {
    if (command.action === "map.highlight") {
      highlightOnMap(command.payload)
    }
    useGisStore.getState().consumeMapCommand(sessionId, command.id)
  }
}, [commands, sessionId])
```

::: warning
Zustand selector 不要每次返回新的 `[]`，要使用稳定的空数组常量（如上面的 `EMPTY_COMMANDS`），否则 React 19 下会触发无限渲染。
:::

### 可视化卡片

工具返回 `_meta.ui` 时，ChatView 会渲染 iframe 卡片：

```json
{
  "_meta": {
    "ui": {
      "resourceHTML": "<!doctype html><html>...</html>",
      "target": "inline",
      "height": 320,
      "title": "地图高亮预览"
    }
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `resourceHTML` | 完整 HTML 文档，用 iframe `srcdoc` 渲染 |
| `resourceUri` | 外部 URL，用 iframe `src` 渲染 |
| `target` | `inline`（消息内嵌）或 `preview`（侧边预览） |
| `height` | iframe 高度（px） |
| `title` | 卡片标题 |

## iframe postMessage

当智能助手嵌入 iframe 时，可以使用统一信封格式通信：

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

宿主 -> Agent 常见 action：

- `addContext` - 注入上下文
- `appendInput` - 追加输入
- `sendMessage` - 发送消息
- `uploadSessionSkill` - 上传会话技能

::: tip
React 宿主优先用 SDK store（`useUiBridgeStore`、`useGisStore`）；只有 iframe 嵌入场景才用 postMessage。
:::

# Vue 接入

::: tip 完整示例工程
[下载 examples-vue.zip](/public-skills/downloads/examples-vue.zip) — Vite + Vue 3 可运行工程，填好 `.env.local` 即可 `pnpm dev`。
:::

Vue 不能直接使用 `ChatView`（React 组件），需要用 `@blade-hq/agent-kit/client` 和底层 Socket.IO 自行渲染。

## 安装与依赖

版本号需和 Blade Agent 后端一致（[如何查看](/integration/concepts#快速开始)）：

```bash
# 将 <version> 替换为后端版本号，如 1.0.10
pnpm add @blade-hq/agent-kit@<version> vue@^3.5.13
```

Vue 只使用 `/client` 入口，不需要 React 相关依赖，也不需要导入 `style.css`。

## BladeClient 初始化

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const token = import.meta.env.VITE_BLADE_AGENT_TOKEN
const client = new BladeClient({
  baseUrl: "http://<host>:8020",
  token: () => token,
})
```

## Composable：useBladeChat

推荐封装一个 composable 管理会话状态。核心类型定义：

```ts
import { ref, shallowRef, readonly, triggerRef } from "vue"
import { BladeClient } from "@blade-hq/agent-kit/client"

export interface Turn {
  turn_id: string
  role: "user" | "assistant" | "system"
  status: string
  blocks: ContentBlock[]
  tool_calls: ToolCall[]
}

export interface ContentBlock {
  type: string
  content: unknown
  tool_call_id?: string | null
  tool_name?: string | null
  display_name?: string | null
}

export interface ToolCall {
  id: string
  tool_name: string
  display_name: string
  arguments: string
  status: "pending" | "done" | "error" | "cancelled" | "awaiting_answer"
  result?: unknown
  duration_ms?: number | null
}
```

核心实现：

```ts
export function useBladeChat(client: BladeClient) {
  const sessionId = ref("")
  const turns = shallowRef<Turn[]>([])
  const streaming = ref(false)
  const error = ref("")
  let socket: any = null

  function upsertTurn(turn: Turn) {
    const list = [...turns.value]
    const idx = list.findIndex((t) => t.turn_id === turn.turn_id)
    if (idx >= 0) list[idx] = turn
    else list.push(turn)
    turns.value = list
    triggerRef(turns)
  }

  async function createSession(intent: string) {
    const { session_id } = await client.sessions.createSession(intent)
    sessionId.value = session_id

    socket = client.socket()
    socket.on("turn:start", (p: Turn) => { upsertTurn(p); streaming.value = true })
    socket.on("turn:patch", (p: any) => { if (p?.data?.turn) upsertTurn(p.data.turn) })
    socket.on("turn:end", (p: Turn) => { upsertTurn(p) })
    socket.on("chat:end", async () => {
      streaming.value = false
      const fresh = await client.sessions.getSessionTurns(session_id)
      turns.value = fresh as Turn[]
      triggerRef(turns)
    })
    socket.on("system:error", (p: any) => {
      error.value = p?.message ?? "未知错误"
      streaming.value = false
    })

    socket.connect()
    socket.emit("session:subscribe", { session_id })
  }

  function send(message: string) {
    if (!socket || !sessionId.value) return
    socket.emit("chat:send", { session_id: sessionId.value, message, mode: "executing" })
    streaming.value = true
    error.value = ""
  }

  function stop() {
    if (socket && sessionId.value) socket.emit("chat:stop", { session_id: sessionId.value })
  }

  function destroy() {
    if (socket) {
      if (sessionId.value) socket.emit("session:unsubscribe", { session_id: sessionId.value })
      socket.disconnect()
      socket = null
    }
  }

  return { sessionId: readonly(sessionId), turns: readonly(turns), streaming: readonly(streaming), error: readonly(error), createSession, send, stop, destroy }
}
```

## 使用示例

```vue
<script setup lang="ts">
import { ref, onUnmounted } from "vue"
import { BladeClient } from "@blade-hq/agent-kit/client"
import { useBladeChat } from "./composables/useBladeChat"

const token = import.meta.env.VITE_BLADE_AGENT_TOKEN
const client = new BladeClient({ baseUrl: "http://<host>:8020", token: () => token })
const chat = useBladeChat(client)

chat.createSession("vue chat example")
onUnmounted(() => chat.destroy())
</script>

<template>
  <div>
    <div v-for="turn in chat.turns.value" :key="turn.turn_id">
      <strong>{{ turn.role }}</strong>
      <p v-for="block in turn.blocks.filter(b => b.type === 'text')" :key="block.content">
        {{ block.content }}
      </p>
    </div>
    <input @keydown.enter="chat.send($event.target.value)" placeholder="输入消息..." />
  </div>
</template>
```

## 提取文本的工具函数

```ts
export function extractText(blocks: unknown): string {
  if (!Array.isArray(blocks)) return ""
  return blocks
    .filter((b: any) => b?.type === "text")
    .map((b: any) => String(b.content ?? ""))
    .join("")
}
```

::: warning chat:send 类型问题
SDK 自动生成的类型把 `chat:send` 的 `message` 误标为对象，但后端实际接受字符串。传字符串时需要做一次类型断言：
```ts
import type { ChatSendPayload } from "@blade-hq/agent-kit/client"
socket.emit("chat:send", { session_id, message: text } as unknown as ChatSendPayload)
```
:::

::: tip 简化方案
如果不需要逐字流式动画，可以只在 `chat:end` 时调一次 `client.sessions.getSessionTurns(session_id)` 拿完整数据渲染，避免手动拼 `turn:patch`。
:::

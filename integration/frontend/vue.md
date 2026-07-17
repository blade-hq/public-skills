# Vue 接入

Vue 项目只需要框架无关的核心包 `@blade-hq/agent-client`。它把 Socket.IO 协议、历史加载、流式消息合并、断线重连全部封装成一个**会话对象**（`AgentSession`），你只面对"状态快照 + 动作 + 事件"。

```bash
npm install @blade-hq/agent-client
```

不需要 React 相关依赖，也不需要导入任何 CSS（聊天界面由你自己渲染）。

## 初始化 client

```ts
// client 建在模块作用域，不要放进组件 setup 里——
// 每次组件重建都会新建 client、重连一次，聊天会疯狂闪断
import { BladeClient } from "@blade-hq/agent-client"

export const client = new BladeClient({
  baseUrl: "https://blade.example.com",   // 后端地址（域名+端口，不带路径）
})
```

::: danger 不要把令牌写进前端
别写 `token: import.meta.env.VITE_BLADE_TOKEN`。`VITE_` 开头的环境变量**会被 Vite 明文编译进 JS 包**，等于把这个 Blade 账号公开给所有访客。令牌只用于 Node.js 后端等服务端场景。
:::

## 登录

浏览器里让用户走弹窗授权。**必须由用户点击触发**，否则会被浏览器当弹窗广告拦截：

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue"
import { client } from "./blade-client"

const user = ref<{ display_name?: string | null } | null>(null)

onMounted(async () => {
  try {
    user.value = await client.auth.getMe()   // 已登录（或 cookie 同域）时直接拿到用户
  } catch {
    user.value = null                        // 未登录，显示登录按钮
  }
})

async function handleLogin() {
  await client.auth.login()   // 用户点"许可授权"后令牌自动生效
  user.value = await client.auth.getMe()
}
</script>

<template>
  <button v-if="!user" @click="handleLogin">登录 Blade</button>
  <span v-else>你好，{{ user.display_name }}</span>
</template>
```

页面与后端同域部署时，cookie 自动生效，不需要登录按钮。三种登录方式（弹窗 / 令牌 / cookie 同域）的选择见[登录配置](./login.md)。

## useAgentSession composable

会话状态快照的引用是**不可变**的（每次变化产生新对象），所以配合 `shallowRef` 就能获得响应式渲染，不需要深层代理。下面是完整参考实现，可直接复制到 `src/composables/useAgentSession.ts`：

```ts
import { onUnmounted, shallowRef } from "vue"
import {
  createInitialSessionState,
  type AgentSession,
  type BladeClient,
  type MessageContent,
  type SendOptions,
  type SessionState,
} from "@blade-hq/agent-client"

/**
 * 连接（或创建）一个 Blade 会话并转成 Vue 响应式状态。
 * 传 sessionId 连接已有会话；不传则自动创建新会话。
 */
export function useAgentSession(client: BladeClient, sessionId?: string) {
  const session = shallowRef<AgentSession | null>(null)
  const state = shallowRef<SessionState>(createInitialSessionState(sessionId ?? ""))
  const error = shallowRef<Error | null>(null)

  let unsubscribe: (() => void) | null = null
  let cancelled = false

  const connecting = sessionId
    ? client.sessions.connect(sessionId)
    : client.sessions.create()

  connecting
    .then((chat) => {
      if (cancelled) return
      session.value = chat
      state.value = chat.getState()
      // 快照引用不可变：整体赋值即可触发更新，不要改动快照内部字段
      unsubscribe = chat.subscribe(() => {
        state.value = chat.getState()
      })
    })
    .catch((err: Error) => {
      if (!cancelled) error.value = err
    })

  onUnmounted(() => {
    cancelled = true
    unsubscribe?.()
  })

  return {
    session,   // AgentSession | null，用 session.value?.on(...) 监听事件
    state,     // 响应式会话快照
    error,
    send: (content: MessageContent, options?: SendOptions) => session.value?.send(content, options),
    append: (text: string) => session.value?.append(text),
    stop: () => session.value?.stop(),
  }
}
```

## 发送与流式渲染

```vue
<script setup lang="ts">
import { getImageParts, getTextContent } from "@blade-hq/agent-client"
import { computed, ref } from "vue"
import { client } from "./blade-client"   // 上一节里建好的 client（模块作用域）
import { useAgentSession } from "./composables/useAgentSession"

const { session, state, send, stop } = useAgentSession(client)
const draft = ref("")

// kind 非空的是内部消息（模式切换、上下文压缩记录等），不是聊天正文，要过滤掉
const visibleMessages = computed(() => state.value.messages.filter((m) => !m.kind))

function submit() {
  if (!session.value || !draft.value.trim()) return
  send(draft.value, { mode: "executing" })   // 要智能体动手干活就显式传
  draft.value = ""
}
</script>

<template>
  <div class="chat">
    <div v-for="(msg, index) in visibleMessages" :key="msg.entry_id ?? index" :class="msg.role">
      <strong>{{ msg.role }}</strong>

      <!--
        content 可能是字符串，也可能是内容块数组（用户发图片等多模态消息时）。
        用 getTextContent / getImageParts 取，别自己写 typeof 判断——
        否则图片消息会悄悄渲染成空白。智能体回复期间文字会逐步变长，直接渲染即可。
      -->
      <p>{{ getTextContent(msg.content) }}</p>
      <img
        v-for="part in getImageParts(msg.content)"
        :key="part.image_url.url"
        :src="part.image_url.url"
        alt=""
      />

      <!-- 工具调用 -->
      <details v-for="call in msg.tool_calls ?? []" :key="call.id">
        <summary>{{ call.display_name || call.name }}（{{ call.status }}）</summary>
        <pre>{{ call.arguments }}</pre>
        <pre v-if="call.result != null">{{ call.result }}</pre>
      </details>
    </div>

    <p v-if="state.errorMessage" class="error">{{ state.errorMessage }}</p>

    <input v-model="draft" :disabled="!session || state.isStreaming" @keydown.enter="submit" placeholder="输入消息..." />
    <button v-if="state.isStreaming" @click="stop">停止</button>
  </div>
</template>
```

状态快照的字段：

| 字段 | 说明 |
| --- | --- |
| `messages` | 渲染就绪的消息列表（角色、文本、工具调用、思考过程） |
| `isStreaming` | 智能体是否正在回复 |
| `status` | 会话状态：`created` / `running` / `completed` / `failed` / `interrupted` / `waiting_for_input`；尚未取得时为 `null` |
| `mode` | 当前工作模式：`planning`（只拆需求列计划）/ `executing`（调工具干活） |
| `connection` | 实时连接状态：`connected` / `connecting` / `reconnecting` / `disconnected` |
| `askAnswers` | 已提交的智能体提问作答 |
| `errorMessage` | 最近一次运行错误 |
| `turns` | 服务端下发的原始记录（一个 turn = 智能体的一轮动作）。日常渲染用 `messages` 就够，不用碰它 |

::: tip 断线了会怎样
实时连接断开时 SDK 会自动重连（期间 `connection` 是 `"reconnecting"`），重连后自动补齐断线期间漏掉的消息，**不需要你手动处理，也不会丢消息**。拿 `connection` 给用户显示个"连接中"提示即可。
:::

消息结构与工具调用渲染的细节见[聊天 UI 与自渲染](./chat-ui.md)。

## 消费工具调用等事件

需要在消息渲染之外响应事件（例如智能体写完订单后刷新业务列表）：

```ts
import { watch } from "vue"

const { session } = useAgentSession(client, sessionId)

watch(session, (chat, _previousChat, onCleanup) => {
  if (!chat) return
  const offs = [
    chat.on("toolCall", ({ toolCall }) => console.log("调用工具:", toolCall.name)),
    chat.on("toolResult", ({ toolCall }) => {
      if (toolCall.name.endsWith("WriteOrder")) refreshOrders()
    }),
    chat.on("chatEnd", ({ status }) => console.log("回复结束:", status)),
    chat.on("error", ({ message }) => console.error(message)),
  ]
  onCleanup(() => {
    for (const off of offs) off()
  })
})
```

`on()` 返回取消函数；事件处理函数抛异常只告警，不会中断会话。完整事件表见[聊天 UI 与自渲染](./chat-ui.md#事件表)。

## 发送选项

```ts
send("换个方案", { mode: "planning" })          // 指定工作模式
send("用另一个模型重新分析", { model: "gpt-4o" })
send([                                           // 多模态内容
  { type: "text", text: "看看这张图" },
  { type: "image_url", image_url: { url: "data:image/png;base64,..." } },
])
```

## 页面协作

让智能体驱动地图、表格等页面组件，用法与 React 完全相同：

```ts
session.value?.onCommand("map.highlight", (payload) => {
  // payload 类型是 unknown（内容由技能作者决定），用前自行断言或校验
  const { cityIds } = payload as { cityIds: string[] }
  map.highlight(cityIds)
})
```

详见[页面协作](./host-integration.md)。

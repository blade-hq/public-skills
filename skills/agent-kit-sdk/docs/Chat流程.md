# Chat 流程

## 整体架构

```
客户端                    服务端 (Server)                  引擎 (Engine)
  │                           │                              │
  │── chat:send ─────────────→│                              │
  │                           │── Engine.chat() ────────────→│
  │←── chat:start ───────────│                              │
  │                           │                              │
  │                           │        ┌── agent_loop() ──┐  │
  │←── turn:start ───────────│←───────│  LLM.complete()   │  │
  │←── turn:patch (text) ────│←───────│  (streaming)      │  │
  │←── turn:patch (tool) ────│←───────│  tool detected    │  │
  │←── turn:patch (result) ──│←───────│  tool executed    │  │
  │←── turn:end ─────────────│←───────│  turn complete    │  │
  │                           │        │                   │  │
  │←── turn:start ───────────│←───────│  next LLM call    │  │
  │←── turn:patch* ──────────│←───────│  ...              │  │
  │←── turn:end ─────────────│←───────│  done             │  │
  │                           │        └───────────────────┘  │
  │←── chat:end ─────────────│←──────────────────────────────│
```

---

## Agent Loop 核心算法

`agent_loop()` 是一个纯函数，循环直到结束：

```
1. 调用 LLM（带工具定义）
2. 解析响应：
   - 有 tool_use → 执行工具 → 结果加入 messages → 回到 1
   - 无 tool_use → 返回文本结果
   - 遇到终止工具（AskUserQuestion 等） → 暂停返回
   - 达到 max_turns → 停止
3. 返回 AgentLoopResult
```

---

## 工具调用流程

### 普通工具

```
assistant turn:
  ├─ [text] "我来执行这个命令..."
  ├─ [tool_use] Bash { command: "ls -la" }
  │   └─ [tool_result] "total 48\ndrwxr-xr-x..."  (status: done)
  └─ [text] "目录中有以下文件..."
```

对应事件：

```
turn:start  (role: assistant)
turn:patch  (add_content: text "我来执行这个命令...")
turn:patch  (add_tool_call: { id, tool_name: "Bash", arguments: '{"command":"ls -la"}', status: "pending" })
turn:patch  (tool_result: { tool_call_id, result: "total 48...", status: "done" })
turn:patch  (add_content: text "目录中有以下文件...")
turn:end    (status: completed)
```

### 工具提供者（Tool Providers）

| Provider | 说明 |
|----------|------|
| `bash` | Shell 命令执行 |
| `file_ops` | 文件/目录操作 |
| `skill` | 动态技能工具 |
| `builtin` | 内建工具（AskUserQuestion 等） |
| `fork` | 子智能体生成 |
| `search` | 网络搜索 |
| `webfetch` | HTTP 请求 |
| `langchain` | LangChain 工具集成 |
| `mcp` | Model Context Protocol 服务 |

---

## AskUserQuestion 交互

当智能体需要用户输入时：

### 1. 智能体发起提问

```
turn:patch (add_tool_call: {
  id: "tc_ask_001",
  tool_name: "AskUserQuestion",
  arguments: '{"questions": [{"question": "选择部署环境", "options": [{"label": "staging"}, {"label": "production"}]}]}',
  status: "awaiting_answer"
})
turn:end (status: paused)
chat:end (status: completed)
```

### 2. 用户回答

```typescript
socket.emit("chat:send", {
  session_id: sessionId,
  message: "",
  askuser_answer: {
    tool_call_id: "tc_ask_001",
    selections: { "0": [0] },   // 选择 staging
    custom: {}
  }
})
```

### 3. 智能体继续执行

收到回答后 agent_loop 恢复运行。

### AskUserQuestion 数据结构

```typescript
interface AskUserQuestionData {
  questions: {
    question: string
    header?: string
    options: {
      label: string
      description?: string
    }[]
    multiSelect?: boolean
  }[]
  source_loop?: {
    loop_name: string
    description: string
  } | null
}

interface AskUserAnswerData {
  selections: Record<number, number[]>   // 题号 → 选项索引数组
  custom: Record<number, string>         // 题号 → 自定义文本
}
```

---

## 子智能体（Fork）

智能体可以生成子智能体来处理子任务。

### 事件流

```
// 父智能体 Turn
turn:patch (add_tool_call: {
  id: "tc_fork_001",
  tool_name: "Agent",
  arguments: '{"description": "分析子任务"}',
  status: "pending"
})

// 子智能体 Turn（parent_fork_tool_call_id = "tc_fork_001"）
turn:start  { turn_id: "child_turn_1", parent_fork_tool_call_id: "tc_fork_001" }
turn:patch* (子智能体的文本和工具调用)
turn:end

// 父智能体工具结果
turn:patch (tool_result: { tool_call_id: "tc_fork_001", result: "子任务完成", status: "done" })
```

### 渲染子智能体

区分根 Turn 和子 Turn：

```typescript
// 根 Turn（无 parent）
const rootTurns = turns.filter(t => !t.parent_fork_tool_call_id)

// 某个 Fork 的子 Turn
const childTurns = turns.filter(t => t.parent_fork_tool_call_id === forkToolCallId)
```

子智能体也可以触发 AskUserQuestion，此时问题会冒泡到父级。

---

## Headless QA（一次性问答）

不需要流式交互的场景：

### TypeScript

```typescript
// 纯文本
const reply = await client.headless.run("法国的首都是什么？")
// reply = "巴黎"

// 结构化输出
const data = await client.headless.run("列出前3个最大的国家", {
  schema: {
    type: "object",
    properties: {
      countries: {
        type: "array",
        items: { type: "string" }
      }
    }
  }
})
// data = { countries: ["俄罗斯", "加拿大", "中国"] }
```

### Python

```python
reply = await client.headless.run("法国的首都是什么？")

data = await client.headless.run(
    "列出前3个最大的国家",
    schema={"type": "object", "properties": {"countries": {"type": "array", "items": {"type": "string"}}}}
)
```

---

## 流式渲染策略

### 方案 A：实时 Patch（推荐 React）

逐 patch 更新 UI，获得最佳流式体验：

```typescript
import { useChat } from "@blade-hq/agent-kit/react"

function Chat({ sessionId }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)
  // messages 自动随 patch 更新
}
```

### 方案 B：Turn 级更新（推荐 Vue / 自定义）

每次 `turn:start` / `turn:patch` 事件携带完整 Turn 快照，直接替换：

```typescript
socket.on("turn:start", (turn) => upsertTurn(turn))
socket.on("turn:patch", (patch) => upsertTurn(patch.data.turn))
socket.on("turn:end", (turn) => upsertTurn(turn))
```

### 方案 C：批量刷新（最简单）

等 `chat:end` 后一次性拉取：

```typescript
socket.on("chat:end", async () => {
  const turns = await client.sessions.getSessionTurns(sessionId)
  renderAll(turns)
})
```

---

## 提取文本内容

从 Turn 的 blocks 中提取纯文本：

```typescript
function extractText(blocks: ContentBlock[]): string {
  return blocks
    .filter(b => b.type === "text")
    .map(b => String(b.content ?? ""))
    .join("")
}
```

---

## React ChatView 快速集成

```tsx
import { ChatView } from "@blade-hq/agent-kit/chat"
import "@blade-hq/agent-kit/style.css"

function App() {
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <ChatView
        sessionId={sessionId}
        classNames={{
          root: "bg-white",
          messageListContent: "max-w-4xl",
        }}
        components={{
          EmptyState: () => <div>开始对话</div>,
        }}
        renderers={{
          tool: {
            Bash: ({ toolCall }) => <pre>{toolCall.arguments}</pre>,
          },
        }}
      />
    </div>
  )
}
```

> **布局要求**：父容器必须设置 `height`、`min-height: 0`、`display: flex`、`flex-direction: column`、`overflow: hidden`。

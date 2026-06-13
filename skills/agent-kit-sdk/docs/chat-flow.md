# Chat 流程

## 核心概念

一次 `chat:send` 会触发一个 **Agent Loop**（智能体循环）：

1. 将用户消息 + 历史上下文发送给 LLM
2. LLM 返回文本或工具调用
3. 如有工具调用 → 执行工具 → 结果加入上下文 → 回到 1
4. 如无工具调用 → 返回文本结果 → 结束
5. 如遇到 AskUserQuestion → 暂停，等待用户回答

一个 Loop 可能产生**多个 Turn**（每次 LLM 调用 = 一个 assistant turn）。

---

## 普通聊天

### 无工具调用

用户发消息，LLM 直接返回文本：

```
→ chat:send { message: "法国的首都是哪里？" }

← chat:start
← turn:start  (role: user)
← turn:end    (role: user)
← turn:start  (role: assistant, status: streaming)
← turn:patch  (add_content, text_delta: "法国")
← turn:patch  (add_content, text_delta: "的首都是")
← turn:patch  (add_content, text_delta: "巴黎。")
← turn:end    (role: assistant, status: completed)
← chat:end    (status: completed)
```

### 有工具调用

LLM 决定调用工具：

```
→ chat:send { message: "列出当前目录下的文件" }

← chat:start
← turn:start  (role: user)
← turn:end    (role: user)

← turn:start  (role: assistant, status: streaming)
← turn:patch  (add_content, text_delta: "我来帮你查看...")
← turn:patch  (add_tool_call: {
     id: "tc_001",
     tool_name: "Bash",
     display_name: "执行命令",
     arguments: "{\"command\": \"ls -la\"}",
     status: "pending"
   })
← turn:patch  (tool_result: {
     tool_call_id: "tc_001",
     result: "total 48\ndrwxr-xr-x ...",
     status: "done",
     duration_ms: 120
   })
← turn:patch  (add_content, text_delta: "当前目录有以下文件...")
← turn:end    (status: completed)
← chat:end    (status: completed)
```

### 多轮工具调用

智能体可能连续调用多个工具，每次 LLM 调用产生一个 Turn：

```
← turn:start  (assistant, turn 1: 调用工具 A)
← turn:patch  (add_tool_call → tool_result)
← turn:end

← turn:start  (assistant, turn 2: 根据工具 A 结果调用工具 B)
← turn:patch  (add_tool_call → tool_result)
← turn:end

← turn:start  (assistant, turn 3: 汇总结果)
← turn:patch  (add_content: 最终回复)
← turn:end

← chat:end
```

---

## AskUserQuestion（用户问答）

当智能体需要用户确认或选择时，会调用 `AskUserQuestion` 工具。

### 1. 智能体发起提问

```
← turn:patch  (add_tool_call: {
     id: "tc_ask_001",
     tool_name: "AskUserQuestion",
     arguments: "{...}",
     status: "awaiting_answer"
   })
← turn:end    (status: paused)
← chat:end    (status: completed)
```

`arguments` 解析后的结构：

```json
{
  "questions": [
    {
      "question": "选择部署环境",
      "header": "部署确认",
      "options": [
        { "label": "staging", "description": "测试环境" },
        { "label": "production", "description": "生产环境" }
      ],
      "multiSelect": false
    }
  ],
  "source_loop": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `questions` | array | 问题列表 |
| `questions[].question` | string | 问题文本 |
| `questions[].header` | string? | 问题标题 |
| `questions[].options` | array | 选项列表 |
| `questions[].options[].label` | string | 选项名称 |
| `questions[].options[].description` | string? | 选项描述 |
| `questions[].multiSelect` | bool? | 是否多选，默认单选 |
| `source_loop` | object? | 来源循环（子智能体场景） |

### 2. 用户回答

```
→ chat:send {
    "session_id": "sess_xxx",
    "message": "",
    "askuser_answer": {
      "tool_call_id": "tc_ask_001",
      "selections": { "0": [0] },
      "custom": {}
    }
  }
```

- `selections`：键为题号（从 "0" 开始），值为选中的选项索引数组
- `custom`：键为题号，值为自定义文本（当用户不选预设选项时）
- 每题必须提供 `selections` 或 `custom` 之一

### 3. 智能体继续

收到回答后，Agent Loop 恢复运行，后续事件流与普通聊天一致。

---

## 子智能体（Fork）

智能体可以生成子智能体来处理子任务。子智能体的 Turn 通过 `parent_fork_tool_call_id` 关联到父级工具调用。

### 事件流

```
← turn:start  (assistant, 父级)
← turn:patch  (add_tool_call: {
     id: "tc_fork_001",
     tool_name: "Agent",
     arguments: "{\"description\": \"数据清洗子任务\"}",
     status: "pending"
   })

  ← turn:start  { parent_fork_tool_call_id: "tc_fork_001", role: "assistant" }
  ← turn:patch  (子智能体的文本和工具调用...)
  ← turn:end

← turn:patch  (tool_result: {
     tool_call_id: "tc_fork_001",
     result: "子任务完成",
     status: "done"
   })
← turn:end
```

### 如何区分 Turn 层级

所有 Turn 都在同一个事件流中。通过 `parent_fork_tool_call_id` 区分：

| `parent_fork_tool_call_id` | 含义 |
|-----------------------------|------|
| `null` | 根级 Turn（主智能体） |
| `"tc_fork_001"` | 该 Turn 属于 `tc_fork_001` 这个 Fork 工具调用的子智能体 |

渲染时：
- 主聊天区只显示 `parent_fork_tool_call_id = null` 的 Turn
- 遇到 Fork 工具调用时，以折叠面板展示其子 Turn

子智能体也可以触发 AskUserQuestion，问题会正常冒泡到客户端。

---

## Headless 模式（一次性问答）

不需要流式交互、只需一次性拿到结果的场景，使用 Headless 模式：

```
→ chat:send {
    "session_id": "sess_xxx",
    "message": "法国的首都是什么？",
    "headless": true
  }
```

响应依然通过 WebSocket 事件流返回。`chat:end` 的 `result` 字段包含结果：

```json
{
  "session_id": "sess_xxx",
  "status": "completed",
  "result": { "output": "巴黎" },
  "finish_reason": "completed"
}
```

### 结构化输出

通过 `output_schema` 要求返回 JSON Schema 约束的结构：

```
→ chat:send {
    "session_id": "sess_xxx",
    "message": "列出前3个最大的国家",
    "headless": true,
    "output_schema": {
      "type": "object",
      "properties": {
        "countries": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
```

`chat:end` 的 `result`：

```json
{
  "output": { "countries": ["俄罗斯", "加拿大", "中国"] },
  "schema": { "..." }
}
```

也可以通过 REST 接口直接调用（无需 WebSocket），但需先创建会话。

---

## 流式渲染策略

根据你的场景选择合适的策略：

### 策略 A：逐字渲染（最佳体验）

监听每个 `turn:patch` 事件，拼接 `text_delta` 实现打字机效果。

**适用：** 需要实时流式展示的前端应用。

**关键逻辑：**
- 收到 `turn:start` → 创建新消息气泡
- 收到 `turn:patch (add_content, text_delta)` → 追加文本
- 收到 `turn:patch (add_tool_call)` → 显示"正在执行..."
- 收到 `turn:patch (tool_result)` → 显示工具结果
- 收到 `turn:end` → 标记消息完成

### 策略 B：Turn 级更新（平衡方案）

只在 `turn:end` 时刷新整个 Turn 的内容。

**适用：** 不需要逐字流式、但需要实时感知进度的场景。

**关键逻辑：**
- 收到 `turn:end` → 用完整的 TurnProjection 替换/追加到消息列表

### 策略 C：批量拉取（最简单）

忽略所有流式事件，仅在 `chat:end` 后一次性拉取：

```
GET /api/sessions/{session_id}/messages
```

**适用：** 后端服务对接、不需要流式展示的场景。

---

## 从 Turn 中提取纯文本

Turn 的内容存在 `blocks` 数组中，每个 block 有不同的 `type`。

提取文本的逻辑（伪代码）：

```
text = ""
for block in turn.blocks:
    if block.type == "text":
        text += block.content
return text
```

提取思考过程：

```
thinking = ""
for block in turn.blocks:
    if block.type == "thinking":
        thinking += block.content
return thinking
```

---

## 可用的工具类型

智能体可调用的工具按提供者分类：

| 工具提供者 | 说明 | 常见工具名示例 |
|-----------|------|---------------|
| bash | Shell 命令执行 | `Bash` |
| file_ops | 文件读写 | `Read`, `Write`, `Edit`, `Glob`, `Grep` |
| builtin | 内建交互 | `AskUserQuestion`, `TaskCreate` |
| fork | 子智能体 | `Agent` |
| search | 网络搜索 | `WebSearch` |
| webfetch | HTTP 请求 | `WebFetch` |
| skill | 动态技能 | 由技能动态注册 |
| mcp | MCP 协议工具 | 由 MCP 服务动态注册 |
| langchain | LangChain 集成 | 由配置动态注册 |

工具调用对调用方是透明的——你只需要处理 `add_tool_call` 和 `tool_result` 事件即可，无需关心工具的内部实现。

# WebSocket 接口

## 连接

使用 Socket.IO 协议连接，路径为 `/socket.io/`。

**连接地址：** `wss://blade.example.com/socket.io/`

**认证方式：** 握手时传递 `auth.token`：

```json
{
  "token": "sk-blade-v2-xxxxxxxxxx"
}
```

> Socket.IO 不是原生 WebSocket，需使用 Socket.IO 客户端库。各语言均有实现：
> - Go: `github.com/googollee/go-socket.io`
> - Java: `io.socket:socket.io-client:2.x`
> - Python: `python-socketio`
> - JavaScript: `socket.io-client`

---

## 客户端 → 服务端事件

### `session:subscribe`

订阅会话的实时更新。订阅后才能收到该会话的 `turn:*`、`chat:*` 事件。

```json
{ "session_id": "sess_xxx" }
```

### `session:unsubscribe`

取消订阅。

```json
{ "session_id": "sess_xxx" }
```

### `chat:send`

发送聊天消息，触发智能体响应。

```json
{
  "session_id": "sess_xxx",
  "message": "你好",
  "mode": "executing",
  "askuser_answer": null,
  "model": null,
  "headless": false,
  "output_schema": null,
  "whatif": null,
  "replay_decision": null,
  "runtime_env": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_id` | string | 是 | 会话 ID |
| `message` | string 或 array | 是 | 消息内容（见下方格式） |
| `mode` | string? | 否 | `"planning"` 或 `"executing"`，覆盖当前模式；业务任务、工具调用和文件处理推荐显式传 `"executing"` |
| `askuser_answer` | object? | 否 | 回答 AskUserQuestion（见 [Chat 流程](./chat-flow.md)） |
| `model` | string? | 否 | 覆盖模型 |
| `headless` | bool | 否 | 无头模式，默认 `false` |
| `output_schema` | object? | 否 | JSON Schema，要求结构化输出 |
| `whatif` | object? | 否 | What-If 重跑参数 |
| `replay_decision` | string? | 否 | `"keep_replay"` 或 `"continue_replay"` |
| `runtime_env` | object? | 否 | 运行时环境变量 `{"KEY": "VALUE"}` |

**message 格式：**

纯文本：

```json
"你好，请帮我分析数据"
```

多模态（文本 + 图片 + 文件）：

```json
[
  { "type": "text", "text": "分析这张图" },
  { "type": "image_url", "image_url": { "url": "data:image/png;base64,..." } },
  { "type": "file", "name": "data.csv", "data": "base64编码内容" }
]
```

**askuser_answer 格式：**

```json
{
  "tool_call_id": "tc_xxx",
  "selections": { "0": [1, 2] },
  "custom": { "0": "自定义文本" }
}
```

- `tool_call_id`：对应状态为 `awaiting_answer` 的工具调用 ID
- `selections`：题号 → 选项索引数组（从 0 开始）
- `custom`：题号 → 自定义文本

**whatif 格式：**

```json
{
  "from_step": 3,
  "quotes": [],
  "deprecate_entry_ids": ["entry_1", "entry_2"]
}
```

### `chat:stop`

停止当前生成。

```json
{ "session_id": "sess_xxx" }
```

### `chat:compact`

手动触发上下文压缩。支持 ack 回调。

```json
{ "session_id": "sess_xxx" }
```

**ack 回调返回：**

```json
{
  "status": "ok | error",
  "message": "string?",
  "code": "string?"
}
```

---

## 服务端 → 客户端事件

### `chat:start`

聊天开始。

```json
{ "session_id": "sess_xxx" }
```

### `turn:start`

新 Turn 开始。载荷为一个完整的 [TurnProjection](./types.md#turnprojection（turn-投影）)，附加 `session_id`。

```json
{
  "session_id": "sess_xxx",
  "id": "entry_xxx",
  "sequence": 0,
  "turn_id": "turn_xxx",
  "role": "assistant",
  "status": "streaming",
  "blocks": [],
  "tool_calls": [],
  "solution_id": null,
  "template_id": null,
  "..."
}
```

### `turn:patch`

流式增量更新。载荷为 [PatchEnvelope](./types.md#patchenvelope（增量更新信封）)。

```json
{
  "session_id": "sess_xxx",
  "sequence": 1,
  "turn_id": "turn_xxx",
  "loop_id": "root",
  "patch_type": "add_content",
  "data": {
    "type": "text",
    "text_delta": "你好"
  }
}
```

**patch_type 一览：**

| patch_type | 说明 | data 关键字段 |
|------------|------|---------------|
| `add_content` | 新增/追加内容块 | `type`, `content`, `text_delta` |
| `add_tool_call` | 新增工具调用 | `id`, `tool_name`, `display_name`, `arguments`, `status` |
| `tool_result` | 工具执行结果 | `tool_call_id`, `result`, `status`, `duration_ms` |
| `set_status` | Turn 状态变更 | `status` |
| `set_tool_status` | 工具状态变更 | `tool_call_id`, `status` |

### `turn:end`

Turn 结束。载荷为完整的 TurnProjection（含最终状态）。

```json
{
  "session_id": "sess_xxx",
  "turn_id": "turn_xxx",
  "status": "completed",
  "duration_ms": 3500,
  "usage": { "input_tokens": 500, "output_tokens": 200 },
  "..."
}
```

### `chat:end`

整轮聊天结束。

```json
{
  "session_id": "sess_xxx",
  "status": "completed | interrupted | failed",
  "result": null,
  "finish_reason": "completed | max_turns | tool_error"
}
```

| 字段 | 说明 |
|------|------|
| `status` | `completed`：正常完成；`interrupted`：被用户停止；`failed`：出错 |
| `result` | Headless 模式下返回结构化结果 `{output, schema}`，普通模式为 `null` |
| `finish_reason` | `completed`：正常；`max_turns`：达到最大轮次；`tool_error`：工具执行出错 |

### `session:updated`

会话元数据变更（标题、模型等）。

```json
{
  "session_id": "sess_xxx",
  "model": "string?",
  "intent": "AI 生成的标题",
  "replay_state": null
}
```

### `workspace:files_changed`

工作空间文件被工具修改。

```json
{
  "session_id": "sess_xxx",
  "file_path": "src/main.py"
}
```

### `system:error`

运行时错误。

```json
{
  "message": "错误描述",
  "session_id": "sess_xxx",
  "code": "string 或 int",
  "detail": null
}
```

### `system:notification`

系统通知。

```json
{
  "session_id": "sess_xxx",
  "notification_type": "scenario:init_script_failed",
  "title": "通知标题",
  "detail": "详细信息",
  "status": "error | warning | info"
}
```

### 其他事件

| 事件 | 说明 |
|------|------|
| `memory:inject:done` | 记忆注入完成 |
| `task:updated` | 任务状态更新 |
| `artifact:created` | 产物创建 |
| `bg:started` | 后台任务启动 |
| `skills:changed` | 技能列表变更 |
| `replay:input_mismatch` | 回放模式输入不匹配 |

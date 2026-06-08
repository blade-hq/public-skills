# WebSocket API (Socket.IO)

传输协议：Socket.IO（`/socket.io` 路径）

连接时通过 `auth` 传递 Bearer Token：

```typescript
const socket = client.socket()
socket.connect()
```

---

## Client → Server 事件

### `session:subscribe`

订阅会话的实时更新。

```json
{ "session_id": "string" }
```

### `session:unsubscribe`

取消订阅。

```json
{ "session_id": "string" }
```

### `chat:send`

发送聊天消息。

```json
{
  "session_id": "string",
  "message": "string | ContentPart[]",
  "mode": "planning | executing | null",
  "askuser_answer": null | {
    "tool_call_id": "string",
    "selections": { "0": [0, 1] },
    "custom": { "0": "自定义文本" }
  },
  "model": "string | null",
  "headless": false,
  "output_schema": null | { "type": "object", "..." },
  "whatif": {
    "from_step": 3,
    "quotes": [],
    "deprecate_entry_ids": []
  },
  "replay_decision": "keep_replay | continue_replay",
  "runtime_env": { "ENV_VAR": "value" }
}
```

**message 格式**：

- 纯文本：`"你好"`
- 多模态：
  ```json
  [
    { "type": "text", "text": "分析这张图" },
    { "type": "image_url", "image_url": { "url": "data:image/png;base64,..." } },
    { "type": "file", "name": "data.csv", "data": "base64..." }
  ]
  ```

### `chat:stop`

停止当前生成。

```json
{ "session_id": "string" }
```

### `chat:compact`

手动触发上下文压缩（带 ack 回调）。

```json
{ "session_id": "string" }
```

### `asr:start` / `asr:audio` / `asr:stop`

语音识别控制。

```json
// asr:start
{ "request_id": "string | optional" }

// asr:audio
{ "pcm": "<bytes>", "request_id": "string | optional" }

// asr:stop
{ "request_id": "string | optional" }
```

### `vibe:logs:start` / `vibe:logs:stop`

Docker 日志流控制。

```json
{ "session_id": "string", "kind": "default | deploy", "version": "string | optional" }
```

### `gis.event.analysis.request`

GIS 态势分析请求。

```json
{
  "event_type": "analysis_request",
  "message_id": "string",
  "session_id": "string",
  "workspace_id": "string",
  "trigger_mode": "selection_plus_text | selection_only | text_only",
  "user_prompt": "string",
  "scope": {}
}
```

---

## Server → Client 事件

### `chat:start`

聊天开始。

```json
{ "session_id": "string" }
```

### `turn:start`

Turn 开始（包含初始投影）。

```json
{
  "session_id": "string",
  "id": "string",
  "sequence": 0,
  "turn_id": "string",
  "role": "user | assistant | system",
  "status": "streaming",
  "blocks": [],
  "tool_calls": [],
  "solution_id": "string | null",
  "template_id": "string | null"
}
```

### `turn:patch`

流式增量更新。

```json
{
  "session_id": "string",
  "sequence": 1,
  "turn_id": "string",
  "loop_id": "string",
  "patch_type": "add_content | add_tool_call | set_status | tool_result | ...",
  "data": { "..." }
}
```

**patch_type 类型**：

| patch_type | data 内容 | 说明 |
|------------|-----------|------|
| `add_content` | `{ type, content, text_delta?, ... }` | 新增内容块（文本增量/思考/模式切换） |
| `add_tool_call` | `{ id, tool_name, display_name, arguments, status }` | 新增工具调用 |
| `set_status` | `{ status }` | 更新 Turn 状态 |
| `tool_result` | `{ tool_call_id, result, status, duration_ms }` | 工具执行结果 |
| `set_tool_status` | `{ tool_call_id, status }` | 更新工具调用状态 |

### `turn:end`

Turn 结束。

```json
{
  "session_id": "string",
  "turn_id": "string",
  "status": "completed | paused | failed",
  "duration_ms": 1234,
  "usage": { "input_tokens": 500, "output_tokens": 200 }
}
```

### `chat:end`

整轮聊天结束。

```json
{
  "session_id": "string",
  "status": "completed | interrupted | failed",
  "result": null | { "output": "string", "schema": "..." },
  "finish_reason": "completed | max_turns | tool_error"
}
```

### `session:updated`

会话元数据变更（标题、模型等）。

```json
{
  "session_id": "string",
  "model": "string | null",
  "intent": "string | null",
  "replay_state": {}
}
```

### `workspace:files_changed`

工作空间文件被工具修改。

```json
{
  "session_id": "string",
  "file_path": "string | null"
}
```

### `system:error`

运行时错误。

```json
{
  "message": "string",
  "session_id": "string | null",
  "code": "string | int",
  "detail": null | "string | object"
}
```

### `system:notification`

系统通知。

```json
{
  "session_id": "string | null",
  "notification_type": "scenario:init_script_failed | ...",
  "title": "string",
  "detail": "string | null",
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
| `asr:ready` / `asr:partial` / `asr:final` / `asr:closed` / `asr:error` | 语音识别事件 |
| `vibe:logs:line` / `vibe:logs:end` | 日志流事件 |

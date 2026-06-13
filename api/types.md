# 核心类型

本文档定义所有 JSON 对象的结构。字段标注 `?` 表示可选（可能为 `null` 或不出现）。

---

## Session（会话）

```json
{
  "id": "sess_xxx",
  "intent": "用户任务描述",
  "status": "created | running | completed | failed | interrupted | waiting_for_input",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "user_id": "user_xxx",
  "solution_id": "string?",
  "biz_role_id": "string?",
  "model": "string?",
  "shared": false,
  "is_pinned": false,
  "memory_enabled": true,
  "is_persistent": false,
  "replay_state": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 会话唯一 ID |
| `intent` | string | 会话意图/标题 |
| `status` | string | 状态枚举，见下方 |
| `solution_id` | string? | 关联的 Solution |
| `biz_role_id` | string? | 业务角色 |
| `model` | string? | 使用的 LLM 模型 |
| `shared` | bool | 是否已分享 |
| `is_pinned` | bool | 是否置顶 |
| `memory_enabled` | bool | 是否启用记忆 |
| `is_persistent` | bool | 是否持久会话 |
| `replay_state` | object? | 回放状态 |

**Session Status 枚举：**

| 值 | 说明 |
|----|------|
| `created` | 已创建，未开始 |
| `running` | 运行中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `interrupted` | 被中断 |
| `waiting_for_input` | 等待用户输入（AskUserQuestion） |

---

## TurnProjection（Turn 投影）

一轮对话的完整快照，是聊天历史的基本单位。

```json
{
  "id": "entry_xxx",
  "sequence": 0,
  "turn_id": "turn_xxx",
  "loop_id": "root",
  "kind": "message",
  "role": "assistant",
  "status": "completed",
  "blocks": [],
  "tool_calls": [],
  "model": "claude-sonnet-4-20250514",
  "usage": { "input_tokens": 500, "output_tokens": 200 },
  "duration_ms": 3500,
  "started_at": "2026-01-01T00:00:00Z",
  "context_window": 200000,
  "memory_refs": null,
  "parent_fork_tool_call_id": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 条目 ID |
| `sequence` | int | 序号（从 0 递增） |
| `turn_id` | string | Turn 唯一 ID |
| `loop_id` | string | 循环 ID（根循环为 `"root"`） |
| `kind` | string | `"message"` 或 `"compaction"`（压缩摘要） |
| `role` | string | `"user"` / `"assistant"` / `"system"` |
| `status` | string | `"streaming"` / `"completed"` / `"paused"` / `"failed"` / `"interrupted"` |
| `blocks` | ContentBlock[] | 内容块列表 |
| `tool_calls` | ToolCallProjection[] | 工具调用列表 |
| `model` | string? | 使用的模型 |
| `usage` | object? | Token 用量 `{input_tokens, output_tokens}` |
| `duration_ms` | int | 耗时（毫秒） |
| `started_at` | string? | 开始时间 |
| `context_window` | int | 上下文窗口大小 |
| `memory_refs` | MemoryRef[]? | 命中的记忆引用 |
| `parent_fork_tool_call_id` | string? | 父级 Fork 工具调用 ID（子智能体场景） |

**Compaction 相关字段**（`kind = "compaction"` 时出现）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `compaction_id` | string? | 压缩 ID |
| `summary_preview` | string? | 摘要预览 |
| `summary_full` | string? | 完整摘要 |
| `archived_count` | int? | 被归档的 Turn 数 |
| `tokens_before` | int? | 压缩前 token 数 |
| `tokens_after` | int? | 压缩后 token 数 |
| `saved_ratio` | float? | 节省比例 0~1 |
| `trigger` | string? | 触发方式：`"auto"` / `"manual"` / `"forced_retry"` |

---

## ContentBlock（内容块）

Turn 内的一个内容元素。

```json
{
  "type": "text",
  "content": "这是回复文本",
  "tool_call_id": null,
  "tool_name": null,
  "display_name": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 内容类型（见枚举） |
| `content` | any | 内容值，类型随 `type` 变化 |
| `tool_call_id` | string? | 关联的工具调用 ID |
| `tool_name` | string? | 工具名称 |
| `display_name` | string? | 工具的友好显示名 |

**type 枚举：**

| 值 | content 类型 | 说明 |
|----|-------------|------|
| `text` | string | 文本内容 |
| `thinking` | string | AI 思考过程 |
| `tool_use` | object | 工具调用声明 |
| `tool_result` | any | 工具执行结果 |
| `tool_ui` | object | 工具返回的 UI 卡片 |
| `tool_bridge` | object | 工具桥接动作（传递给宿主页面） |
| `system_notification` | string | 系统通知 |
| `mode_change` | object | 模式切换 |
| `planning_enter` | - | 进入规划模式 |
| `planning_exit` | - | 退出规划模式 |
| `plan_status` | object | 计划状态更新 |
| `ask_user_answer` | object | 用户回答 |

---

## ToolCallProjection（工具调用）

```json
{
  "id": "tc_xxx",
  "tool_name": "Bash",
  "display_name": "执行命令",
  "arguments": "{\"command\": \"ls -la\"}",
  "status": "done",
  "result": "total 48\ndrwxr-xr-x ...",
  "duration_ms": 150,
  "pending_question_ref": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 工具调用唯一 ID |
| `tool_name` | string | 工具名称 |
| `display_name` | string | 显示名称（优先展示） |
| `arguments` | string | **JSON 字符串**，需自行解析 |
| `status` | string | 状态枚举 |
| `result` | any? | 执行结果 |
| `duration_ms` | int? | 耗时（毫秒） |
| `pending_question_ref` | object? | 等待用户回答的引用信息 |

**status 枚举：**

| 值 | 说明 |
|----|------|
| `pending` | 执行中 |
| `done` | 已完成 |
| `error` | 出错 |
| `cancelled` | 已取消 |
| `awaiting_answer` | 等待用户回答 |

**pending_question_ref 结构：**

```json
{
  "child_loop_name": "string",
  "child_tool_call_id": "string",
  "description": "string?"
}
```

---

## MemoryRef（记忆引用）

```json
{
  "id": 1,
  "content_preview": "记忆内容预览...",
  "skill_name": "string?"
}
```

---

## PatchEnvelope（增量更新信封）

WebSocket `turn:patch` 事件的载荷格式。

```json
{
  "session_id": "sess_xxx",
  "sequence": 1,
  "turn_id": "turn_xxx",
  "loop_id": "root",
  "patch_type": "add_content",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | string | 会话 ID |
| `sequence` | int | 序号 |
| `turn_id` | string | Turn ID |
| `loop_id` | string | 循环 ID |
| `patch_type` | string | 补丁类型（见下表） |
| `data` | object | 补丁数据，结构随 `patch_type` 变化 |

**patch_type 枚举与 data 结构：**

### `add_content`

新增内容块。

```json
{
  "type": "text",
  "content": "新文本",
  "text_delta": "增量文本"
}
```

> 流式文本场景下 `text_delta` 为增量字符串，可拼接。`content` 为该块的当前完整内容。

### `add_tool_call`

新增工具调用。

```json
{
  "id": "tc_xxx",
  "tool_name": "Bash",
  "display_name": "执行命令",
  "arguments": "{\"command\": \"ls\"}",
  "status": "pending"
}
```

### `tool_result`

工具执行完毕。

```json
{
  "tool_call_id": "tc_xxx",
  "result": "执行结果...",
  "status": "done",
  "duration_ms": 150
}
```

### `set_status`

Turn 状态变更。

```json
{
  "status": "completed"
}
```

### `set_tool_status`

工具调用状态变更。

```json
{
  "tool_call_id": "tc_xxx",
  "status": "done"
}
```

---

## Memory（记忆）

```json
{
  "id": 1,
  "type": "feedback",
  "content": "记忆内容",
  "skill_name": null,
  "record_type": null,
  "scope": null,
  "owner": null,
  "topic": null,
  "mem0_id": null,
  "superseded_by": null,
  "write_reason": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": null,
  "hit_count": 0,
  "last_hit_at": null,
  "disabled": false,
  "source_session": "sess_xxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 记忆 ID |
| `type` | string | `"feedback"` 或 `"experience"` |
| `content` | string | 记忆内容（1-500 字符） |
| `skill_name` | string? | 关联技能 |
| `record_type` | string? | `"memory"` 或 `"skill_comment"` |
| `scope` | string? | 范围 |
| `owner` | string? | 所有者 |
| `topic` | string? | 主题 |
| `mem0_id` | string? | 外部 ID |
| `superseded_by` | int? | 被哪条记忆替代 |
| `write_reason` | string? | 写入原因 |
| `hit_count` | int | 命中次数 |
| `last_hit_at` | string? | 最后命中时间 |
| `disabled` | bool | 是否禁用 |
| `source_session` | string | 来源会话 ID |

---

## ApiKey

```json
{
  "id": "key_xxx",
  "name": "My Key",
  "masked": "sk-blade-v2-...xxxx",
  "plaintext": null,
  "created_at": "2026-01-01T00:00:00Z",
  "last_used_at": "2026-01-02T00:00:00Z"
}
```

> `plaintext` 仅在创建时返回一次，之后始终为 `null`。

---

## ScheduledTask（定时任务）

```json
{
  "id": "task_xxx",
  "title": "每日报告",
  "prompt": "生成今日数据摘要",
  "cron": "0 9 * * *",
  "timezone": "Asia/Shanghai",
  "enabled": true,
  "expires_at": null,
  "skip_confirmations": false,
  "model": null
}
```

## ScheduledTaskRun（运行记录）

```json
{
  "id": "run_xxx",
  "task_id": "task_xxx",
  "session_id": "sess_xxx",
  "status": "completed | failed | running",
  "error": null,
  "triggered_at": "2026-01-01T09:00:00Z",
  "finished_at": "2026-01-01T09:05:00Z"
}
```

---

## Tool _meta 扩展

工具执行结果中可携带 `_meta` 字段，用于向宿主页面传递动作或 UI 卡片。

### Bridge（页面动作）

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

宿主页面监听 bridge 事件后执行相应动作（如地图高亮）。

### UI Card（内联/预览卡片）

```json
{
  "_meta": {
    "ui": {
      "resourceHTML": "<!doctype html>...",
      "resourceUri": "https://...",
      "target": "inline | preview",
      "height": 320,
      "title": "卡片标题"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `resourceHTML` | string? | 完整 HTML，通过 iframe srcdoc 渲染 |
| `resourceUri` | string? | 外部 URL，通过 iframe src 渲染 |
| `target` | string | `"inline"`（聊天区内联）或 `"preview"`（侧边预览） |
| `height` | int? | iframe 高度（像素） |
| `title` | string? | 卡片标题 |

> `resourceHTML` 和 `resourceUri` 二选一。

# REST API 接口

基础路径：`/api`
认证：`Authorization: Bearer sk-blade-v2-...`

## 接口总览

> 重要程度：🔴 核心（必须对接） · 🟡 常用 · ⚪ 可选

### 会话（Sessions） — 最核心的资源

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/sessions`](#post-apisessions) | 创建会话 | 🔴 核心 |
| [GET `/api/sessions`](#get-apisessions) | 列出会话 | 🔴 核心 |
| [GET `/api/sessions/{id}`](#get-apisessionssession_id) | 获取会话详情 | 🔴 核心 |
| [DELETE `/api/sessions/{id}`](#delete-apisessionssession_id) | 删除会话 | 🟡 常用 |
| [PATCH `/api/sessions/{id}`](#patch-apisessionssession_id) | 更新会话（标题等） | 🟡 常用 |
| [PUT `/api/sessions/{id}/env`](#put-apisessionssession_idenv) | 更新会话环境变量 | ⚪ 可选 |
| [PATCH `/api/sessions/{id}/pin`](#patch-apisessionssession_idpin) | 固定/取消固定会话 | ⚪ 可选 |

### 聊天历史

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/messages`](#get-apisessionssession_idmessages) | 获取 Turn 列表（聊天记录） | 🔴 核心 |
| [GET `/api/sessions/{id}/history`](#get-apisessionssession_idhistory) | 获取原始历史树 | ⚪ 可选 |

### 检查点 & 回退

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/checkpoints`](#get-apisessionssession_idcheckpoints) | 列出检查点 | 🟡 常用 |
| [POST `/api/sessions/{id}/rewind`](#post-apisessionssession_idrewind) | 回退到检查点 | 🟡 常用 |
| [POST `/api/sessions/{id}/checkout`](#post-apisessionssession_idcheckout) | 查看检查点状态（不修改） | ⚪ 可选 |
| [POST `/api/sessions/{id}/switch-branch`](#post-apisessionssession_idswitch-branch) | 切换分支 | ⚪ 可选 |
| [POST `/api/sessions/{id}/compact`](#post-apisessionssession_idcompact) | 手动上下文压缩 | ⚪ 可选 |

### 模式 & 配置

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [PATCH `/api/sessions/{id}/sharing`](#patch-apisessionssession_idsharing) | 开启/关闭分享 | 🟡 常用 |
| [PATCH `/api/sessions/{id}/memory`](#patch-apisessionssession_idmemory) | 开启/关闭记忆 | ⚪ 可选 |

### 回放

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/sessions/{id}/replay`](#post-apisessionssession_idreplay) | 创建回放会话 | ⚪ 可选 |
| [GET `/api/sessions/{id}/replay/preview`](#get-apisessionssession_idreplaypreview) | 预览回放 | ⚪ 可选 |
| [PATCH `/api/sessions/{id}/replay`](#patch-apisessionssession_idreplay) | 更新回放配置 | ⚪ 可选 |

### 工作空间文件

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/ls/{path}`](#get-apisessionssession_idlsdir_path) | 列出目录 | 🟡 常用 |
| [GET `/api/sessions/{id}/files/{path}`](#get-apisessionssession_idfilesfile_path) | 读取文件 | 🟡 常用 |
| [PUT `/api/sessions/{id}/files/{path}`](#put-apisessionssession_idfilesfile_path) | 写入文件 | 🟡 常用 |
| [POST `/api/sessions/{id}/upload/{path}`](#post-apisessionssession_iduploaddir_path) | 上传文件 | 🟡 常用 |
| [DELETE `/api/sessions/{id}/files/{path}`](#delete-apisessionssession_idfilesfile_path) | 删除文件 | ⚪ 可选 |
| [POST `.../files/{path}/rename`](#post-apisessionssession_idfilesfile_pathrename) | 重命名文件 | ⚪ 可选 |
| [POST `.../files/{path}/copy`](#post-apisessionssession_idfilesfile_pathcopy) | 复制文件 | ⚪ 可选 |
| [GET `.../download-dir/{path}`](#get-apisessionssession_iddownload-dirdir_path) | 下载目录 ZIP | ⚪ 可选 |

### 分享

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/sessions/{id}/share`](#post-apisessionssession_idshare) | 创建分享链接 | 🟡 常用 |
| [DELETE `/api/sessions/{id}/share/{token}`](#delete-apisessionssession_idsharetoken) | 撤销分享 | ⚪ 可选 |
| [GET `/api/share/{token}`](#get-apisharetoken) | 获取已分享会话（公开） | 🟡 常用 |

### 导入 & 导出

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/export`](#get-apisessionssession_idexport) | 导出会话 ZIP | ⚪ 可选 |
| [POST `/api/sessions/preview-import`](#post-apisessionspreview-import) | 预览导入 | ⚪ 可选 |
| [POST `/api/sessions/import`](#post-apisessionsimport) | 导入会话 | ⚪ 可选 |

### Tokenize

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/sessions/tokenize/prompt`](#post-apisessionstokenizeprompt) | 计算 prompt token 数 | ⚪ 可选 |
| [POST `/api/sessions/tokenize/messages`](#post-apisessionstokenizemessages) | 计算消息 token 数 | ⚪ 可选 |

### 后台任务

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/background-tasks`](#get-apisessionssession_idbackground-tasks) | 列出后台任务 | ⚪ 可选 |
| [GET `.../background-tasks/{task_id}`](#get-apisessionssession_idbackground-taskstask_id) | 获取任务输出 | ⚪ 可选 |
| [POST `.../background-tasks/{task_id}/stop`](#post-apisessionssession_idbackground-taskstask_idstop) | 停止任务 | ⚪ 可选 |

### 会话技能

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/sessions/{id}/skills`](#get-apisessionssession_idskills) | 列出会话技能 | ⚪ 可选 |
| [POST `.../skills:upload`](#post-apisessionssession_idskillsupload) | 上传会话级技能 | 🟡 常用 |
| [POST `.../skills/install`](#post-apisessionssession_idskillsinstall) | 安装合作伙伴技能 | ⚪ 可选 |
| [POST `.../skills:resync`](#post-apisessionssession_idskillsresync) | 重新同步技能 | ⚪ 可选 |

### Skills（全局技能）

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/skills`](#get-apiskills) | 列出所有技能 | 🟡 常用 |
| [GET `/api/skills/{skill_id}`](#get-apiskillsskill_id) | 获取技能详情 | ⚪ 可选 |
| [GET `/api/skills/search`](#get-apiskillssearch) | 语义搜索技能 | ⚪ 可选 |
| [GET `/api/skills/installed`](#get-apiskillsinstalled) | 已安装技能列表 | ⚪ 可选 |

### Memories（记忆）

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/memories`](#post-apimemories) | 创建记忆 | 🟡 常用 |
| [GET `/api/memories`](#get-apimemories) | 列出记忆 | 🟡 常用 |
| [GET `/api/memories/{id}`](#get-apimemoriesmemory_id) | 获取记忆 | ⚪ 可选 |
| [PUT `/api/memories/{id}`](#put-apimemoriesmemory_id) | 更新记忆 | ⚪ 可选 |
| [PATCH `/api/memories/{id}`](#patch-apimemoriesmemory_id) | 启用/禁用记忆 | ⚪ 可选 |
| [DELETE `/api/memories/{id}`](#delete-apimemoriesmemory_id) | 删除记忆 | ⚪ 可选 |
| [POST `/api/memories/batch`](#post-apimemoriesbatch) | 批量操作 | ⚪ 可选 |

### Solutions（工作流模板）

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/solutions`](#get-apisolutions) | 列出 Solution | 🟡 常用 |
| [GET `.../biz-roles`](#get-apisolutionssolution_idbiz-roles) | 列出业务角色 | ⚪ 可选 |
| [GET `.../files/{path}`](#get-apisolutionssolution_idfilesfile_path) | 获取 Solution 文件 | ⚪ 可选 |

### Production Solutions（多智能体 DAG）

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/prod_solution`](#post-apiprod_solution) | 创建 Prod Solution | 🟡 常用 |
| [GET `/api/prod_solution`](#get-apiprod_solution) | 列出 | ⚪ 可选 |
| [GET/PATCH/DELETE `.../prod_solution/{id}`](#get-apiprod_solutionprod_solution_id) | 获取/更新/删除 | ⚪ 可选 |
| [DAG 管理接口（7 个）](#dag-管理) | DAG 的增删改查、验证、发布、回滚 | 🟡 常用 |
| [Architecture 管理接口](#architecture-管理) | 架构管理（同 DAG 结构） | ⚪ 可选 |

### Production Agents（生产智能体）

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/prod_agents`](#post-apiprod_agents) | 创建生产智能体 | 🟡 常用 |
| [POST `.../start-session`](#post-apiprod_agentsrecord_idstart-session) | 从智能体启动会话 | 🔴 核心 |
| [GET `/api/prod_agents`](#get-apiprod_agents) | 列出 | 🟡 常用 |
| [其他 CRUD](#get-apiprod_agentsprovider_key) | 获取/更新/删除/实例化 | ⚪ 可选 |

### API Keys

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [POST `/api/user/api-keys/`](#post-apiuserapi-keys) | 创建 API Key | 🔴 核心 |
| [GET `/api/user/api-keys/`](#get-apiuserapi-keys) | 列出 Key | 🟡 常用 |
| [DELETE `/api/user/api-keys/{id}`](#delete-apiuserapi-keyskey_id) | 删除 Key | 🟡 常用 |

### Health & Config

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [GET `/api/health`](#get-apihealth) | 健康检查 | 🔴 核心 |
| [GET `/api/config`](#get-apiconfig) | 运行时配置 | ⚪ 可选 |
| [GET `/api/config/models`](#get-apiconfigmodels) | 可用模型列表 | 🟡 常用 |
| [GET `/api/auth/me`](#get-apiauthme) | 当前用户信息 | 🟡 常用 |

### 其他

| 接口 | 说明 | 重要程度 |
|------|------|----------|
| [Scheduled Tasks（6 个）](#scheduled-tasks) | 定时任务管理 | ⚪ 可选 |
| [Environment](#environment) | 环境配置 | ⚪ 可选 |
| [User Preferences](#user-preferences) | 用户偏好 | ⚪ 可选 |
| [Admin](#admin) | 管理员操作 | ⚪ 可选 |
| [Prod Workspaces](#prod-workspaces) | 工作空间管理 | ⚪ 可选 |
| [Published Apps](#published-apps) | 应用发布 | ⚪ 可选 |
| [Registry](#registry) | 注册资源 | ⚪ 可选 |

---

## Health & Configuration

### GET `/api/health`

健康检查。

**Response:**
```json
{ "status": "ok" }
```

### GET `/healthz`

备用健康检查（同上）。

### GET `/api/config`

运行时配置。

**Response:**
```json
{
  "sentryDsn": "string",
  "posthogKey": "string",
  "posthogHost": "string",
  "asrEnabled": true,
  "asrProvider": "volcengine",
  "gisMapUrl": "string",
  "bladeOsPath": "string",
  "publicSharingEnabled": true,
  "memoryEnabled": true
}
```

### GET `/api/config/models`

可用 LLM 模型列表。

**Response:**
```json
{
  "default": "model-id",
  "models": [
    { "id": "model-id", "name": "Model Name", "..." }
  ]
}
```

---

## Authentication

### GET `/api/auth/me`

获取当前用户信息（JWT/cookie 或 API Key 认证）。

**Response:**
```json
{
  "id": "user-id",
  "username": "string",
  "avatar_url": "string | null",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## Sessions

### POST `/api/sessions`

创建会话。

**Request:**
```json
{
  "intent": "",                          // string, 会话意图
  "solution_id": null,                   // string?, Solution ID
  "biz_role_id": null,                   // string?, 业务角色 ID
  "template_id": null,                   // string?, 模板 ID（旧版）
  "primary_skill_id": null,              // string?, 主技能 ID
  "model": null,                         // string?, LLM 模型
  "software_factory_id": null,           // int?, 软件工厂 ID
  "memory_enabled": null,               // bool?, 启用记忆
  "is_persistent": false,                // bool, 持久会话
  "env": null,                           // dict?, 环境变量 {"KEY": "VALUE"}
  "workspace_id": null,                  // string?, 工作空间 ID
  "disable_tools": null                  // string[]?, 禁用的工具列表
}
```

**Response:**
```json
{ "session_id": "sess_xxx" }
```

### GET `/api/sessions`

列出会话。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template_id_prefix` | string? | - | 按模板 ID 前缀过滤 |
| `q` | string? | - | 搜索关键词 |
| `limit` | int | 20 | 每页数量（≥1） |
| `offset` | int | 0 | 偏移量（≥0） |

**Response:**
```json
{
  "items": [
    {
      "id": "sess_xxx",
      "intent": "string",
      "status": "created | running | completed | failed | interrupted | waiting_for_input",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z",
      "user_id": "string",
      "solution_id": "string | null",
      "biz_role_id": "string | null",
      "model": "string | null",
      "shared": false,
      "is_pinned": false,
      "memory_enabled": true,
      "is_persistent": false,
      "replay_state": null
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "content_match_truncated": false
}
```

### GET `/api/sessions/{session_id}`

获取会话详情。

**Response:**
```json
{
  "id": "sess_xxx",
  "intent": "string",
  "status": "running",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "user_id": "string",
  "solution_id": "string | null",
  "biz_role_id": "string | null",
  "model": "string",
  "shared": false,
  "is_pinned": false,
  "memory_enabled": true,
  "is_persistent": false,
  "replay_state": null,
  "solution": { "...": "Solution 详情" },
  "primary_skill_snapshot": null,
  "session_setup": { "...": "会话配置" },
  "viewer_role": "owner"
}
```

### PATCH `/api/sessions/{session_id}`

更新会话。

**Request:**
```json
{
  "intent": "新标题"       // string?, 新的意图
}
```

**Response:** 同 GET `/api/sessions/{session_id}`

### DELETE `/api/sessions/{session_id}`

删除会话。

**Response:**
```json
{ "deleted": true }
```

### PUT `/api/sessions/{session_id}/env`

更新会话环境变量。

**Request:**
```json
{
  "env": { "API_KEY": "xxx", "DEBUG": "true" }
}
```

**Response:** 同 GET `/api/sessions/{session_id}`（含 env 字段）

### PATCH `/api/sessions/{session_id}/pin`

固定/取消固定会话。

**Request:**
```json
{ "pinned": true }
```

**Response:** 同 GET `/api/sessions/{session_id}`

---

### 聊天历史（Turns）

### GET `/api/sessions/{session_id}/messages`

获取 Turn 列表（渲染后的投影）。

**Response:**
```json
[
  {
    "id": "entry_xxx",
    "sequence": 0,
    "turn_id": "turn_xxx",
    "loop_id": "root",
    "kind": "message",
    "role": "user | assistant | system",
    "status": "completed | streaming | paused | failed | interrupted",
    "blocks": [
      {
        "type": "text | thinking | tool_use | tool_result | ...",
        "content": "文本内容",
        "tool_call_id": null,
        "tool_name": null,
        "display_name": null
      }
    ],
    "tool_calls": [
      {
        "id": "tc_xxx",
        "tool_name": "Bash",
        "display_name": "执行命令",
        "arguments": "{\"command\": \"ls\"}",
        "status": "done | pending | error | cancelled | awaiting_answer",
        "result": "...",
        "duration_ms": 150,
        "pending_question_ref": null
      }
    ],
    "model": "claude-sonnet-4-20250514",
    "usage": { "input_tokens": 500, "output_tokens": 200 },
    "duration_ms": 3500,
    "started_at": "2026-01-01T00:00:00Z",
    "context_window": 200000,
    "memory_refs": null,
    "parent_fork_tool_call_id": null,
    "compaction_id": null,
    "summary_preview": null,
    "summary_full": null,
    "archived_count": null,
    "tokens_before": null,
    "tokens_after": null,
    "saved_ratio": null,
    "trigger": null,
    "failure_reason": null
  }
]
```

### GET `/api/sessions/{session_id}/history`

获取原始历史树。

**Response:**
```json
{
  "nodes": [ "..." ],
  "system_prompt_tokens": 1200,
  "tools_tokens": 800,
  "tokenizer_model": "string"
}
```

---

### 检查点 & 回退

### GET `/api/sessions/{session_id}/checkpoints`

列出检查点。

**Response:**
```json
[ { "checkpoint_id": "cp_xxx", "turn_id": "turn_xxx", "..." } ]
```

### POST `/api/sessions/{session_id}/rewind`

回退到检查点。

**Request:**
```json
{ "checkpoint_id": "cp_xxx" }
```

**Response:** 回退结果 dict

### POST `/api/sessions/{session_id}/checkout`

查看某个检查点状态（不修改会话）。

**Request:**
```json
{
  "checkpoint_id": "cp_xxx",
  "position": "before"          // "before" | "turn_end"，默认 "before"
}
```

**Response:** Checkout 结果 dict

### POST `/api/sessions/{session_id}/switch-branch`

切换分支。

**Request:**
```json
{ "checkpoint_id": "cp_xxx" }
```

**Response:** 分支切换结果 dict

### POST `/api/sessions/{session_id}/compact`

手动触发上下文压缩。

**Response:** Compaction 结果 dict

---

### 模式 & 配置

### PATCH `/api/sessions/{session_id}/sharing`

开启/关闭分享。

**Request:**
```json
{ "shared": true }
```

**Response:**
```json
{ "shared": true }
```

### PATCH `/api/sessions/{session_id}/memory`

开启/关闭记忆。

**Request:**
```json
{ "memory_enabled": true }
```

**Response:**
```json
{ "memory_enabled": true }
```

---

### 回放

### POST `/api/sessions/{session_id}/replay`

创建回放会话。

**Request:**
```json
{
  "speed": 5              // 1 | 2 | 5，回放速度
}
```

**Response:**
```json
{ "session_id": "sess_replay_xxx" }
```

### GET `/api/sessions/{session_id}/replay/preview`

预览回放。

**Response:**
```json
{
  "session_id": "sess_xxx",
  "intent": "string",
  "supported": true,
  "reason": null
}
```

### PATCH `/api/sessions/{session_id}/replay`

更新回放配置。

**Request:**
```json
{
  "speed": 2,                       // 1 | 2 | 5，可选
  "status": "autonomous"            // "autonomous" | null，可选
}
```

**Response:**
```json
{ "replay_state": { "..." } }
```

---

### 工作空间文件

### GET `/api/sessions/{session_id}/ls/{dir_path}`

列出目录。

**Response:**
```json
[
  { "name": "file.py", "type": "file", "size": 1234 },
  { "name": "src", "type": "directory" }
]
```

### GET `/api/sessions/{session_id}/files/{file_path}`

读取文件内容。

**Response:** 文件内容（text 或 binary stream）

### PUT `/api/sessions/{session_id}/files/{file_path}`

写入文件。

**Request:**
```json
{ "content": "文件内容" }
```

**Response:**
```json
{ "success": true }
```

### POST `/api/sessions/{session_id}/upload/{dir_path}`

上传文件（multipart/form-data）。

**Form Data:**
- `files`: 文件列表（UploadFile[]）
- `paths`: JSON 数组，相对路径（可选）

**Response:**
```json
{
  "uploaded": ["file1.py", "file2.py"],
  "failed": []
}
```

### DELETE `/api/sessions/{session_id}/files/{file_path}`

删除文件或目录。

**Response:**
```json
{ "deleted": true }
```

### POST `/api/sessions/{session_id}/files/{file_path}/rename`

重命名文件。

**Request:**
```json
{ "new_name": "new_file.py" }
```

**Response:**
```json
{ "path": "new_file.py" }
```

### POST `/api/sessions/{session_id}/files/{file_path}/copy`

复制文件。

**Response:**
```json
{ "path": "file_copy.py" }
```

### GET `/api/sessions/{session_id}/download-dir/{dir_path}`

下载目录为 ZIP。

**Response:** ZIP 文件（FileResponse）

---

### 分享

### POST `/api/sessions/{session_id}/share`

创建分享链接。

**Request:**
```json
{
  "ttl_seconds": 86400       // int?, 过期时间（秒），可选
}
```

**Response:**
```json
{
  "token": "share_xxx",
  "url": "https://blade.example.com/share/share_xxx",
  "expires_at": "2026-01-02T00:00:00Z"
}
```

### DELETE `/api/sessions/{session_id}/share/{token}`

撤销分享。

**Response:**
```json
{ "revoked": true }
```

### GET `/api/share/{token}`

获取已分享的会话（公开只读）。

**Response:** Turn 列表（同 GET messages）

---

### 导入 & 导出

### GET `/api/sessions/{session_id}/export`

导出会话为 ZIP。

**Response:** ZIP 文件

### POST `/api/sessions/preview-import`

预览导入（multipart/form-data）。

**Form Data:** `file` (ZIP 文件)

**Response:** 导入预览摘要 dict

### POST `/api/sessions/import`

导入会话（multipart/form-data）。

**Form Data:**
- `file`: ZIP 文件
- `name`: 会话名称（string，默认空）
- `solution_id`: Solution ID（string?）

**Response:** 新会话 dict

---

### Tokenize

### POST `/api/sessions/tokenize/prompt`

计算 prompt token 数。

**Request:**
```json
{
  "prompt": "要计算的文本",
  "model": null               // string?, 模型 ID
}
```

**Response:** Tokenization 结果 dict

### POST `/api/sessions/tokenize/messages`

计算消息列表 token 数。

**Request:**
```json
{
  "messages": [{"role": "user", "content": "hello"}],
  "model": null,
  "add_generation_prompt": true,
  "enable_thinking": null,
  "tools": null
}
```

**Response:** Tokenization 详细结果 dict

---

### 后台任务

### GET `/api/sessions/{session_id}/background-tasks`

列出后台任务。

**Response:** 后台任务列表

### GET `/api/sessions/{session_id}/background-tasks/{task_id}`

获取后台任务输出。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tail` | int | 100 | 返回最后 N 行 |

**Response:** 任务输出 dict

### POST `/api/sessions/{session_id}/background-tasks/{task_id}/stop`

停止后台任务。

**Response:** 任务 dict

---

### 会话技能

### GET `/api/sessions/{session_id}/skills`

列出会话技能。

**Response:** 技能列表

### GET `/api/sessions/{session_id}/skill-stats`

获取技能统计。

**Response:** 技能统计 dict

### POST `/api/sessions/{session_id}/skills:upload`

上传会话级技能。

**Request:**
```json
{
  "name": "my-skill",
  "files": [
    { "path": "SKILL.md", "content": "# My Skill\n..." },
    { "path": "tools/my_tool.py", "content": "..." }
  ]
}
```

**Response:**
```json
{
  "name": "my-skill",
  "skill_dir": "/path/to/skill",
  "file_count": 2,
  "overwritten": false
}
```

### POST `/api/sessions/{session_id}/skills/install`

安装合作伙伴技能。

**Response:** 安装结果 dict

### POST `/api/sessions/{session_id}/skills:resync`

重新同步技能。

**Response:**
```json
{ "detail": "string", "..." }
```

---

### 其他会话接口

### GET `/api/sessions/{session_id}/context-stats`

获取上下文统计。

**Response:** 上下文统计 dict

### GET `/api/sessions/{session_id}/tasks`

获取任务列表。

**Response:** 任务列表

### POST `/api/sessions/{session_id}/share-file`

分享文件到 .share 目录。

**Request:**
```json
{
  "source_path": "workspace/output.csv",
  "link_name": "",              // string, 自定义名称
  "share_folder": ""            // string, .share 下子目录
}
```

**Response:**
```json
{ "path": ".share/output.csv", "target": "workspace/output.csv" }
```

### POST `/api/sessions/{session_id}/upset_extra_info`

更新会话扩展信息。

**Request:**
```json
{ "extra": { "key": "value" } }
```

**Response:**
```json
{
  "session_id": "sess_xxx",
  "extra": { "key": "value" },
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### GET `/api/sessions/{session_id}/extra_info`

获取会话扩展信息。

**Response:**
```json
{
  "session_id": "sess_xxx",
  "extra": { "key": "value" },
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### GET `/api/sessions/extra_info/by_task/{task_id}`

按任务 ID 查会话扩展信息。

**Response:**
```json
{
  "session_id": "sess_xxx | null",
  "extra": { "..." },
  "..."
}
```

---

## Skills

### GET `/api/skills`

列出所有技能。

**Response:** 技能列表

### GET `/api/skills/{skill_id}`

获取技能详情。

**Response:** 技能详情 dict

### GET `/api/skills/search`

语义搜索技能。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | 必填 | 搜索关键词 |
| `limit` | int | 10 | 最多返回（1-50） |

**Response:**
```json
{ "results": [ { "..." } ] }
```

### GET `/api/skills/installed`

已安装技能列表。

**Response:** 技能列表

### GET `/api/skills/scenario-resources`

场景资源列表。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | int | 500 | 最多返回（1-2000） |

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/skill-store/stats`

技能商店统计。

**Response:** 统计 dict

---

## Memories

### POST `/api/memories`

创建记忆。返回 `201`。

**Request:**
```json
{
  "content": "记忆内容",                     // string, 1-500 字符，必填
  "type": "feedback",                        // "feedback" | "experience"，默认 "feedback"
  "skill_name": null,                        // string?, ≤255 字符
  "record_type": null,                       // "memory" | "skill_comment" | null
  "scope": null,                             // string?, ≤255 字符
  "owner": null,                             // string?, ≤255 字符
  "topic": null,                             // string?, ≤255 字符
  "mem0_id": null,                           // string?, 外部 ID ≤255 字符
  "write_reason": null                       // string?, 写入原因 1-500 字符
}
```

**Response:**
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

### GET `/api/memories`

列出记忆。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | string? | - | 搜索关键词 |
| `skill_name` | string? | - | 按技能过滤 |
| `type` | string? | - | 按类型过滤 |
| `record_type` | string? | - | 按记录类型过滤 |
| `scope` | string? | - | 按范围过滤 |
| `owner` | string? | - | 按所有者过滤 |
| `topic` | string? | - | 按主题过滤 |
| `status` | string? | - | 按状态过滤 |
| `offset` | int | 0 | 偏移量 |
| `limit` | int | 20 | 每页数量（1-100） |

**Response:**
```json
{
  "items": [ { "...MemoryResponse" } ],
  "total": 42
}
```

### GET `/api/memories/{memory_id}`

获取记忆。

**Response:** MemoryResponse（同上）

### PUT `/api/memories/{memory_id}`

更新记忆。

**Request:**
```json
{
  "content": null,              // string?, 1-500 字符
  "type": null,                 // "feedback" | "experience" | null
  "skill_name": null,           // string?, ≤255
  "record_type": null,          // "memory" | "skill_comment" | null
  "scope": null,                // string?, ≤255
  "owner": null,                // string?, ≤255
  "topic": null,                // string?, ≤255
  "mem0_id": null,              // string?, ≤255
  "write_reason": null          // string?, ≤500
}
```

**Response:** MemoryResponse

### PATCH `/api/memories/{memory_id}`

启用/禁用记忆。

**Request:**
```json
{ "disabled": true }
```

**Response:** MemoryResponse

### DELETE `/api/memories/{memory_id}`

删除记忆。

**Response:**
```json
{ "ok": true }
```

### POST `/api/memories/batch`

批量操作。

**Request:**
```json
{
  "action": "delete | disable | enable",
  "ids": [1, 2, 3]                         // int[], 1-100 个
}
```

**Response:**
```json
{ "ok": true, "count": 3 }
```

---

## Solutions

### GET `/api/solutions`

列出 Solution。

**Response:**
```json
{
  "items": [
    {
      "id": "solution-id",
      "name": "名称",
      "version": "1.0",
      "description": "描述",
      "layout_type": "default",
      "initial_message": "欢迎...",
      "data": { "..." },
      "roles": [ { "id": "role-id", "name": "角色名", "..." } ]
    }
  ]
}
```

### GET `/api/solutions/{solution_id}/biz-roles`

列出 Solution 的业务角色。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | string? | - | 指定用户（管理员） |

**Response:**
```json
{
  "solution_id": "string",
  "user_id": "string",
  "items": [ { "id": "role-id", "name": "角色名", "..." } ]
}
```

### GET `/api/solutions/{solution_id}/files/{file_path}`

获取 Solution 文件内容。

**Response:** 文本或 JSON

---

## Production Solutions（多智能体 DAG）

### POST `/api/prod_solution`

创建 Prod Solution。

**Request:**
```json
{
  "name": "方案名称",                      // string, 必填（≥1 字符）
  "description": null,                      // string?
  "session_id": null,                       // string?, 关联会话
  "ai_assist": false,                       // bool
  "flow_session_id": null,                  // string?
  "flow_ai_assist": null,                   // bool?
  "architecture_session_id": null,          // string?
  "architecture_ai_assist": false           // bool
}
```

**Response:** Prod Solution dict

### GET `/api/prod_solution`

列出 Prod Solution。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_solution/{prod_solution_id}`

获取 Prod Solution。

**Response:** Prod Solution dict

### PATCH `/api/prod_solution/{prod_solution_id}`

更新 Prod Solution。

**Request:**
```json
{
  "name": null,            // string?
  "description": null,     // string?
  "status": null           // string?
}
```

**Response:** 更新后的 Prod Solution dict

### DELETE `/api/prod_solution/{prod_solution_id}`

**Response:**
```json
{ "ok": true }
```

### PUT `/api/prod_solution/{prod_solution_id}/session`

更新关联会话。

**Request:**
```json
{ "session_id": "sess_xxx" }    // string, 必填（≥1 字符）
```

**Response:**
```json
{ "ok": true }
```

---

### DAG 管理

### GET `/api/prod_solution/dag/{prod_solution_id}`

获取当前 DAG。

**Response:** DAG dict

### PUT `/api/prod_solution/dag/{prod_solution_id}`

保存 DAG。

**Request:**
```json
{
  "base_version": 1,                       // int, ≥1，基于的版本号
  "dag": {
    "steps": [ { "..." } ],               // dict[]?
    "nodes": [ { "..." } ],               // dict[]?
    "edges": [ { "..." } ],               // dict[]?
    "viewport": { "..." }                  // dict?
  },
  "message": null                          // string?, 提交信息
}
```

**Response:** 保存结果 dict

### POST `/api/prod_solution/dag/{prod_solution_id}/validate`

验证 DAG。

**Request:**
```json
{
  "dag": { "steps": [], "nodes": [], "edges": [], "viewport": null }
}
```

**Response:** 验证结果 dict

### POST `/api/prod_solution/dag/{prod_solution_id}/publish`

发布 DAG 版本。

**Request:**
```json
{
  "dag": null,                  // DagPayload?, 不传则用当前
  "version": null,              // int?, ≥1，指定版本
  "message": null               // string?
}
```

**Response:** 发布后的 DAG dict

### GET `/api/prod_solution/dag/{prod_solution_id}/versions`

列出 DAG 版本。

**Response:**
```json
{ "items": [ { "version": 1, "..." } ] }
```

### GET `/api/prod_solution/dag/{prod_solution_id}/versions/{version}`

获取指定版本 DAG。

**Response:** DAG 版本 dict

### DELETE `/api/prod_solution/dag/{prod_solution_id}/versions/{version}`

删除 DAG 版本。

**Response:**
```json
{ "ok": true }
```

### POST `/api/prod_solution/dag/{prod_solution_id}/rollback`

回滚 DAG。

**Request:**
```json
{
  "from_version": 3,           // int, ≥1
  "message": null              // string?
}
```

**Response:** 回滚结果 dict

---

### Architecture 管理

与 DAG 接口结构一致，路径前缀替换为 `/api/prod_solution/architecture/{prod_solution_id}`：

| Method | Path | 说明 |
|--------|------|------|
| GET | `.../architecture/{id}` | 获取当前架构 |
| PUT | `.../architecture/{id}` | 保存架构（`SaveArchitectureRequest`） |
| POST | `.../architecture/{id}/validate` | 验证架构 |
| POST | `.../architecture/{id}/publish` | 发布架构版本 |
| GET | `.../architecture/{id}/versions` | 列出版本 |
| GET | `.../architecture/{id}/versions/{v}` | 获取指定版本 |
| DELETE | `.../architecture/{id}/versions/{v}` | 删除版本 |
| POST | `.../architecture/{id}/rollback` | 回滚 |

`ArchitecturePayload` 与 `DagPayload` 类似：
```json
{
  "nodes": [ { "..." } ],      // dict[], 必填
  "viewport": null              // dict?
}
```

---

### Prod Solution Agents

### GET `/api/prod_solution/agents/runtimes`

列出 Agent 运行时。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### POST `/api/prod_solution/agents`

创建 Agent 实例。

**Request:**
```json
{
  "name": "Agent 名称",           // string, ≥1 字符
  "runtime_id": "runtime_xxx",    // string, ≥1 字符
  "visibility": "workspace",      // string?, 默认 "workspace"
  "instructions": null             // string?
}
```

**Response:** Agent 创建结果 dict

### GET `/api/prod_solution/agents`

列出 Agent 实例。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `include_archived` | bool | false | 包含已归档 |

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_solution/agents/{agent_id}`

获取 Agent 实例。

**Response:** Agent dict

---

## Production Agents

### GET `/api/prod_agents`

列出生产智能体。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_agents/{provider_key}`

获取智能体详情。

**Response:**
```json
{
  "provider": "string",
  "runtime": { "..." },
  "agent": { "..." }
}
```

### GET `/api/prod_agents/catalog/solutions`

Solution 目录。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### POST `/api/prod_agents`

创建生产智能体。

**Request:**
```json
{
  "name": "智能体名称",                     // string, 1-128 字符
  "icon": "",                               // string, ≤64
  "agent_id": null,                         // string?
  "solution_id": "sol_xxx",                 // string, 1-128，必填
  "biz_role_id": "role_xxx",               // string, 1-128，必填
  "agent_template": "",                     // string, ≤200000
  "initial_mode": null,                     // string?, ≤64
  "skills": [],                             // string[], ≤200 个
  "skills_data": {},                        // dict
  "init_script": "",                        // string, ≤200000
  "layout_type": "default",                 // string, ≤64
  "preview_urls": [],                       // PreviewUrl[], ≤200 个
  "runtime_provider": "",                   // string, ≤256
  "visibility": "workspace",               // string, ≤32
  "instructions": ""                        // string, ≤200000
}
```

`PreviewUrl`:
```json
{ "name": "预览名称", "url": "https://..." }    // name: 1-128, url: 1-2000
```

**Response:** 创建结果 dict

### PATCH `/api/prod_agents/{record_id}`

更新生产智能体（字段同 POST，无 `agent_id`）。

**Response:** 更新结果 dict

### DELETE `/api/prod_agents/{record_id}`

**Response:**
```json
{ "ok": true }
```

### POST `/api/prod_agents/{record_id}/instantiate`

实例化智能体。

**Response:** 实例化结果 dict

### POST `/api/prod_agents/{record_id}/start-session`

从智能体启动会话。

**Response:**
```json
{
  "session_id": "sess_xxx",
  "route_solution_id": "sol_xxx"
}
```

---

## API Keys

### GET `/api/user/api-keys/`

列出 API Key。

**Response:**
```json
[
  {
    "id": "key_xxx",
    "name": "My Key",
    "masked": "sk-blade-v2-...xxxx",
    "plaintext": null,
    "created_at": "2026-01-01T00:00:00Z",
    "last_used_at": "2026-01-02T00:00:00Z"
  }
]
```

### GET `/api/user/api-keys/{key_id}`

获取单个 Key。

**Response:** ApiKeyPublic（同上）

### POST `/api/user/api-keys/`

创建 API Key。返回 `201`。

**Request:**
```json
{ "name": "My Backend Key" }     // string, 1-50 字符
```

**Response:**
```json
{
  "key": {
    "id": "key_xxx",
    "name": "My Backend Key",
    "masked": "sk-blade-v2-...xxxx",
    "plaintext": null,
    "created_at": "2026-01-01T00:00:00Z",
    "last_used_at": null
  },
  "plaintext": "sk-blade-v2-xxxxxxxxxxxxxxxx"
}
```

> **注意**：`plaintext` 仅在创建时返回一次，请妥善保存。

### PATCH `/api/user/api-keys/{key_id}`

重命名 Key。

**Request:**
```json
{ "name": "New Name" }          // string, 1-50 字符
```

**Response:** ApiKeyPublic

### DELETE `/api/user/api-keys/{key_id}`

删除 Key。返回 `204 No Content`。

---

## Environment

### GET `/api/env`

环境配置列表。

**Response:**
```json
[
  {
    "group": "LLM",
    "items": [
      {
        "env_var": "API_KEY",
        "value": "sk-...",
        "default": "",
        "remark": "LLM provider API key"
      }
    ]
  }
]
```

### GET `/api/env/check`

运行环境诊断（SSE 流）。

**Response:** Server-Sent Events 流

### POST `/api/env/check/{check_id}`

执行特定检查（SSE 或 JSON）。

**Response:** SSE 流或 JSON dict

---

## User Environment Buckets

### GET `/api/user/env-buckets`

列出环境桶。

**Response:**
```json
[
  { "bucket": "my-project", "env": { "KEY": "VALUE" } }
]
```

### GET `/api/user/env-buckets/{bucket}`

获取环境桶。

**Response:**
```json
{ "bucket": "my-project", "env": { "KEY": "VALUE" } }
```

### PUT `/api/user/env-buckets/{bucket}`

设置环境桶。

**Request:**
```json
{ "env": { "KEY": "VALUE" } }
```

**Response:** EnvBucket

### DELETE `/api/user/env-buckets/{bucket}`

删除环境桶。

**Response:**
```json
{ "bucket": "my-project", "status": "deleted" }
```

---

## User Preferences

### GET `/api/user/preferences/{key}`

获取偏好设置。

**Response:**
```json
{ "value": "string | null" }
```

### PUT `/api/user/preferences/{key}`

设置偏好。

**Request:**
```json
{ "value": "string" }
```

**Response:**
```json
{ "value": "string" }
```

### POST `/api/users/me/reset-computer`

重置用户计算环境。

**Response:**
```json
{
  "removed_containers": 2,
  "removed_volume": true,
  "cleared_memo": 5
}
```

### GET `/api/users/me/computer-upgrade`

检查计算环境升级状态。

**Response:**
```json
{
  "upgrade_available": true,
  "reason": "New sandbox image available",
  "current_version": "v0.4.17",
  "target_version": "v0.4.18"
}
```

### POST `/api/users/me/upgrade-computer`

升级计算环境。

**Response:**
```json
{
  "removed_containers": 1,
  "removed_volume": true,
  "cleared_memo": 3
}
```

---

## Scheduled Tasks

### POST `/api/scheduled-tasks`

创建定时任务。返回 `201`。

**Request:**
```json
{
  "title": "每日报告",                      // string, 1-200 字符
  "prompt": "生成今日数据摘要",             // string, ≥1 字符
  "cron": "0 9 * * *",                     // string, cron 表达式 1-100 字符
  "timezone": "Asia/Shanghai",              // string, 1-100，默认系统时区
  "enabled": true,                          // bool
  "expires_at": null,                       // datetime?
  "skip_confirmations": false,              // bool
  "model": null                             // string?, ≤200
}
```

**Response:** ScheduledTaskPublic

### GET `/api/scheduled-tasks`

列出定时任务。

**Response:** ScheduledTaskPublic 列表

### GET `/api/scheduled-tasks/{task_id}`

获取定时任务。

**Response:** ScheduledTaskPublic

### PATCH `/api/scheduled-tasks/{task_id}`

更新定时任务（所有字段可选，类型同 POST）。

**Response:** ScheduledTaskPublic

### DELETE `/api/scheduled-tasks/{task_id}`

删除定时任务。返回 `204`。

### POST `/api/scheduled-tasks/{task_id}/start`

启动定时任务。

**Response:** ScheduledTaskPublic（enabled=true）

### POST `/api/scheduled-tasks/{task_id}/stop`

停止定时任务。

**Response:** ScheduledTaskPublic（enabled=false）

### GET `/api/scheduled-tasks/calendar`

获取日历视图。

**Query Parameters:**
| 参数 | 类型 | 说明 |
|------|------|------|
| `from` | datetime | 开始时间，必填 |
| `to` | datetime | 结束时间，必填 |

**Response:**
```json
[
  {
    "task_id": "task_xxx",
    "title": "每日报告",
    "occurrences": ["2026-01-01T09:00:00Z", "2026-01-02T09:00:00Z"]
  }
]
```

### GET `/api/scheduled-tasks/{task_id}/runs`

列出任务运行记录。

**Response:**
```json
[
  {
    "id": "run_xxx",
    "task_id": "task_xxx",
    "session_id": "sess_xxx",
    "status": "completed | failed | running",
    "error": null,
    "triggered_at": "2026-01-01T09:00:00Z",
    "finished_at": "2026-01-01T09:05:00Z"
  }
]
```

---

## Admin

### GET `/api/admin/admins`

列出管理员。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### POST `/api/admin/admins`

授权管理员。

**Request:**
```json
{ "user_id": "user_xxx" }
```

**Response:**
```json
{ "ok": true }
```

### DELETE `/api/admin/admins/{user_id}`

撤销管理员。

**Response:**
```json
{ "ok": true }
```

### GET `/api/admin/users/{user_id}/solutions/{solution_id}/biz-roles`

获取用户角色白名单。

**Response:**
```json
{
  "user_id": "user_xxx",
  "solution_id": "sol_xxx",
  "biz_role_ids": ["role_a", "role_b"],
  "default_all": false
}
```

### PUT `/api/admin/users/{user_id}/solutions/{solution_id}/biz-roles`

设置用户角色白名单。

**Request:**
```json
{ "biz_role_ids": ["role_a", "role_b"] }
```

**Response:**
```json
{ "ok": true }
```

---

## Prod Users

### GET `/api/prod_users`

列出生产用户。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### POST `/api/prod_users/token-status`

检查用户 Token 状态。

**Request:**
```json
{
  "users": [
    { "email": "a@example.com", "name": "Alice", "sub": "user_xxx" }
  ]
}
```

**Response:**
```json
{
  "items": [
    { "sub": "user_xxx", "email": "a@example.com", "ok": true, "changed": false, "message": "" }
  ]
}
```

---

## Prod Workspaces

### GET `/api/prod_workspaces`

列出工作空间。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### POST `/api/prod_workspaces`

创建工作空间。

**Request:**
```json
{
  "name": "我的项目",              // string, 1-128
  "description": null              // string?, ≤1000
}
```

**Response:** 工作空间 dict

### GET `/api/prod_workspaces/{workspace_id}`

获取工作空间。

**Response:** 工作空间 dict

### GET `/api/prod_workspaces/{workspace_id}/agents`

列出工作空间智能体。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_workspaces/{workspace_id}/members`

列出工作空间成员。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_workspaces/{workspace_id}/assistant-session`

获取助手会话。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `biz_role_id` | string | `multica_assistant` | 角色 ID |

**Response:** 会话 dict

### PUT `/api/prod_workspaces/{workspace_id}/assistant-session`

创建/更新助手会话。

**Request:**
```json
{
  "biz_role_id": "role_xxx",      // string, 1-128
  "session_id": "sess_xxx"        // string, 1-128
}
```

**Response:** 会话 dict

---

### Workspace Issues

### POST `/api/prod_workspaces/{workspace_id}/issues`

创建 Issue。

**Request:**
```json
{
  "title": "Bug: 登录失败",                  // string, ≥1 字符
  "description": null,                       // string?
  "priority": null,                          // "urgent" | "high" | "medium" | "low" | "none" | null
  "status": null,                            // "backlog" | "todo" | "in_progress" | "in_review" | "done" | "blocked" | "cancelled" | null
  "assignee": null,                          // string?, 负责人名称
  "assignee_type": null,                     // "member" | "agent" | "squad" | null
  "assignee_id": null,                       // string?, 负责人 ID
  "project": null                            // string?, 项目名称
}
```

**Response:** Issue dict

### GET `/api/prod_workspaces/{workspace_id}/issues`

列出 Issues。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/prod_workspaces/{workspace_id}/issues/query`

查询 Issues（query params 转发后端）。

### GET `/api/prod_workspaces/{workspace_id}/issues/grouped`

分组查询 Issues。

### GET `/api/prod_workspaces/{workspace_id}/issues/child-progress`

子 Issue 进度。

### GET `/api/prod_workspaces/{workspace_id}/issues/{issue_id}`

获取单个 Issue。

### PUT `/api/prod_workspaces/{workspace_id}/issues/{issue_id}`

更新 Issue。

**Request:** Issue 字段 dict

**Response:** 更新后的 Issue dict

### GET `/api/prod_workspaces/{workspace_id}/issues/{issue_id}/timeline`

Issue 时间线。

### GET `/api/prod_workspaces/{workspace_id}/issues/{issue_id}/task-runs`

Issue 任务运行记录。

### GET `/api/prod_workspaces/{workspace_id}/issues/{issue_id}/usage`

Issue 用量统计。

---

## Published Apps

### POST `/api/published-apps`

发布应用。

**Request:**
```json
{
  "session_id": "sess_xxx",
  "working_dir": null              // string?
}
```

**Response:** 发布结果 dict

### GET `/api/published-apps`

列出已发布应用。

**Response:**
```json
{ "items": [ { "..." } ] }
```

### GET `/api/published-apps/{session_id}`

获取发布信息。

**Response:** 发布详情 dict

### DELETE `/api/published-apps/{session_id}`

取消发布。

**Response:** 取消结果 dict

---

## Registry

### GET `/api/registry/resources`

列出注册资源。

**Query Parameters:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | string? | - | 资源类型 |
| `subtype` | string? | - | 子类型 |
| `limit` | int | 200 | 每页数量 |
| `offset` | int | 0 | 偏移量 |

**Response:** 资源列表

### GET `/api/registry/resources/{resource_id}`

获取资源。

### GET `/api/registry/skills/orgs`

列出技能组织。

### GET `/api/registry/templates`

列出模板。

### GET `/api/registry/templates/{type_key}/{subtype}`

获取模板。

**Query Parameters:**
| 参数 | 类型 | 说明 |
|------|------|------|
| `driver` | string? | 驱动类型 |

**Response:** 模板 dict

---

## GIS

### GET `/api/gis/{session_id}/state`

GIS 态势分析状态。

**Response:** 态势状态 dict

---

## Payload Annotations

### GET `/api/payloads/{payload_id}/annotations`

获取请求标注。

### POST `/api/payloads/{payload_id}/annotations`

创建标注。

### PATCH `/api/payloads/{payload_id}/annotations/{annotation_id}`

更新标注。

### DELETE `/api/payloads/{payload_id}/annotations/{annotation_id}`

删除标注。

---

## Frontend Config

### GET `/api/frontend_config/{file_path}`

获取前端配置文件。

### PUT `/api/frontend_config/{file_path}`

更新前端配置文件。

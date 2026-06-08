# REST API

基础路径：`/api`

---

## Health & Configuration

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/healthz` | 备用健康检查 |
| GET | `/api/config` | 运行时配置（ASR、Sentry、PostHog 等） |
| GET | `/api/config/models` | 可用 LLM 模型列表 |

---

## Authentication

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/auth/me` | 当前用户信息（JWT/cookie 或 API Key） |

---

## Sessions

### CRUD

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions` | 列出会话（支持搜索、分页） |
| GET | `/api/sessions/{session_id}` | 获取会话详情 |
| PUT | `/api/sessions/{session_id}` | 更新会话（intent） |
| DELETE | `/api/sessions/{session_id}` | 删除会话 |

#### 创建会话请求体

```json
{
  "intent": "用户任务描述",
  "solution_id": "string | null",
  "model": "string | null",
  "memory_enabled": true,
  "is_persistent": false,
  "env": { "KEY": "VALUE" },
  "workspace_id": "string | null",
  "disable_tools": ["tool_name"]
}
```

### 聊天历史

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/sessions/{session_id}/turns` | 获取 Turn 列表（渲染后的投影） |
| GET | `/api/sessions/{session_id}/turns/{turn_id}` | 获取单个 Turn |

### 标题生成

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/intent` | AI 生成会话标题 |

### 分享

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/share` | 分享会话 |
| POST | `/api/sessions/{session_id}/sharing` | 开启/关闭分享 |

### 检查点 & 回退

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/checkpoint` | 创建检查点 |
| GET | `/api/sessions/{session_id}/checkpoints` | 列出检查点 |
| POST | `/api/sessions/{session_id}/rewind` | 回退到检查点 |
| POST | `/api/sessions/{session_id}/checkout` | 查看某个 Turn 的状态（不修改） |

### 工作空间文件

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/sessions/{session_id}/workspace` | 列出文件 |
| POST | `/api/sessions/{session_id}/workspace/upload` | 上传文件 |
| GET | `/api/sessions/{session_id}/workspace/{path}` | 读取文件 |
| PUT | `/api/sessions/{session_id}/workspace/{path}` | 写入文件 |
| DELETE | `/api/sessions/{session_id}/workspace/{path}` | 删除文件 |
| POST | `/api/sessions/{session_id}/workspace/{path}/rename` | 重命名文件 |

### 沙箱 & 环境

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/sandbox:reset` | 重置沙箱 |
| POST | `/api/sessions/{session_id}/env` | 更新会话环境变量 |
| POST | `/api/sessions/{session_id}/mode` | 切换 planning/executing 模式 |
| POST | `/api/sessions/{session_id}/memory` | 开启/关闭记忆 |

### 导入 & 导出

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/import` | 导入会话 |
| GET | `/api/sessions/{session_id}/export` | 导出会话 |

### 其他

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sessions/{session_id}/replay` | 创建回放会话 |
| GET | `/api/sessions/{session_id}/bg-tasks` | 后台任务输出 |
| GET | `/api/sessions/{session_id}/payloads` | LLM 请求日志 |
| GET | `/api/sessions/{session_id}/annotations` | 标注数据 |
| POST | `/api/sessions/{session_id}/tokenize:prompt` | Token 计数（prompt） |
| POST | `/api/sessions/{session_id}/tokenize:messages` | Token 计数（messages） |

---

## Skills

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/skills` | 列出所有技能 |
| GET | `/api/skills/{skill_id}` | 获取技能详情 |
| GET | `/api/skills/search?q=` | 语义搜索技能 |
| GET | `/api/skills/installed` | 已安装技能列表 |
| GET | `/api/skills/scenario-resources` | 场景资源列表 |
| GET | `/api/skill-store/stats` | 技能商店统计 |
| POST | `/api/sessions/{session_id}/skills:upload` | 上传会话级技能 |
| POST | `/api/sessions/{session_id}/skills:resync` | 重新同步技能 |
| POST | `/api/sessions/{session_id}/skills/install` | 安装合作伙伴技能 |

---

## Memories

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/memories` | 创建记忆 |
| GET | `/api/memories` | 列出记忆（搜索、分页） |
| GET | `/api/memories/{memory_id}` | 获取记忆 |
| PUT | `/api/memories/{memory_id}` | 更新记忆 |
| PATCH | `/api/memories/{memory_id}` | 部分更新记忆 |
| DELETE | `/api/memories/{memory_id}` | 删除记忆 |
| POST | `/api/memories/batch` | 批量操作 |

---

## Solutions（工作流/智能体模板）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/solutions` | 列出可用 Solution |
| GET | `/api/solutions/{solution_id}` | 获取 Solution 详情 |
| POST | `/api/solutions` | 创建 Solution（管理员） |
| PUT | `/api/solutions/{solution_id}` | 更新 Solution |
| DELETE | `/api/solutions/{solution_id}` | 删除 Solution |

---

## Production Solutions（多智能体 DAG）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/prod-solutions` | 列出生产 Solution |
| POST | `/api/prod-solutions` | 创建 |
| GET | `/api/prod-solutions/{id}` | 获取 |
| PATCH | `/api/prod-solutions/{id}` | 更新 |
| DELETE | `/api/prod-solutions/{id}` | 删除 |
| GET | `/api/prod-solutions/{id}/dag` | 获取 DAG 定义 |
| PUT | `/api/prod-solutions/{id}/dag` | 更新 DAG |
| POST | `/api/prod-solutions/{id}/dag/validate` | 验证 DAG |
| POST | `/api/prod-solutions/{id}/dag/publish` | 发布 DAG 版本 |
| GET | `/api/prod-solutions/{id}/dag/versions` | DAG 版本列表 |
| GET | `/api/prod-solutions/{id}/architecture` | 获取架构 |
| PUT | `/api/prod-solutions/{id}/architecture` | 更新架构 |
| POST | `/api/prod-solutions/{id}/architecture/validate` | 验证架构 |
| POST | `/api/prod-solutions/{id}/architecture/publish` | 发布架构 |

---

## Production Agents（生产智能体）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/prod-agents` | 列出生产智能体 |
| GET | `/api/prod-agents/{provider_key}` | 获取智能体详情 |
| POST | `/api/prod-agents` | 创建 |
| PATCH | `/api/prod-agents/{record_id}` | 更新 |
| DELETE | `/api/prod-agents/{record_id}` | 删除 |
| POST | `/api/prod-agents/{record_id}/instantiate` | 实例化到会话 |
| POST | `/api/prod-agents/{record_id}/start-session` | 从智能体启动会话 |
| GET | `/api/prod-agents/catalog/solutions` | Solution 目录 |

---

## API Keys

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/api-keys` | 列出 API Key |
| GET | `/api/api-keys/{key_id}` | 获取 Key 详情 |
| POST | `/api/api-keys` | 创建 Key（返回明文，仅一次） |
| PATCH | `/api/api-keys/{key_id}` | 更新 Key |
| DELETE | `/api/api-keys/{key_id}` | 吊销 Key |

---

## Environment & Configuration

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/env` | 环境检查列表 |
| GET | `/api/env/check` | 运行诊断 |
| POST | `/api/env/check/{check_id}` | 执行特定检查 |
| GET | `/api/user-env` | 用户级环境变量 |
| POST | `/api/user-env` | 更新用户环境 |
| GET | `/api/admin-env/global` | 全局环境（管理员） |
| PUT | `/api/admin-env/global` | 更新全局环境（管理员） |
| DELETE | `/api/admin-env/global` | 删除全局环境（管理员） |
| GET | `/api/admin-env/platform` | 平台环境（只读） |

---

## 其他接口

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/gis/{session_id}/state` | GIS 态势分析状态 |
| GET | `/api/payloads/{id}/annotations` | 请求标注 |
| POST | `/api/payloads/{id}/annotations` | 创建标注 |
| PATCH | `/api/payloads/{id}/annotations/{ann_id}` | 更新标注 |
| DELETE | `/api/payloads/{id}/annotations/{ann_id}` | 删除标注 |
| GET | `/api/frontend_config/{path}` | 前端配置 |
| PUT | `/api/frontend_config/{path}` | 更新前端配置 |
| GET | `/api/scheduled-tasks` | 定时任务列表 |
| POST | `/api/scheduled-tasks` | 创建定时任务 |
| PATCH | `/api/scheduled-tasks/{task_id}` | 更新定时任务 |
| DELETE | `/api/scheduled-tasks/{task_id}` | 删除定时任务 |

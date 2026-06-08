# API 概览

## 架构

Blade Agent 由三层组成：

```
┌─────────────────────────────────────────────┐
│  Transport (server)                         │
│  FastAPI + Socket.IO — HTTP/WS 传输层       │
├─────────────────────────────────────────────┤
│  Host (host)                                │
│  Engine / Session / LLM / Skills / Tools    │
├─────────────────────────────────────────────┤
│  Core (core)                                │
│  Protocol 定义 + 纯函数 agent_loop()         │
└─────────────────────────────────────────────┘
```

- **Core** — 协议定义（`ToolSpec`, `ToolResult`, `LLMClient` 等）+ 纯函数 `agent_loop()`
- **Host** — 所有实现：Engine、会话管理、LLM 对接、技能加载、工具注册
- **Server** — HTTP REST + Socket.IO 实时传输

## 认证

所有请求（REST 和 Socket.IO）使用统一的 **Bearer Token**：

```
Authorization: Bearer sk-blade-v2-...
```

### Token 类型

| 类型 | 说明 | 获取方式 |
|------|------|----------|
| API Key | 长期有效，推荐后端使用 | Web UI 创建 或 SDK `client.apiKeys.createApiKey()` |
| Session JWT | 短期有效，浏览器同源使用 | 登录后自动获取（cookie） |

### TypeScript 客户端

```typescript
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-v2-..."           // 静态
  // token: () => getTokenFromStore() // 动态（token 变化后需重连 socket）
})
```

### Python 客户端

```python
from blade_agent_kit import BladeAgentClient

async with BladeAgentClient(
    "http://127.0.0.1:8020",
    token="sk-blade-v2-...",  # 或 env BLADE_AGENT_TOKEN
) as client:
    ...
```

## SDK 入口

### NPM (`@blade-hq/agent-kit`)

```bash
npm install @blade-hq/agent-kit
```

| 入口 | 用途 |
|------|------|
| `@blade-hq/agent-kit/client` | `BladeClient`（纯 JS，任意框架） |
| `@blade-hq/agent-kit/react` | `BladeClientProvider`, `useChat`, `useSessionStore`, `useUiBridgeStore` |
| `@blade-hq/agent-kit/chat` | `ChatView` React 组件 |
| `@blade-hq/agent-kit/style.css` | ChatView 样式 |

### PyPI (`blade-agent-kit`)

```bash
pip install blade-agent-kit
```

```python
from blade_agent_kit import (
    BladeAgentClient,
    TurnStart, TurnPatch, TurnEnd, ChatEnd, SystemError,
)
```

## BladeClient 方法总览

### Sessions

```typescript
client.sessions.createSession(intent: string)
client.sessions.getSession(sessionId)
client.sessions.listSessions()
client.sessions.getSessionTurns(sessionId)
client.sessions.getSessionHistory(sessionId)
client.sessions.deleteSession(sessionId)
```

### Skills

```typescript
client.skills.uploadSessionSkill(sessionId, { name, files })
client.skills.listSessionSkills(sessionId)
client.skills.getSkillStats(sessionId)
```

### API Keys

```typescript
client.apiKeys.createApiKey(name)
client.apiKeys.listApiKeys()
client.apiKeys.renameApiKey(id, name)
client.apiKeys.deleteApiKey(id)
```

### Headless QA

```typescript
const reply = await client.headless.run(prompt, {
  schema?,      // JSON Schema → 结构化输出
  model?,       // 模型 ID
  timeoutMs?,   // 超时（默认 300000）
})
```

### Socket

```typescript
const socket = client.socket()
```

> **Node.js 注意**：使用完毕必须 `socket.disconnect()`，否则进程不会退出。

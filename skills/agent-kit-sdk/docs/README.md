# Blade Agent API Documentation

Blade Agent 的 API 接口文档，涵盖 REST、WebSocket、核心类型与会话/聊天设计。

## 目录

| 文档 | 说明 |
|------|------|
| [API 概览](./API概览.md) | 架构总览、认证方式、SDK 入口 |
| [REST 接口](./REST接口.md) | 全部 HTTP 接口（Sessions / Skills / Memories / Solutions / API Keys 等） |
| [WebSocket 接口](./WebSocket接口.md) | Socket.IO 事件协议（chat、turn、session 等） |
| [核心类型](./核心类型.md) | TurnProjection / ContentBlock / ToolCall / Patch 等数据模型 |
| [会话生命周期](./会话生命周期.md) | 会话创建 → 订阅 → 聊天 → 销毁 全流程 |
| [Chat 流程](./Chat流程.md) | 聊天请求/响应流、流式更新、工具调用、子智能体、AskUser 交互 |

## 版本要求

| 组件 | 最低版本 |
|------|----------|
| Docker 镜像 | `registry.cn-beijing.aliyuncs.com/bladeai/blade-agent:v0.4.17` |
| NPM 包 | `@blade-hq/agent-kit@0.4.17` |
| Python 包 | `blade-agent-kit==0.4.17` |

## 平台兼容性

| 能力 | React | Vue | Node.js | Python |
|------|-------|-----|---------|--------|
| Chat UI 组件 | ChatView | 自行渲染 | - | - |
| Headless QA | BladeClient | BladeClient | BladeClient | BladeAgentClient |
| REST API | BladeClient | BladeClient | BladeClient | BladeAgentClient |
| Socket.IO 流式 | useChat / socket | socket | socket | async iterator |
| API Key 管理 | SDK | SDK | SDK | 仅消费 |

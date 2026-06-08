# Blade Agent API 接口文档

本文档面向**任意语言**的开发者（Go、Java、Python、前端等），描述 Blade Agent 的 HTTP 和 WebSocket 接口协议。

## 目录

| 文档 | 说明 |
|------|------|
| [API 概览](./API概览.md) | 架构、基础地址、认证、通用约定 |
| [REST 接口](./REST接口.md) | 全部 HTTP 端点，含请求/响应 JSON |
| [WebSocket 接口](./WebSocket接口.md) | Socket.IO 实时事件协议 |
| [数据模型](./核心类型.md) | 所有 JSON 对象结构定义 |
| [会话生命周期](./会话生命周期.md) | 会话从创建到销毁的完整流程 |
| [Chat 流程](./Chat流程.md) | 聊天交互：流式响应、工具调用、用户问答、子智能体 |

## 传输协议

| 协议 | 用途 |
|------|------|
| HTTP REST | 资源 CRUD（会话、技能、记忆、配置等） |
| WebSocket (Socket.IO) | 实时聊天流（发送消息、接收流式回复） |

> Socket.IO 是基于 WebSocket 的上层协议，大多数语言都有现成的客户端库（Go: `go-socket.io`、Java: `socket.io-client-java`、Python: `python-socketio`）。

## 版本要求

对接时请确保 Blade Agent 服务端版本 ≥ `v0.4.17`。

---
name: agent-kit-sdk
description: "Agent Kit 集成目录：按 React、Vue 前端与 Node.js、Python 后端引导接入 Blade Agent。"
---

# Agent Kit 集成目录

本文件只做目录导航。根据宿主技术栈选择要读的文档。

## 使用规则

如果你不确定某个 SDK 入口、方法名、事件名、REST 路径、依赖版本或返回字段，必须先回到本技能的 reference 文档查找确认；不要按常见框架经验猜测 Blade API。文档没有明确写出的 Blade endpoint、SDK 方法或包入口，不要自行发明。

交付前必须自检：列出你实际采用的 SDK 包入口、依赖版本、session 创建方法、文件上传方法、任务发送方式和事件监听方式；这些项目必须能在本技能文档中找到依据。任一项找不到依据时，先继续查文档或改用文档中的示例，不要交付猜测实现。

Node.js 后端应用必须使用 `@blade-hq/agent-kit@0.5.11` 和 `@blade-hq/agent-kit/client`。`docs/rest-api.md`、`docs/websocket-api.md` 等底层协议文档只用于查证 SDK 背后的公开 endpoint 和事件；除非用户明确要求“不要使用 SDK，直接协议接入”，否则不能用 `axios`、`fetch` 或裸 `socket.io-client` 替代 Node SDK。`DOCS_AUDIT.md` 的 SDK 包入口不能写“无特定 SDK”。

## 版本要求

本技能基于以下版本或以上：

- 阿里云镜像：`registry.cn-beijing.aliyuncs.com/bladeai/blade-agent:v0.4.17`
- NPM：`@blade-hq/agent-kit@0.5.11`
- React peer dependencies：`react@^19.0.0`、`react-dom@^19.0.0`、`@tanstack/react-query@^5.0.0`、`sonner@^2.0.7`
- PyPI：`blade-agent-kit==0.4.17`

低于上述版本时，部分 API、样式入口或 skills 行为可能不一致，请先升级再按本技能集成。

## 第一步：拿到 token（所有场景必读）

SDK 的所有 REST 和 Socket.IO 请求都需要 Bearer token，且 **API key 必须先登录才能创建**。开始集成前先读：

- [references/auth-token.md](references/auth-token.md)：token 类型、创建 API key 的顺序、在 SDK 里注入 token。

## React 应用

React 应用可以直接复用 SDK 组件。

阅读：

- [references/react-quickstart.md](references/react-quickstart.md)：React 最小可复制模板。先看这份，避免 React 版本、包入口、依赖版本和端点写错。
- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：安装、包入口、`BladeClient`、token、baseUrl。
- [references/chat-ui.md](references/chat-ui.md)：`ChatView`、`BladeClientProvider`、组件自定义、headless hooks。
- [references/events-and-types.md](references/events-and-types.md)：用 `useChat` headless 自渲染时，查 `ChatMessage` / 工具调用 / 事件字段。
- [references/session-runtime.md](references/session-runtime.md)：session 创建、active session、Socket.IO、运行时 token。
- [references/work-modes.md](references/work-modes.md)：规划模式与干活模式，`mode: "executing"` / `mode: "planning"` 的使用时机。
- [references/file-upload.md](references/file-upload.md)：上传普通业务文件到 session workspace，并让 Agent 在干活模式读取处理。
- [references/host-app-integration.md](references/host-app-integration.md)：宿主页面给 ChatView 加上下文、追加输入、接收工具触发的页面动作。
- [references/session-skill-upload.md](references/session-skill-upload.md)：如果要把 skill 临时上传到指定 session，比如地图操控、查 CRM、生成订单，就读这份。
- [references/troubleshooting.md](references/troubleshooting.md)：常见问题。

## Vue 应用

Vue 不能直接使用 React 版 `ChatView`，需要用 SDK client / socket 自己渲染聊天 UI。

**完整示例项目**：[examples/vue-chat/](examples/vue-chat/)，包含流式对话、工具调用、AskUserQuestion 交互、子智能体渲染，可直接复制使用。

阅读：

- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：安装、`@blade-hq/agent-kit/client`、token、baseUrl。
- [references/session-runtime.md](references/session-runtime.md)：session、Socket.IO 订阅、发送消息、流式事件。
- [references/work-modes.md](references/work-modes.md)：自渲染前端发送任务时，如何显式进入干活模式。
- [references/file-upload.md](references/file-upload.md)：用户上传 Markdown、文本、CSV 等普通业务文件后，如何放入 session workspace。
- [references/chat-ui.md](references/chat-ui.md)：只看 headless 数据结构和自渲染要点，不使用 React 组件部分。
- [references/events-and-types.md](references/events-and-types.md)：自渲染必读的事件 → payload 映射、TurnProjection / ContentBlock / 工具调用字段速查。
- [references/host-app-integration.md](references/host-app-integration.md)：需要页面联动、上下文注入或工具 UI 时再读。
- [references/session-skill-upload.md](references/session-skill-upload.md)：如果要把 skill 临时上传到指定 session，比如地图操控、查 CRM、生成订单，就读这份。
- [references/troubleshooting.md](references/troubleshooting.md)：常见问题。

## Node.js / Python 后端

后端不渲染 UI，只通过网络调用：建会话、发消息拿结果、headless 一次性问答、读历史、上传 session skill。

Node.js 后端的默认集成方式是 SDK，不是裸协议。先复制 [references/backend-quickstart.md](references/backend-quickstart.md) 的模板；`docs/` API 文档是补充查证资料，不是替代 SDK 的实现许可。

阅读：

- [references/backend-quickstart.md](references/backend-quickstart.md)：Node.js 后端最小可复制模板。先看这份，避免 `/api/v1/*`、JSON workspace 上传和 task polling 写错。
- [references/backend.md](references/backend.md)：Node.js（`@blade-hq/agent-kit/client`）和 Python（`blade-agent-kit`）完整后端用法，含 headless、流式、会话与历史。
- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：`@blade-hq/agent-kit/client` 包入口和基础配置（Node 适用）。
- [references/work-modes.md](references/work-modes.md)：后端代用户发任务时，通常显式传 `mode: "executing"`。
- [references/file-upload.md](references/file-upload.md)：普通文件上传到 session workspace；文档分析、表格分析、报告生成这类后端必读。
- [references/session-skill-upload.md](references/session-skill-upload.md)：上传或管理指定 session 里的临时 skill。
- [references/troubleshooting.md](references/troubleshooting.md)：鉴权、连接和 session skill 上传问题。

后端如果要确认底层 HTTP / Socket.IO 协议，必须继续查 SDK API 文档：

- [docs/README.md](docs/README.md)：API 文档目录和适用范围。
- [docs/api-overview.md](docs/api-overview.md)：ASCII 路径；基础地址、认证和通用约定。
- [docs/rest-api.md](docs/rest-api.md)：ASCII 路径；公开 HTTP endpoint 列表，确认 session、文件上传、历史等 REST 路径。
- [docs/websocket-api.md](docs/websocket-api.md)：ASCII 路径；Socket.IO 连接、`session:subscribe`、`chat:send`、`turn:*`、`chat:end`、`system:error` 等事件。
- [docs/chat-flow.md](docs/chat-flow.md)：ASCII 路径；流式聊天、工具调用、用户问答、子智能体流程。
- [docs/core-types.md](docs/core-types.md)：ASCII 路径；事件 payload 和响应对象结构。
- [docs/API概览.md](docs/API概览.md)：基础地址、认证和通用约定。
- [docs/REST接口.md](docs/REST接口.md)：公开 HTTP endpoint 列表，确认 session、文件上传、历史等 REST 路径。
- [docs/WebSocket接口.md](docs/WebSocket接口.md)：Socket.IO 连接、`session:subscribe`、`chat:send`、`turn:*`、`chat:end`、`system:error` 等事件。
- [docs/Chat流程.md](docs/Chat流程.md)：流式聊天、工具调用、用户问答、子智能体流程。
- [docs/核心类型.md](docs/核心类型.md)：事件 payload 和响应对象结构。

交付后端代码前，必须能说明每个 Blade API 调用来自上述 reference 或 docs 文件中的哪一条依据。

读取 `docs/` 文件时复制下面的精确路径；中文文件名中没有空格，例如是 `docs/API概览.md`，不是 `docs/API 概览.md`：

```text
docs/README.md
docs/api-overview.md
docs/rest-api.md
docs/websocket-api.md
docs/chat-flow.md
docs/core-types.md
docs/API概览.md
docs/REST接口.md
docs/WebSocket接口.md
docs/Chat流程.md
docs/核心类型.md
```

## 功能区域

- Vue 完整示例（流式 + 工具 + 问答 + 子智能体）：[examples/vue-chat/](examples/vue-chat/)
- 鉴权与 token：[references/auth-token.md](references/auth-token.md)
- React 快速开始：[references/react-quickstart.md](references/react-quickstart.md)
- 后端快速开始：[references/backend-quickstart.md](references/backend-quickstart.md)
- 后端集成（Node.js / Python）：[references/backend.md](references/backend.md)
- 底层 API 文档目录：[docs/README.md](docs/README.md)
- REST / Socket.IO API 概览：[docs/API概览.md](docs/API概览.md)
- REST endpoint 速查：[docs/REST接口.md](docs/REST接口.md)
- Socket.IO 事件速查：[docs/WebSocket接口.md](docs/WebSocket接口.md)
- SDK 入口：[references/sdk-entrypoints.md](references/sdk-entrypoints.md)
- 聊天 UI 与自渲染：[references/chat-ui.md](references/chat-ui.md)
- 事件与数据结构速查：[references/events-and-types.md](references/events-and-types.md)
- 会话、鉴权与运行时：[references/session-runtime.md](references/session-runtime.md)
- 规划模式与干活模式：[references/work-modes.md](references/work-modes.md)
- 普通文件上传：[references/file-upload.md](references/file-upload.md)
- 宿主页面联动：[references/host-app-integration.md](references/host-app-integration.md)
- Session skill 上传：[references/session-skill-upload.md](references/session-skill-upload.md)
- 故障排查：[references/troubleshooting.md](references/troubleshooting.md)

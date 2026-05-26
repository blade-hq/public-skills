---
name: agent-kit-sdk
description: "Agent Kit 集成目录：按 React、Vue、Node.js 引导接入 Blade Agent。"
---

# Agent Kit 集成目录

本文件只做目录导航。根据宿主技术栈选择要读的文档。

## React 应用

React 应用可以直接复用 SDK 组件。

阅读：

- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：安装、包入口、`BladeClient`、token、baseUrl。
- [references/chat-ui.md](references/chat-ui.md)：`ChatView`、`BladeClientProvider`、组件自定义、headless hooks。
- [references/session-runtime.md](references/session-runtime.md)：session 创建、active session、Socket.IO、运行时 token。
- [references/host-app-integration.md](references/host-app-integration.md)：宿主页面给 ChatView 加上下文、追加输入、接收工具触发的页面动作。
- [references/session-skill-upload.md](references/session-skill-upload.md)：如果要把 skill 临时上传到指定 session，比如地图操控、查 CRM、生成订单，就读这份。
- [references/troubleshooting.md](references/troubleshooting.md)：常见问题。

## Vue 应用

Vue 不能直接使用 React 版 `ChatView`，需要用 SDK client / socket 自己渲染聊天 UI。

阅读：

- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：安装、`@blade-hq/agent-kit/client`、token、baseUrl。
- [references/session-runtime.md](references/session-runtime.md)：session、Socket.IO 订阅、发送消息、流式事件。
- [references/chat-ui.md](references/chat-ui.md)：只看 headless 数据结构和自渲染要点，不使用 React 组件部分。
- [references/host-app-integration.md](references/host-app-integration.md)：需要页面联动、上下文注入或工具 UI 时再读。
- [references/session-skill-upload.md](references/session-skill-upload.md)：如果要把 skill 临时上传到指定 session，比如地图操控、查 CRM、生成订单，就读这份。
- [references/troubleshooting.md](references/troubleshooting.md)：常见问题。

## Node.js / 服务端脚本

Node.js 通常使用纯 client，不使用 React 组件和 CSS。

阅读：

- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：`@blade-hq/agent-kit/client` 和基础配置。
- [references/session-runtime.md](references/session-runtime.md)：创建 session、读取历史、底层 socket。
- [references/session-skill-upload.md](references/session-skill-upload.md)：上传或管理指定 session 里的临时 skill。
- [references/troubleshooting.md](references/troubleshooting.md)：鉴权、连接和 session skill 上传问题。

## 功能区域

- SDK 入口：[references/sdk-entrypoints.md](references/sdk-entrypoints.md)
- 聊天 UI 与自渲染：[references/chat-ui.md](references/chat-ui.md)
- 会话、鉴权与运行时：[references/session-runtime.md](references/session-runtime.md)
- 宿主页面联动：[references/host-app-integration.md](references/host-app-integration.md)
- Session skill 上传：[references/session-skill-upload.md](references/session-skill-upload.md)
- 故障排查：[references/troubleshooting.md](references/troubleshooting.md)

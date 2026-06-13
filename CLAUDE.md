# Blade Agent 文档站点

## 项目定位

本仓库是 Blade Agent 全家桶的统一文档站点，使用 VitePress 构建，部署在 GitHub Pages。

文档同时作为 AI Skill 使用——AI 辅助编程时可以参考文档内容来指导开发。

## 文档读者

文档面向两类读者，所有内容必须明确属于其中一类：

1. **非程序员用户**：想使用 Blade 平台完成业务工作的人（财务、法务、产品经理等）。他们关心的是如何操作，不需要看代码。
2. **开发者**：通过 SDK 将 Blade Agent 接入自己应用的集成开发者，或通过 Solution/Skill 机制扩展平台能力的开发者。

不面向任何一类读者的内部知识（如平台架构、组件关系、部署拓扑）不放进用户文档，写在本文件中供 AI 编程参考。

## 全家桶组件关系

| 项目 | 定位 |
|------|------|
| blade-agent | 核心 AI Agent 引擎 + Web UI + SDK（`@blade-hq/agent-kit`） |
| skill_registry | Skill 注册中心，提供搜索、版本管理、上传下载 |
| blade-os | 浏览器桌面工作台，应用以 ES Module 懒加载 |
| llm-gateway | 统一 LLM 网关，多上游路由 + OpenAI/Anthropic 协议互转 |
| mock-center | 演示数据中心，提供 HTTP/MCP 接口的模拟数据集 |

各项目源码位置：`~/code-space/{blade-agent, skill_registry, blade-os, llm-gateway, mock-center}`

## 技术栈

- 文档框架：VitePress
- 部署：GitHub Pages（GitHub Actions 自动构建）
- 包管理：pnpm

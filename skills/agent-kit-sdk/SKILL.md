---
name: agent-kit-sdk
description: "开发 Blade Agent npm SDK / @blade-hq/agent-kit React 组件时使用。覆盖 ChatView 自定义渲染、classNames/components/renderers 扩展、skills/@skill mention/SkillStatusBar 接入、SDK API 边界和前端验证。"
---

# Agent Kit SDK

用于修改 `web/packages/agent-kit`，尤其是 npm SDK 的 React chat 组件、client API、skills 接入和对外导出面。

## 先确认边界

- SDK 是给第三方开发者用的，优先保持 API 稳定、类型清晰、可组合。
- 不要为了前端自定义新增后端专属事件；优先复用现有 message / tool_call / block / skills API。
- `ChatView` 负责默认体验和数据流，重度自定义应通过 `useChat(sessionId)`、`skillsApi`、`useSkills()` 等 headless 能力完成。
- 业务文案面向非技术用户；SDK 类型、props 和注释使用清晰常见英文。

## ChatView 自定义约定

修改聊天 UI 时优先维护这四层能力：

1. `classNames`：让宿主改样式，不改逻辑。
2. `components`：让宿主替换语义节点，例如 `EmptyState`、`UserMessage`、`AssistantTurn`、`ToolCall`、`SkillStatusBar`。
3. `renderers`：让宿主替换数据驱动渲染，例如特定 tool renderer。
4. headless hooks：保留 `useChat` / stores / API client，允许宿主完全自建 UI。

新增扩展点时，使用语义节点，不要暴露每个内部 `div/span`。优先选择：

- root / viewerBanner
- messageListRoot / messageListContent / messageListInner / emptyState
- userMessage / errorMessage / assistantTurn / assistantText / toolCall
- chatInputRoot / chatInputInner
- skillStatusBarRoot / skillStatusBarInner

## Skills 接入

Blade Agent 自己的 skills 能力已经通过以下路径进入 SDK：

- `web/packages/agent-kit/src/react/api/skills.ts`
- `web/packages/agent-kit/src/react/hooks/use-skills.ts`
- `ChatInput` 的 `/` skill command 和 `@skill` mention
- `SkillStatusBar`
- `ToolCallBlock` / `AssistantTurnBlock` 中的 `LoadSkillTools`、`SearchSkills` 等工具展示

Anthropic-style skills 是 filesystem artifact，通常位于 `.claude/skills/<name>/SKILL.md`。不要假设存在 SDK 级 programmatic registration API。前端 SDK 需要支持的是：

- 能展示/选择/搜索后端已发现的 skills。
- 能让宿主替换 skills 状态栏或入口。
- 能正确渲染 skill 相关 tool calls。
- 不把 skills 接入写成 BA 专属 socket event。

## 修改文件入口

常用入口：

- `web/packages/agent-kit/src/react/components/chat/ChatView.tsx`
- `web/packages/agent-kit/src/react/components/chat/MessageList.tsx`
- `web/packages/agent-kit/src/react/components/chat/AssistantTurnBlock.tsx`
- `web/packages/agent-kit/src/react/components/chat/ToolCallBlock.tsx`
- `web/packages/agent-kit/src/react/components/chat/ChatInput.tsx`
- `web/packages/agent-kit/src/react/components/chat/SkillStatusBar.tsx`
- `web/packages/agent-kit/src/react/components/chat/index.ts`
- `web/packages/agent-kit/src/react/index.ts`
- `web/packages/agent-kit/README.md`

导出新能力时，同时检查子包入口：

- `@blade-hq/agent-kit/chat`：`src/react/components/chat/index.ts`
- `@blade-hq/agent-kit/react`：`src/react/index.ts`
- `package.json` exports 是否已覆盖对应入口

## 验证

前端 SDK 改动至少运行：

```bash
cd web && pnpm typecheck
cd web && pnpm --filter @blade-hq/agent-kit test
```

如果改了样式、组件结构或用户可见 UI，再运行：

```bash
cd web && pnpm lint
```

如果改动影响 app 使用方式，还要搜索所有 `ChatView` 调用点，确认旧 props 兼容：

```bash
rg -n "ChatView|MessageList|ChatInput|SkillStatusBar" web/apps web/packages/agent-kit/src -S
```

# Vue Chat 示例

基于 `@blade-hq/agent-kit/client` 的 Vue 3 自渲染聊天界面，演示：

- 流式对话（实时显示文本、思考过程）
- 工具调用渲染（参数、结果、状态徽章）
- AskUserQuestion 交互（选项选择 + 自定义输入 + 提交回答）
- 子智能体渲染（折叠/展开子 turn）

## 启动

```bash
cd examples/vue-chat
pnpm install

# 在 .env 中配置 token
echo "VITE_BLADE_AGENT_TOKEN=sk-blade-v2-xxx" > .env

pnpm dev
```

默认端口 5930，Vite 代理 `/api` 和 `/socket.io` 到 `http://127.0.0.1:8020`。

## 文件结构

```
src/
├── App.vue                      # 入口：创建 BladeClient 和会话
├── composables/
│   └── useBladeChat.ts          # 核心 composable：socket 事件 → 响应式 turns
└── components/
    ├── ChatPanel.vue            # 消息列表 + 输入框
    ├── MessageCard.vue          # 单条 turn：文本 + 思考 + 工具调用分发
    ├── ToolCallCard.vue         # 普通工具调用卡片
    ├── AskUserQuestion.vue      # 用户问答交互表单
    ├── AgentLoop.vue            # 子智能体折叠面板
    └── utils.ts                 # extractText / prettyJson / 状态映射
```

## 核心模式

### 自渲染数据流

```
BladeClient.socket()
  → turn:start    → upsertTurn()  （新 turn 出现）
  → turn:patch    → upsertTurn()  （流式更新：文本、工具状态）
  → turn:end      → upsertTurn()  （turn 最终状态）
  → chat:end      → getSessionTurns() 刷新（保证数据完整）
```

### 回答 AskUserQuestion

```ts
socket.emit("chat:send", {
  session_id,
  message: "用户的回答如下：\n- 问题 -> 选项",
  askuser_answer: {
    tool_call_id: "tc_xxx",
    selections: { 0: [1] },
    custom: {},
  },
})
```

普通业务消息显式传 `mode: "executing"`。回答已有 AskUserQuestion 时不要强制传 `mode`，让回答沿用当前会话/turn 模式；只做方案、不执行工具时才传 `mode: "planning"`。

### 子智能体

子 turn 的 `parent_fork_tool_call_id` 指向父 turn 的 Agent 工具调用 ID，用它过滤和嵌套渲染。

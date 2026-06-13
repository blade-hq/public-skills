# 工作模式

Blade Agent 每次 `chat:send` 都在一个模式下运行。

## 规划模式 vs 干活模式

| 模式 | 字段值 | 行为 |
| --- | --- | --- |
| 规划模式 | `planning` | 拆需求、列计划、评审方案，不执行工具或修改文件 |
| 干活模式 | `executing` | 调用工具、读写文件、运行命令、完成业务动作 |

## 何时用哪种

**用 `executing`：**
- 后端代用户发起任务，希望直接完成
- 前端"发送/执行/分析"按钮，点击后立即干活
- 已上传文件到工作区，希望 Agent 读取处理
- Headless 结构化输出

**用 `planning`：**
- 用户要求"先给方案，不要执行"
- 产品需要审批计划，用户确认后再执行
- 把需求拆成两步：先规划再执行

## SDK 中切换模式

### Node.js / 前端

```ts
// 干活模式
socket.emit("chat:send", {
  session_id: sessionId,
  message: "请读取 data.csv，统计各渠道收入",
  mode: "executing",
})

// 规划模式
socket.emit("chat:send", {
  session_id: sessionId,
  message: "先给数据分析方案，不要读取或修改文件",
  mode: "planning",
})

// 用户确认后，再执行
socket.emit("chat:send", {
  session_id: sessionId,
  message: "按刚才方案执行",
  mode: "executing",
})
```

### Python

```python
async for event in client.chat(
    session_id,
    message="请读取报告并提取风险点",
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.status)
```

Headless 场景强制干活模式：

```python
async for event in client.chat(
    session_id,
    message="请读取 report.md 并返回结构化结果",
    headless=True,
    output_schema=schema,
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.result)
```

### Solution 默认模式

在 `roles/<biz_role_id>/role.yaml` 中设置角色默认模式：

```yaml
initial_mode: executing
```

面向终端用户的业务角色推荐 `executing`，面向方案评审的角色才用 `planning`。

## 自渲染注意事项

收到以下 content block 时不要当正文渲染，它们是模式状态事件：

- `mode_change` - 模式切换，content 包含 `{ from, to }`
- `planning_enter` - 进入规划
- `planning_exit` - 退出规划
- `plan_status` - 规划状态

聊天正文仍取 `type === "text"` 的 block。

## 常见问题

| 问题 | 原因 |
| --- | --- |
| 只发消息但 Agent 不执行工具 | 检查是否传了 `mode: "planning"` 或角色默认 `initial_mode` 是 `planning` |
| 上传文件后 Agent 没读取 | 发送时显式传 `mode: "executing"`，消息写清文件名 |
| 自研 UI 显示很多模式事件 | 过滤 `mode_change`、`planning_enter` 等 block |

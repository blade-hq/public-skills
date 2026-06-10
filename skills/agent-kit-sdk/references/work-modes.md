# 会话模式：规划模式与干活模式

Blade Agent 每次 `chat:send` 都在一个会话模式下运行。公开 SDK 只使用两个模式值：

| 模式 | 英文字段值 | 适用场景 |
| --- | --- | --- |
| 规划模式 | `planning` | 先拆需求、列计划、评审方案，不直接改文件或执行业务动作 |
| 干活模式 | `executing` | 直接调用工具、读写文件、运行命令、处理上传文件、完成业务动作 |

开发 AI 应用时，默认把真实业务请求发到 **干活模式**。例如：读取用户上传的合同、分析表格、生成报告、调用 session skill、写入工作区文件，都应显式传 `mode: "executing"`。

## 什么时候显式传 `executing`

- 后端 SDK 代用户发起一次任务，希望 Agent 直接完成。
- 前端有“发送 / 执行 / 分析 / 生成”按钮，点击后要立即干活。
- 已上传文件到 session workspace，希望 Agent 读取并处理。
- 使用 headless 结构化输出，希望一次返回最终结果。
- 使用较弱 coding agent 或较小模型生成集成代码时，建议示例里始终写出 `mode: "executing"`，不要依赖默认值。

## 什么时候用 `planning`

- 用户要求“先给方案，不要执行”。
- 产品需要审批计划，再由用户确认后执行。
- 开发者想把同一需求拆成两步：先 `planning` 生成计划，再 `executing` 执行计划。

## Node.js Socket.IO

```ts
socket.emit("chat:send", {
  session_id: sessionId,
  message: "请读取刚上传的 data.csv，统计各渠道收入并生成结论",
  mode: "executing",
})
```

先规划、用户确认后再执行：

```ts
socket.emit("chat:send", {
  session_id: sessionId,
  message: "先给数据分析方案，不要读取或修改文件",
  mode: "planning",
})

socket.emit("chat:send", {
  session_id: sessionId,
  message: "按刚才方案执行",
  mode: "executing",
})
```

## Python SDK

`client.chat(...)` 的额外参数会透传到 `chat:send`。干活模式写法：

```python
async for event in client.chat(
    session_id,
    message="请读取刚上传的 report.md，提取标题、摘要和风险点",
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.status)
```

Headless 场景底层也是 `chat:send`。如果需要强制干活模式，可以直接用 `client.chat(..., headless=True, output_schema=..., mode="executing")`：

```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "risk_count": {"type": "integer"},
    },
    "required": ["title", "risk_count"],
}

async for event in client.chat(
    session_id,
    message="请读取刚上传的 report.md，并调用 submit_result 返回结构化结果",
    headless=True,
    output_schema=schema,
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.result)
```

## 自研前端渲染

收到这些 content block 时，不要当普通助手正文渲染：

- `mode_change`
- `planning_enter`
- `planning_exit`
- `plan_status`

它们是模式和计划状态事件。聊天正文仍然取 `type === "text"` 的 block。

## Solution / BizRole 默认模式

如果你在做 Solution 包，而不是普通 SDK 集成，可以在 `roles/<biz_role_id>/role.yaml` 里设置角色默认模式：

```yaml
initial_mode: executing
```

面向最终用户直接完成任务的业务角色，推荐用 `executing`。面向方案评审、需求拆解、设计审核的角色，才用 `planning`。

## 常见错误

- **只发消息但 Agent 不执行工具**：检查是否传了 `mode: "planning"`，或角色默认 `initial_mode` 是否是 `planning`。
- **上传文件后 Agent 没读取文件**：发送处理请求时显式传 `mode: "executing"`，并在消息里写清文件名或路径。
- **自研 UI 显示很多模式事件**：过滤 `mode_change`、`planning_enter`、`planning_exit`、`plan_status` 这类 block。
- **模型容易误解模式**：示例代码里固定写 `mode: "executing"`，比只在自然语言里说“请执行”更稳定。

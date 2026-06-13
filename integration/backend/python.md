# Python 后端接入

## 安装

```bash
pip install blade-agent-kit
# 或
uv add blade-agent-kit
```

import 名是 `blade_agent_kit`。客户端是异步的，所有网络方法都需要 `await`。

## 创建 Client

```python
from blade_agent_kit import BladeAgentClient

async with BladeAgentClient(
    "http://127.0.0.1:8020",          # 后端 origin
    token="sk-blade-v2-...",          # 不传则读环境变量 BLADE_AGENT_TOKEN
) as client:
    print(await client.health())
```

## 创建会话

```python
created = await client.create_session(intent="用户任务")
session_id = created.id  # 注意：Python 用 .id，不是 session_id
```

## 流式对话

`client.chat(...)` 返回异步事件迭代器，事件类型有 `TurnStart`、`TurnPatch`、`TurnEnd`、`ChatEnd`、`SystemError`，用 `event.kind` 区分：

```python
def extract_text(blocks) -> str:
    if not isinstance(blocks, list):
        return ""
    return "".join(
        b.get("content", "")
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    )

final_reply = ""
async for event in client.chat(
    session_id,
    message="用一句话介绍你自己",
    mode="executing",
):
    if event.kind == "turn:end" and event.raw.get("role") == "assistant":
        text = extract_text(event.raw.get("blocks"))
        if text:
            final_reply = text
    elif event.kind == "chat:end":
        print("done:", event.status)  # completed / failed

print(final_reply)
```

事件类型可显式导入：

```python
from blade_agent_kit import TurnStart, TurnPatch, TurnEnd, ChatEnd, SystemError
```

## Headless 一次性问答

```python
# 纯文本
reply = await client.headless.run("用一句话介绍你自己")  # str

# 结构化结果
data = await client.headless.run(
    "提取公司名和金额：...",
    schema={
        "type": "object",
        "properties": {"company": {"type": "string"}, "amount": {"type": "number"}},
        "required": ["company", "amount"],
    },
)  # dict
```

`headless.run(prompt, *, schema=None, model=None, timeout_secs=300.0)`

`schema` 也可以传一个有 `model_json_schema()` 方法的 Pydantic 模型类。

如果 headless 任务需要读取工作区文件，用底层 `client.chat` 替代：

```python
schema = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
}

async for event in client.chat(
    session_id,
    message="请读取工作区里的 report.md，并返回摘要",
    headless=True,
    output_schema=schema,
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.result)
```

## 会话管理（REST）

```python
sessions = await client.list_sessions()
detail = await client.get_session(session_id)
history = await client.get_history(session_id)
files = await client.list_dir(session_id, ".")  # 工作区目录
checkpoints = await client.get_checkpoints(session_id)
await client.delete_session(session_id)
```

其他操作：`client.subscribe(session_id)` 单独订阅，`await client.stop(session_id)` 中途打断。

## 选 Headless 还是流式？

| 场景 | 方式 |
| --- | --- |
| 只要最终结果（问答、抽取、批处理） | Headless |
| 要展示中间过程、工具调用、逐字输出 | 流式 `client.chat()` |
| UI 交给浏览器，后端只做编排 | 后端 Headless，前端 `@blade-hq/agent-kit` |

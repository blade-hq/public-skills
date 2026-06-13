# 文件上传

将普通业务文件（Markdown、CSV、PDF 等）上传到 Session Workspace，让智能体读取分析。

::: tip
普通文件上传和[会话技能上传](../capabilities/session-skill.md)不同。业务文件用本页方法，工具包用 `client.skills.uploadSessionSkill()`。
:::

## Python SDK

```python
from pathlib import Path

created = await client.create_session(intent="文档分析")
session_id = created.id

result = await client.upload_file(
    session_id,
    Path("q2-launch-notes.md"),
    dir_path=".",                    # 目标目录，默认根目录
    remote_path="q2-launch-notes.md", # 可选，默认用本地文件名
)

if result.get("failed"):
    raise RuntimeError(f"上传失败: {result['failed']}")
```

参数说明：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | str | 目标会话 ID |
| `file_path` | str / Path | 本地文件路径 |
| `dir_path` | str | 工作区目标目录，默认 `"."` |
| `remote_path` | str / None | 上传后的文件名，默认用本地文件名 |

上传到子目录：

```python
await client.upload_file(session_id, "local/report.md", dir_path="uploads", remote_path="report.md")
# Agent 可读取 uploads/report.md
```

## Node.js SDK

```ts
import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL!,
  token: process.env.BLADE_AGENT_TOKEN!,
})

const { session_id } = await client.sessions.createSession("文档分析")

const result = await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([await readFile("report.md")], "report.md"), name: "report.md" },
])

if (result.failed?.length) {
  throw new Error(`上传失败: ${JSON.stringify(result.failed)}`)
}
```

::: danger
不要使用 `client.uploadFile(...)` 或 `client.workspaces.uploadFile(...)`，0.5.11 没有这些方法。
:::

## REST 直接上传

```http
POST /api/sessions/{session_id}/upload/{dir_path}
Content-Type: multipart/form-data
Authorization: Bearer sk-blade-v2-...
```

FormData 字段：

| 字段 | 说明 |
| --- | --- |
| `files` | 一个或多个文件 |
| `paths` | 可选，JSON 字符串数组，和 `files` 一一对应 |

不要手动设置 `Content-Type`，让 `fetch` / FormData 自动生成 boundary。

## 智能体读取文件

上传后在消息里写清文件路径，并显式传 `mode: "executing"`：

```ts
socket.emit("chat:send", {
  session_id,
  message: "请读取工作区里的 q2-launch-notes.md，提取标题和风险列表。",
  mode: "executing",
})
```

## 常见问题

| 问题 | 修复 |
| --- | --- |
| Agent 说找不到文件 | 确认上传返回的 `uploaded` 路径，消息中使用相同路径 |
| 上传成功但 Agent 不执行 | 发送时显式传 `mode: "executing"` |
| Node 报 `client.uploadFile is not a function` | 改用 `client.sessions.uploadFiles(session_id, ".", files)` |
| 多文件路径错乱 | `paths` 数组长度和 `files` 数量要一致，顺序也要一致 |
| 鉴权失败 | REST 请求同样需要 `Authorization: Bearer ...` |

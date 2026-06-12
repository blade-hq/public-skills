# Session Workspace 文件上传

本文说明如何把普通业务文件上传到指定 session workspace，例如 Markdown、文本、CSV、PDF 等用户材料。

普通文件上传和 [session-skill-upload.md](session-skill-upload.md) 不是一回事：

- 普通文件上传：把 `report.md`、`data.csv` 这类业务文件放进 session workspace，后续让 Agent 读取和处理。
- Session skill 上传：把 `SKILL.md`、`tools.py` 这类工具包临时安装到某个 session，让 Agent 获得新的业务工具。

如果你的需求是“用户上传一份文档，然后让 Agent 分析它”，用本文的普通文件上传。

## Python SDK

Python SDK 提供 `upload_file()`：

```python
result = await client.upload_file(
    session_id,
    file_path,
    dir_path=".",
    remote_path=None,
)
```

参数：

| 参数 | 说明 |
| --- | --- |
| `session_id` | 目标 Blade session ID |
| `file_path` | 本地文件路径，类型可以是 `str` 或 `Path` |
| `dir_path` | 上传到 session workspace 的目标目录，默认 `"."` |
| `remote_path` | 可选。上传后的相对路径或文件名；不传时使用本地文件名 |

返回值：

```json
{
  "uploaded": ["report.md"],
  "failed": []
}
```

`uploaded` 是成功写入 workspace 的路径列表；`failed` 是失败项列表。只要 `failed` 非空，后端应把失败原因返回给调用方，不要继续假装文件已可读。

最小示例：

```python
from pathlib import Path

created = await client.create_session(intent="文档分析")
session_id = created.id

upload_result = await client.upload_file(
    session_id,
    Path("q2-launch-notes.md"),
    dir_path=".",
    remote_path="q2-launch-notes.md",
)

if upload_result.get("failed"):
    raise RuntimeError(f"文件上传失败: {upload_result['failed']}")

async for event in client.chat(
    session_id,
    message="请读取工作区里的 q2-launch-notes.md，提取标题、owner、category、二级标题和风险列表。",
    mode="executing",
):
    if event.kind == "chat:end":
        print(event.status)
```

上传到子目录：

```python
await client.upload_file(
    session_id,
    "local/report.md",
    dir_path="uploads",
    remote_path="report.md",
)

# Agent 可读取 uploads/report.md
```

## Node.js SDK

Node.js 后端使用 `@blade-hq/agent-kit@0.5.11` 时，普通文件上传优先用 client SDK：

```ts
import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: process.env.BLADE_AGENT_URL!,
  token: process.env.BLADE_AGENT_TOKEN!,
})

const { session_id } = await client.sessions.createSession("文档分析")
const localPath = "q2-launch-notes.md"
const remotePath = basename(localPath)

const result = await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([await readFile(localPath)], remotePath), name: remotePath },
])

if (result.failed?.length) {
  throw new Error(`文件上传失败: ${JSON.stringify(result.failed)}`)
}
```

Express + multer 代理上传：

```ts
import express from "express"
import multer from "multer"
import { BladeClient } from "@blade-hq/agent-kit/client"

const app = express()
const upload = multer({ storage: multer.memoryStorage() })

app.post("/api/upload", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "missing file" })
    }

    const client = new BladeClient({
      baseUrl: process.env.BLADE_AGENT_URL!,
      token: process.env.BLADE_AGENT_TOKEN!,
    })
    const { sessionId, remotePath = req.file.originalname } = req.body

    const result = await client.sessions.uploadFiles(sessionId, ".", [
      {
        file: new File([req.file.buffer], req.file.originalname, {
          type: req.file.mimetype || "application/octet-stream",
        }),
        name: remotePath,
      },
    ])

    if (result.failed?.length) {
      return res.status(502).json({ error: "upload failed", detail: result })
    }
    res.json(result)
  } catch (err) {
    next(err)
  }
})
```

不要使用 `client.uploadFile(...)` 或 `client.workspaces.uploadFile(...)`；0.5.11 的 Node client 没有这些普通文件上传方法。不要从包根导入 SDK；Node 后端必须使用 `@blade-hq/agent-kit/client` 和 `client.sessions.uploadFiles(...)`。

## Node.js / REST

如果不用 SDK 上传，可以直接调用公开 REST 接口：

```http
POST /api/sessions/{session_id}/upload/{dir_path}
Content-Type: multipart/form-data
Authorization: Bearer sk-blade-v2-...
```

不要使用 `/api/v1/sessions/{session_id}/workspace`，也不要把文件内容包装成 JSON `{ files: [...] }` 上传。普通文件上传必须是 multipart。

FormData 字段：

| 字段 | 说明 |
| --- | --- |
| `files` | 一个或多个文件 |
| `paths` | 可选。JSON 字符串数组，和 `files` 一一对应，表示上传后的相对路径 |

Node 18+ 示例：

```ts
import { readFile } from "node:fs/promises"
import { basename } from "node:path"

function encodeWorkspacePath(path: string): string {
  return encodeURIComponent(path || ".")
}

async function uploadWorkspaceFile(options: {
  baseUrl: string
  token: string
  sessionId: string
  localPath: string
  dirPath?: string
  remotePath?: string
}) {
  const dirPath = options.dirPath ?? "."
  const remotePath = options.remotePath ?? basename(options.localPath)
  const bytes = await readFile(options.localPath)

  const form = new FormData()
  form.append("files", new Blob([bytes]), basename(options.localPath))
  form.append("paths", JSON.stringify([remotePath]))

  const response = await fetch(
    `${options.baseUrl.replace(/\/$/, "")}/api/sessions/${options.sessionId}/upload/${encodeWorkspacePath(dirPath)}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${options.token}`,
      },
      body: form,
    },
  )

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`文件上传失败: HTTP ${response.status} ${detail}`)
  }

  const result = await response.json()
  if (Array.isArray(result.failed) && result.failed.length > 0) {
    throw new Error(`文件上传失败: ${JSON.stringify(result.failed)}`)
  }
  return result as { uploaded: string[]; failed: unknown[] }
}
```

Express + multer 直接 REST 代理上传：

```ts
app.post("/api/upload", upload.single("file"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "missing file" })
  }

  const { sessionId, remotePath = req.file.originalname } = req.body
  const form = new FormData()
  form.append("files", new Blob([req.file.buffer]), req.file.originalname)
  form.append("paths", JSON.stringify([remotePath]))

  const upstream = await fetch(
    `${process.env.BLADE_AGENT_URL}/api/sessions/${sessionId}/upload/${encodeURIComponent(".")}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${process.env.BLADE_AGENT_TOKEN}` },
      body: form,
    },
  )

  const body = await upstream.json().catch(() => ({}))
  if (!upstream.ok || body.failed?.length) {
    return res.status(502).json({ error: "upload failed", detail: body })
  }

  res.json({ uploaded: body.uploaded, failed: body.failed })
})
```

不要手动设置 `Content-Type: multipart/form-data`；让 `fetch` / FormData 自动生成 boundary。

## 上传后让 Agent 读取文件

上传成功后，业务消息里写清文件路径，并显式传 `mode: "executing"`：

```ts
socket.emit("chat:send", {
  session_id: sessionId,
  message: "请读取工作区里的 q2-launch-notes.md，提取标题、owner、category、所有二级标题和风险列表。",
  mode: "executing",
})
```

如果上传到子目录，消息中使用相同路径：

```ts
socket.emit("chat:send", {
  session_id: sessionId,
  message: "请读取 uploads/q2-launch-notes.md 并总结风险。",
  mode: "executing",
})
```

## 常见错误

- **Agent 说找不到文件**：确认上传返回的 `uploaded` 路径，并在消息里使用完全相同的 workspace 相对路径。
- **上传成功但 Agent 不执行读取**：发送处理请求时显式传 `mode: "executing"`。
- **把文件上传成 session skill**：普通业务文件不要用 `client.skills.uploadSessionSkill()`；那只适用于上传工具包。
- **Node 报 `client.uploadFile is not a function`**：改用 `client.sessions.uploadFiles(session_id, ".", files)`。
- **Node 报 `client.workspaces` 是 undefined**：0.5.11 普通文件上传不在 `client.workspaces` 下，改用 `client.sessions.uploadFiles(session_id, ".", files)`。
- **多文件上传路径错乱**：`paths` 数组长度和 `files` 数量要一致，顺序也要一致。
- **鉴权失败**：后端上传 REST 请求同样需要 `Authorization: Bearer ...`。

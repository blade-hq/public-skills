# REST 通道

`@blade-hq/agent-client` 对高频操作提供类型化方法；其余接口用通用通道 `client.api` 直接调，路径与请求体对照后端 Swagger（`<后端地址>/docs`）。两者都自动携带鉴权。

## 类型化资源方法

### 会话

```ts
await client.sessions.connect(sessionId)        // 连接会话，返回实时的 AgentSession
await client.sessions.create({ intent: "数据分析" })  // 创建并连接
await client.sessions.createSessionWithRequest({      // 只创建，返回 { session_id }
  intent: "数据分析",
  solution_id: "my-solution",   // 可选：解决方案（一组业务场景的打包）
  biz_role_id: "analyst",       // 可选：业务角色
  model: "gpt-4o",              // 可选：模型
  env: { API_KEY: "..." },      // 可选：会话环境变量
})

await client.sessions.listSessions()
await client.sessions.listSessionsPaginated({ limit: 20, offset: 0, q: "关键词" })
await client.sessions.getSession(sessionId)
await client.sessions.updateSession(sessionId, { intent: "新标题" })
await client.sessions.deleteSession(sessionId)
await client.sessions.getSessionTurns(sessionId)      // 历史消息（与实时收到的结构一致）
await client.sessions.getSessionContextStats(sessionId)
await client.sessions.getSessionTasks(sessionId)
```

### 工作区文件

每个会话有一个专属工作目录，上传的文件放这里，智能体能读写。

```ts
uploadFiles(sessionId, dirPath, files, options?)
```

| 参数 | 说明 |
| --- | --- |
| `dirPath` | 工作目录下的目标子目录。**根目录用 `""` 或 `"."` 都可以**，两者等价；子目录直接写 `"uploads"` |
| `files` | `FileList`（表单 `<input type="file">` 的 `.files` 直接传）、`File[]`，或 `{ file, name }[]`（需要改上传后的文件名时用） |
| `options.onProgress` | 上传进度回调 |

返回 `{ uploaded: string[], failed: string[] }`——**要检查 `failed` 再继续**。

```ts
await client.sessions.listDir(sessionId, "")                       // 列目录
await client.sessions.uploadFiles(sessionId, "", fileInput.files)  // 浏览器表单上传
await client.sessions.uploadFiles(sessionId, "uploads", files, {   // 带进度
  onProgress: (p) => console.log(p.percent),
})
await client.sessions.writeFile(sessionId, "notes.md", "# 内容")
await client.sessions.renameFile(sessionId, "a.md", "b.md")
await client.sessions.deleteFile(sessionId, "notes.md")
client.buildAuthedUrl(`/api/sessions/${sessionId}/files/report.pdf`)  // 带鉴权的下载/预览地址
```

### 让智能体读到上传的文件

上传本身不会通知智能体。**必须在消息里写清路径**，并显式传干活模式：

```ts
const result = await client.sessions.uploadFiles(sessionId, "", fileInput.files)
if (result.failed.length) throw new Error(`上传失败: ${result.failed}`)

// 用返回的 uploaded 路径原样写进消息，否则智能体会说"找不到文件"
await chat.send(`请读取工作区里的 ${result.uploaded[0]}，提取标题和风险列表。`, {
  mode: "executing",
})
```

### 技能

```ts
await client.skills.listSkills()
await client.skills.searchSkills("数据分析", 10)
await client.skills.getSkill("skill-name")
await client.skills.listSessionSkills(sessionId)
await client.skills.uploadSessionSkill(sessionId, payload)  // 把临时技能装进指定会话
await client.skills.resyncSkills(sessionId)
```

### 其他

```ts
await client.auth.getMe()

// 可用模型列表：返回 { default, thinkingAvailable?, models }
const { models, default: defaultModel } = await client.models.getModelsConfig()

await client.headless.run(prompt, { schema })   // 见 node.md
```

## 通用通道：client.api

```ts
const skills = await client.api.get("/api/skills")
const list = await client.api.get("/api/sessions", { query: { limit: 20, offset: 0 } })
const created = await client.api.post("/api/sessions", { intent: "分析报表" })
await client.api.put("/api/user-preferences", { theme: "dark" })
await client.api.patch(`/api/sessions/${id}/pin`, { pinned: true })
await client.api.del(`/api/sessions/${id}`)

// 需要原始 Response（下载文件、读响应头）时
const resp = await client.api.raw(`/api/sessions/${id}/files/a.png`)
const blob = await resp.blob()
```

泛型标注返回类型：`await client.api.get<Skill[]>("/api/skills")`。

## 错误处理

请求失败抛出 `BladeApiError`，带 `status` 和后端返回的 detail；401/403 的报错信息里会附上"该怎么办"的指引。

```ts
import { BladeApiError } from "@blade-hq/agent-client"

try {
  await client.api.get("/api/skills")
} catch (error) {
  if (error instanceof BladeApiError && error.status === 401) {
    await client.auth.login()   // 浏览器：重新登录
  }
  throw error
}
```

::: warning 不要绕过 SDK 用裸 fetch
裸 `fetch` 不会携带 SDK 管理的令牌，跨域场景也拿不到 cookie，容易出现 401/403。所有后端调用统一走 `client.api` 或类型化方法。
:::

# 指定解决方案与角色

创建会话时，可以指定 Solution（解决方案）和 BizRole（业务角色），让智能体使用特定的技能集和行为配置。

## 创建会话时指定

### Node.js

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({ baseUrl, token })

const { session_id } = await client.sessions.createSession("用户任务", {
  solution_id: "my-solution",
  biz_role_id: "analyst",
})
```

### Python

```python
created = await client.create_session(
    intent="用户任务",
    solution_id="my-solution",
    biz_role_id="analyst",
)
session_id = created.id
```

## Solution 与 BizRole 的关系

- **Solution**：一组业务场景的打包，包含角色定义、技能配置、初始化脚本等
- **BizRole**：Solution 下的一个角色，定义了该角色的提示词、默认模式、可用技能

一个 Solution 可以包含多个 BizRole，每个 BizRole 有自己的 `role.yaml` 配置：

```yaml
# roles/<biz_role_id>/role.yaml
initial_mode: executing
```

## 内置 Solution

平台预置了以下 Solution，创建会话时可以直接使用对应的 `solution_id`：

| solution_id | 说明 |
|-------------|------|
| `skill_editor` | 技能编辑器，提供技能开发与调试环境 |
| `software_factory` | 软件工程工作台，支持需求拆分、PRD、UI 设计、技术设计到任务分工的完整流程 |

示例——创建技能编辑器会话：

```ts
const { session_id } = await client.sessions.createSession("技能编辑", {
  solution_id: "skill_editor",
})
```

## 注意事项

- `solution_id` 和 `biz_role_id` 在创建会话时指定，创建后不可更改
- 切换角色需要创建新的 Session
- 不指定时使用系统默认的 Solution 和角色
- 查看当前会话的 Solution 和角色信息：

```ts
const detail = await client.sessions.getSession(session_id)
```

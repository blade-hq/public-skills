# 会话技能上传

会话技能（Session Skill）是临时上传到某个 Session 的工具包，让智能体在该会话中获得额外的业务能力。

## 什么是会话技能

- 不走 Skill Registry，不是全局安装
- 上传后只属于当前 Session
- 通常包含 `SKILL.md`（工具说明）和 `tools.py`（Python 工具函数）

::: tip
如果只是上传 Markdown、CSV 等业务文件让 Agent 读取分析，请使用[文件上传](../backend/file-upload.md)，不要用 Session Skill 接口。
:::

## 上传

```ts
await client.skills.uploadSessionSkill(sessionId, {
  name: "demo/map-highlight",
  files: [
    { path: "SKILL.md", content: skillMarkdown },
    { path: "tools.py", content: toolsPython },
  ],
})
```

约束：
- `name` 必须符合 `org/skill-name` 格式
- `files` 必须包含 `SKILL.md`
- 文件路径必须是相对路径，不能包含 `..`

## 管理

```ts
// 列出当前会话的所有 skill
const skills = await client.skills.listSessionSkills(sessionId)

// 查看 skill 加载状态
const stats = await client.skills.getSkillStats(sessionId)
```

## SKILL.md 示例

```markdown
---
name: 地图城市高亮
description: 通过宿主地图高亮指定城市
---

# 地图城市高亮

当用户希望在地图上高亮某些城市时，调用 `highlight_cities` 工具，传入城市 id 列表。
```

## tools.py 示例

```python
from __future__ import annotations
import json
from langchain_core.tools import tool

@tool
def highlight_cities(city_ids: list[str]) -> str:
    """在宿主地图上高亮指定城市。

    Args:
        city_ids: 城市 id 列表，如 ["hangzhou", "ningbo"]
    """
    return json.dumps(
        {
            "ok": True,
            "highlighted": city_ids,
            "_meta": {
                "bridge": {
                    "action": "map.highlight",
                    "payload": {"cityIds": city_ids},
                },
                "ui": {
                    "resourceHTML": f"<html><body><p>已高亮：{'、'.join(city_ids)}</p></body></html>",
                    "target": "inline",
                    "height": 320,
                    "title": "地图高亮预览",
                },
            },
        },
        ensure_ascii=False,
    )
```

## 工具返回前端数据

工具返回 JSON 时可包含 `_meta`（不给模型读，给前端处理）：

| 字段 | 用途 |
| --- | --- |
| `_meta.bridge` | 驱动宿主页面动作（如地图高亮） |
| `_meta.ui` | 在 ChatView 中渲染 iframe 卡片 |

两者可同时使用。

## 删除

Session 结束后技能自动清理。如需手动管理，通过 `listSessionSkills` 检查状态。

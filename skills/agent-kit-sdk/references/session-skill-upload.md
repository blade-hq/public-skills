# Session Skill 上传

本文说明如何把一组 skill 文件临时上传到指定 session，让 Agent 在这个 session 中调用宿主提供的业务能力。

如果你只是要上传 Markdown、文本、CSV、PDF 等普通业务文件，让 Agent 读取分析，请读 [file-upload.md](file-upload.md)。不要用 session skill 上传普通业务文件。

它不走 skill registry，也不是全局安装。上传后的 skill 只属于当前 session。

上传的 session skill 通常包含：

- `SKILL.md`：告诉模型工具能做什么。
- `tools.py`：Python 工具函数。

前端只负责把这些文件上传到指定 session。Agent 后续在这个 session 的运行环境里发现并调用这些工具。

## 上传 session skill

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

- `name` 必须符合 `org/skill-name` 格式。
- `files` 必须包含 `SKILL.md`。
- 文件路径必须是相对路径，不能包含 `..`。
- 上传后可用 `client.skills.listSessionSkills(sessionId)` 或 `client.skills.getSkillStats(sessionId)` 验证。

## SKILL.md 示例

```markdown
---
name: 地图城市高亮
description: 通过宿主地图高亮指定城市，并在对话中展示 mini-map 卡片
---

# 地图城市高亮

当用户希望在地图上高亮某些城市时，调用 `highlight_cities` 工具，传入城市 id 列表。

## 宿主已知 id

hangzhou, ningbo, wenzhou, shaoxing
```

## tools.py 示例

```python
from __future__ import annotations

import json

from langchain_core.tools import tool


def make_map_card(city_ids: list[str]) -> str:
    city_text = "、".join(city_ids)
    return f"""<!doctype html>
<html>
  <body style="font-family: sans-serif; padding: 12px">
    <h3>已高亮城市</h3>
    <p>{city_text}</p>
  </body>
</html>"""


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
                    "resourceHTML": make_map_card(city_ids),
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

工具返回 JSON 字符串时，可以包含 `_meta`。`_meta` 不给模型读，主要给 Blade Agent 前端处理。

- `_meta.bridge`：让宿主页面执行一个动作，例如地图高亮、打开 CRM 记录。
- `_meta.ui`：让 ChatView 渲染一张卡片或右侧预览。

### 只触发宿主页面动作

例如工具查出城市后，希望外部地图高亮这些城市，但聊天区不需要额外卡片：

```python
html = """<!doctype html>
<html>
  <body style="font-family: sans-serif; padding: 12px">
    <h3>已高亮城市</h3>
    <p>hangzhou、ningbo</p>
  </body>
</html>"""

return json.dumps(
    {
        "ok": True,
        "city_ids": ["hangzhou", "ningbo"],
        "_meta": {
            "bridge": {
                "action": "map.highlight",
                "payload": {
                    "cityIds": ["hangzhou", "ningbo"],
                    "reason": "用户要求高亮已选城市",
                },
            }
        },
    },
    ensure_ascii=False,
)
```

React 宿主可以从 `useGisStore` 消费 `map.highlight`，原生 iframe 宿主可以监听 `postMessage`。

### 只渲染 ChatView 卡片

例如工具生成一张图表，只需要在聊天区展示，不需要驱动宿主页面：

```python
return json.dumps(
    {
        "ok": True,
        "_meta": {
            "ui": {
                "resourceHTML": "<!doctype html><html><body><div id='chart'>...</div></body></html>",
                "target": "inline",
                "height": 360,
                "title": "销售趋势",
            }
        },
    },
    ensure_ascii=False,
)
```

`resourceHTML` 必须是完整 HTML 文档。已有线上页面时也可以用 `resourceUri`：

```python
"_meta": {
    "ui": {
        "resourceUri": "https://partner.example.com/orders/O-1001?embed=1",
        "target": "preview",
        "height": 720,
        "title": "订单详情",
    }
}
```

### 同时触发动作和渲染卡片

地图类工具通常两者都要：外部大地图高亮城市，同时聊天区展示一张小地图卡片。

```python
return json.dumps(
    {
        "ok": True,
        "highlighted": ["hangzhou", "ningbo"],
        "_meta": {
            "bridge": {
                "action": "map.highlight",
                "payload": {"cityIds": ["hangzhou", "ningbo"]},
            },
            "ui": {
                "resourceHTML": html,
                "target": "inline",
                "height": 320,
                "title": "地图高亮预览",
            },
        },
    },
    ensure_ascii=False,
)
```

这时前端会做两件事：

1. 把 `map.highlight` 分发给宿主页面。
2. 在 ChatView 里渲染 `resourceHTML` 对应的卡片。

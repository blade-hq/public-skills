# 页面协作（地图联动等）

页面协作解决两个方向的联动：

- **智能体 → 页面**：智能体干活时让你的页面做出反应（高亮地图、打开面板、刷新表格）。
- **页面 → 智能体**：用户在页面上的操作（选中点位、勾选表格行）作为上下文交给智能体。

## 指令是怎么来的（必读）

智能体 → 页面的每条指令带一个 **action 字符串**（如 `"map.highlight"`）。它的来源必须先搞清楚，否则会误以为是 SDK 内置的固定列表：

> **action 是技能作者在工具代码的返回值里写的。**

技能（Skill）是智能体可调用的一组业务工具。技能工具返回的 JSON 里如果带 `_meta.bridge: { action, payload }` 字段，后端会把这段数据从对话历史里摘出来（大模型看不到它），单独送到前端页面。

（`bridge` 只是这个字段的名字，你不用理解它的由来，照抄即可。）

因此：

- action 是**技能作者与页面开发者之间约定的暗号**，起名完全自由，两边写同一个字符串即可；
- **大模型不参与**：它只决定"调不调这个工具、传什么参数"，指令本身写死在工具代码里；
- **SDK 不做枚举**：SDK 只负责原样传递，不限制也不校验 action 取值。

## 完整闭环示例：GIS 地图协作

### 第 1 步：技能侧（技能作者写的 Python 工具）

```python
# skills/map-tools/tools.py

def highlight_cities(city_ids: list[str]) -> dict:
    """在地图上高亮指定城市"""
    return {
        "ok": True,
        "message": f"已高亮 {len(city_ids)} 座城市",
        # _meta.bridge 会被后端剥离并送达前端页面，不进入大模型上下文
        "_meta": {
            "bridge": {
                "action": "map.highlight",            # 与页面开发者约定的暗号
                "payload": {"cityIds": city_ids},     # 任意可 JSON 序列化的数据
            }
        },
    }


def fly_to(lng: float, lat: float, zoom: int = 12) -> dict:
    """把地图视角移动到指定坐标"""
    return {
        "ok": True,
        "message": f"已定位到 ({lng}, {lat})",
        "_meta": {
            "bridge": {
                "action": "map.flyTo",
                "payload": {"lng": lng, "lat": lat, "zoom": zoom},
            }
        },
    }
```

### 第 2 步：页面侧（宿主页面开发者写的前端代码）

action 字符串与技能侧完全一致：

::: code-group

```ts [任意框架 / Vue]
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({ baseUrl: "https://blade.example.com" })
const chat = await client.sessions.connect(sessionId)

chat.onCommand("map.highlight", (payload) => {
  const { cityIds } = payload as { cityIds: string[] }
  map.highlight(cityIds)
})

chat.onCommand("map.flyTo", (payload) => {
  const { lng, lat, zoom } = payload as { lng: number; lat: number; zoom: number }
  map.flyTo([lng, lat], zoom)
})
```

```tsx [React（ChatView）]
import { ChatView } from "@blade-hq/agent-react"

// payload 是 unknown，用前先断言
const commands = {
  "map.highlight": (payload: unknown) => {
    const { cityIds } = payload as { cityIds: string[] }
    map.highlight(cityIds)
  },
  "map.flyTo": (payload: unknown) => {
    const { lng, lat, zoom } = payload as { lng: number; lat: number; zoom: number }
    map.flyTo([lng, lat], zoom)
  },
}

<ChatView sessionId={sessionId} commands={commands} />
```

```tsx [React（hooks）]
import { useEffect } from "react"
import { useAgentSession } from "@blade-hq/agent-react"

// hooks 必须写在组件内部，写在模块顶层 React 会直接报 Invalid hook call
function MapPanel({ sessionId }: { sessionId: string }) {
  const { session } = useAgentSession(sessionId)

  useEffect(() => {
    return session?.onCommand("map.highlight", (payload) => {
      const { cityIds } = payload as { cityIds: string[] }
      map.highlight(cityIds)
    })
  }, [session])

  return <MapCanvas />
}
```

:::

::: warning payload 是 unknown
`payload` 来自技能工具的返回值，SDK 不知道也不校验它的结构，类型是 `unknown`——TypeScript 严格模式下直接取字段会报错。用之前要么类型断言（相信技能作者按约定返回），要么做运行时校验（更安全，毕竟数据最终源自技能代码）。

两种 handler 签名有差异，别记混：

- `session.onCommand(action, (payload, meta) => ...)` —— 第二个参数 `meta` 带 `toolCallId`
- `ChatView` 的 `commands` 属性里，handler 是 `(payload) => ...` —— **只有 `payload`，没有 `meta`**
:::

### 第 3 步：用户选点 → 交给智能体

```ts
map.on("click", (e) => {
  // 把点位作为附件放进聊天输入框
  chat.attach("选中点位", { lng: e.lngLat.lng, lat: e.lngLat.lat })
  // 再往输入框追加一句提示语（不发送，用户可以改完再发）
  chat.insertText("请分析这个点位周边的商业情况")
})
```

用户点发送 → 智能体调用技能工具查数据 → 工具返回 `_meta.bridge` → 页面收到 `map.highlight` 指令完成高亮。闭环完成。

## 页面 → 智能体的三个方法

```ts
chat.attach("选中点位", { lng: 116.4, lat: 39.9 })  // 变成输入框里的附件，随下一条消息发出
chat.insertText("请分析这个区域")                    // 往输入框追加文字（不发送）
await chat.send("这里适合开店吗？")                  // 跳过输入框，直接代用户发送
```

`attach` 和 `insertText` 需要渲染层配合才有可见效果：React 的 `ChatView` 内置支持；完全自建 UI 时监听 `attachRequested` / `insertTextRequested` 事件自行渲染，或者干脆直接用 `send()`。

## onCommand 的可靠性

- **注册前缓冲**：指令先于 `onCommand` 注册到达时（比如页面还在加载历史），会被缓冲，注册后立刻补发——不存在"注册晚了漏消息"。
- **自动去重**：同一次工具调用产生的指令只投递一次，断线重连补数不会重复触发。
- `onCommand` 返回取消函数，组件卸载时调用即可。

需要拿到底层信息（如工具调用 ID）或统一分发时，也可以监听原始事件：

```ts
chat.on("command", ({ action, payload, toolCallId }) => { ... })
```

## 相关：工具可视化预览

技能工具返回 `_meta.ui` 时，`ChatView` 会把它渲染成消息里的卡片：

```json
{
  "_meta": {
    "ui": {
      "resourceHTML": "<!doctype html><html>...</html>",
      "target": "inline",
      "height": 320,
      "title": "地图高亮预览"
    }
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `resourceHTML` | 完整 HTML 文档，用 iframe `srcdoc` 渲染 |
| `resourceUri` | 外部 URL，用 iframe `src` 渲染 |
| `target` | `inline`（消息内嵌）或 `preview`（侧边预览） |
| `height` | iframe 高度（px） |
| `title` | 卡片标题 |

::: warning toolPreview 事件只对 target: "preview" 触发
`chat.on("toolPreview", ...)` 和 `<ChatView onPreview={...}>` **只在 `target` 为 `"preview"` 时触发**，`target: "inline"` 不会走这个事件。

- `target: "preview"` → 监听 `toolPreview` 事件，把内容渲染到你的侧边预览区
- `target: "inline"` → `ChatView` 内置渲染成消息里的卡片；**自建 UI 需要自己从 `message.blocks` 里找 `type === "tool_ui"` 的块**来渲染
:::

::: tip 两套独立机制
`_meta.ui` 负责**渲染内容**，`_meta.bridge` 负责**驱动页面行为**，互不影响，可以同时用。
:::

## iframe 嵌入形态

如果你不是嵌组件，而是把 Blade 聊天页整个用 iframe 嵌进系统，宿主这边的协作用法完全一样，见 [iframe 嵌入](./embedded.md)。

## 常见问题

| 现象 | 原因与解法 |
| --- | --- |
| `onCommand` 收不到指令 | action 拼写与技能工具返回的 `_meta.bridge.action` 不一致；或技能根本没返回 `_meta.bridge` |
| 指令收到了但页面没反应 | 处理函数里报错被吞了（SDK 只告警不中断），看浏览器控制台 |
| `attach` 没在输入框里出现 | 自建 UI 没监听 `attachRequested` 事件；改用 `send()` 或补上渲染 |

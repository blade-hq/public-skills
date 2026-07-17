# 页面协作：智能体与宿主页面互相驱动

页面协作解决两个方向的联动：

- **智能体 → 页面**：智能体执行技能工具时，让宿主页面做出反应（高亮地图、打开面板、刷新表格）。
- **页面 → 智能体**：用户在页面上的操作（选中点位、勾选行）作为上下文交给智能体。

## action 从哪里来（必读）

智能体 → 页面的每条指令有一个 `action` 字符串（如 `"map.highlight"`）。它的来源必须搞清楚：

**action 是技能作者在工具实现的返回值 JSON 里写的**。技能工具返回 `_meta.bridge: { action, payload }` 字段时，后端会把这段数据从工具结果里摘出来（大模型看不到它），单独送到前端页面。（`bridge` 只是这个字段的名字，你不用理解它的由来，照抄即可。）

也就是说：

- action 是**技能作者与宿主页面开发者之间的业务契约**——两边约定同一个字符串即可，起名完全自由；
- **模型（LLM）不参与**：它只决定"调不调这个工具、传什么参数"，指令本身是工具代码写死的；
- **SDK 不做枚举**：SDK 只负责原样传递，不限制也不校验 action 取值。

## 两侧代码并排

技能侧（技能作者，Python 工具实现）：

```python
# skills/map-tools/tools.py
def highlight_cities(city_ids: list[str]) -> dict:
    """在地图上高亮指定城市"""
    return {
        "ok": True,
        "message": f"已高亮 {len(city_ids)} 座城市",
        # _meta.bridge 会被后端剥离并送达前端页面，不进入模型上下文
        "_meta": {
            "bridge": {
                "action": "map.highlight",           # 与页面开发者约定的契约字符串
                "payload": {"cityIds": city_ids},    # 任意可 JSON 序列化的数据
            }
        },
    }
```

页面侧（宿主页面开发者，任意框架）：

```ts
const chat = await client.sessions.connect(sessionId)

// action 字符串与技能侧完全一致
chat.onCommand("map.highlight", (payload) => {
  // payload 类型是 unknown：它来自技能工具的返回值，SDK 不知道也不校验它的结构。
  // 用之前必须自行断言（信任技能作者）或做运行时校验（更安全）。
  const { cityIds } = payload as { cityIds: string[] }
  map.highlight(cityIds)
})
```

`onCommand` 的 handler 签名是 `(payload: unknown, meta: { toolCallId?: string }) => void`。第二个参数 `meta` 带工具调用 ID，需要时可用。

::: 关于 payload 的类型与安全
`payload` 是 `unknown`，TypeScript 严格模式下直接取字段会报错。两种处理方式：

```ts
// 简单场景：类型断言（相信技能作者按约定返回）
const { cityIds } = payload as { cityIds: string[] }

// 严谨场景：运行时校验后再用（payload 最终源自技能工具，值得防一手）
if (!isStringArray((payload as any)?.cityIds)) return
```
:::

`onCommand` 的可靠性保障：

- **注册前缓冲**：指令先于 `onCommand` 注册到达时（比如历史加载阶段），会被缓冲，注册后立刻补发；
- **去重**：同一次工具调用产生的指令只投递一次，重连补数不会重复触发；
- 返回取消函数，组件卸载时调用即可。

需要拿到底层信息（如 toolCallId）或统一分发时，也可以监听原始事件：

```ts
chat.on("command", ({ action, payload, toolCallId }) => { ... })
```

## 页面 → 智能体

```ts
// 把业务数据作为附件放进聊天输入框，随用户下一条消息一起发给智能体
chat.attach("选中点位", { lng: 116.4, lat: 39.9 })

// 往输入框追加一段文字（不发送，用户可编辑后再发）
chat.insertText("请分析这个区域")

// 也可以跳过输入框直接代用户发送
await chat.send("分析坐标 (116.4, 39.9) 周边的门店分布")
```

`attach` / `insertText` 需要渲染层配合展示：React 的 `ChatView` 内置支持；完全自建 UI 时监听 `attachRequested` / `insertTextRequested` 事件自行渲染，或直接用 `send()`。

## 完整闭环示例（GIS 地图）

1. 页面初始化时注册指令处理：

```ts
chat.onCommand("map.highlight", (p) => {
  const { cityIds } = p as { cityIds: string[] }
  map.highlight(cityIds)
})
chat.onCommand("map.flyTo", (p) => {
  const { lng, lat, zoom } = p as { lng: number; lat: number; zoom: number }
  map.flyTo([lng, lat], zoom)
})
```

2. 用户在地图上选点，页面把点位交给聊天：

```ts
map.on("click", (e) => {
  chat.attach("选中点位", { lng: e.lngLat.lng, lat: e.lngLat.lat })
  chat.insertText("请分析这个点位周边的商业情况")
})
```

3. 用户点发送 → 智能体调用技能工具（技能里查数据并返回 `_meta.bridge`）→ 页面收到 `map.highlight` 指令完成高亮。

## iframe 嵌入形态

把 Blade 聊天页用 iframe 嵌进自己系统时，宿主侧 API 与上面完全一样（`onCommand` / `attach` / `insertText` / `send`），见 [embedded-iframe.md](embedded-iframe.md)。

## 相关：工具可视化预览（_meta.ui）

技能工具返回 `_meta.ui`（`resourceHTML` 或 `resourceUri`）时，`ChatView` 会渲染成 iframe 卡片；自建 UI 可监听 `chat.on("toolPreview", ...)` 自行展示。这与页面协作指令是两套独立机制：`_meta.ui` 渲染内容，`_meta.bridge` 驱动页面行为。

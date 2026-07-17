# iframe 嵌入

如果你不打算在自己的页面里渲染聊天组件，而是把 **Blade 的聊天页面整个用 iframe 嵌进自己的系统**，用 `connectEmbedded()` 在宿主页面拿到协作 API。它与同页集成的 API 完全一样（`onCommand` / `attach` / `insertText` / `send`），业务代码可以原样复用。

```bash
npm install @blade-hq/agent-client
```

## 最小示例

```html
<iframe id="blade" src="https://blade.example.com/chat" style="width: 480px; height: 100%; border: 0"></iframe>
```

```ts
import { connectEmbedded } from "@blade-hq/agent-client"

const chat = connectEmbedded({
  iframe: document.querySelector<HTMLIFrameElement>("#blade")!,
  allowedOrigins: ["https://blade.example.com"],
})

// 智能体 → 页面（payload 是 unknown，用前需自行断言或校验）
chat.onCommand("map.highlight", (payload) => {
  const { cityIds } = payload as { cityIds: string[] }
  map.highlight(cityIds)
})

// 页面 → 智能体
chat.attach("选中点位", { lng: 116.4, lat: 39.9 })
chat.insertText("请分析这个区域")
chat.send("这里适合开店吗？")

// 页面卸载时
chat.dispose()
```

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `allowedOrigins` | **是** | 允许接收消息的来源列表，填 Blade 页面的 origin（如 `"https://blade.example.com"`）。发往 iframe 的消息用列表第一项作为目标来源 |
| `iframe` | 否 | 嵌入 Blade 页面的 iframe 元素。不传则只监听来自任意子窗口的消息，且无法向智能体发消息（`attach` / `insertText` / `send` 会失效并告警） |

返回的对象：`onCommand(action, handler)`、`attach(label, data)`、`insertText(text)`、`send(text)`、`dispose()`。

## 安全说明

::: danger allowedOrigins 必填
不校验来源意味着**任意第三方页面都能向你的页面伪造智能体指令**（例如伪造一条"删除全部数据"的指令让你的页面执行）。`allowedOrigins` 为空时 SDK 直接抛错，也不要填 `"*"`。
:::

SDK 的安全保障：

- 消息来源 origin 必须在 `allowedOrigins` 内；传了 `iframe` 时还要求消息确实来自该 iframe 的窗口（两层校验）。
- 发往 iframe 的消息不使用 `"*"` 作为目标来源，避免内容泄漏给被替换的页面。

你这边需要注意：

- 只把你真正信任的 Blade 部署地址放进列表，**不要**把用户可配置的地址原样传进来。
- 指令处理函数里不要 `eval` 或按 payload 拼接执行任意逻辑，按 action 白名单分发到具体业务函数。

## action 从哪里来

与同页集成一致：action 是**技能作者**在工具返回值 JSON 的 `_meta.bridge` 里写的暗号，Blade 页面检测到自己处于 iframe 中时会把它转发给宿主页面。技能侧与页面侧的并排示例见[页面协作](./host-integration.md)。

## 怎么选：iframe 还是同页集成

| 场景 | 建议 |
| --- | --- |
| 想深度定制聊天界面、共享登录态、多个聊天并存 | 同页集成（[React](./react.md) / [Vue](./vue.md)） |
| 只想"塞一个 Blade 聊天进来"，不想给主应用加 npm 依赖，要求与主应用彻底隔离 | iframe + `connectEmbedded` |

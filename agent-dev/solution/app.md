# 解决方案应用开发

## 什么是 Solution App

Solution App 是将解决方案作为独立应用运行的模式。通过配置 `layout_type`，解决方案可以拥有定制化的 UI 布局，而不仅仅是默认的对话界面。

这适用于需要特定工作区布局的业务场景，例如带有预览面板的文档工作台、带有代码编辑器的开发环境等。

## layout_type 配置

在 `solution.yaml` 或 `role.yaml` 中通过 `layout_type` 字段指定布局类型：

| layout_type | 说明 |
|-------------|------|
| `default` | 默认对话布局，纯聊天界面 |
| `chat-only` | 仅聊天界面 |
| `chat-preview` | 对话 + 预览面板 |
| `skill-editor` | 技能编辑器布局，左侧编辑器 + 右侧对话 |
| `blade-coa` | 工作台布局，支持多面板协作 |
| `solution-app` | 独立应用布局，需配合 `ui.json` 使用 |

```yaml
# solution.yaml 中设置全局默认布局
layout_type: blade-coa

# role.yaml 中可覆盖特定角色的布局
layout_type: default
```

角色级 `layout_type` 会覆盖 solution 级的设置。

## 工作台布局（blade-coa）

`blade-coa` 布局提供多面板工作台，适合需要同时查看对话和内容预览的场景：

```
+----------------------------------------------------------+
|  工作台布局 (blade-coa)                                    |
+----------------------------------------------------------+
|  对话区               |  预览区                           |
|  +----------------+   |  +----------------------------+   |
|  | 用户: 生成报告  |   |  |                            |   |
|  |                |   |  |  [渲染的 HTML / 文档预览]    |   |
|  | 智能体: 已生成  |   |  |                            |   |
|  | 报告，请查看    |   |  |                            |   |
|  | 右侧预览。     |   |  |                            |   |
|  +----------------+   |  +----------------------------+   |
+----------------------------------------------------------+
```

## 固定预览布局配置

对于需要固定预览内容的场景（如始终显示某个文档或仪表盘），可以在 `solution.yaml` 的 `data` 字段中配置预览面板的默认内容：

```yaml
id: my_app
name: 报告工作台
manifest_version: 3
version: 1.0.0
layout_type: blade-coa
data:
  preview:
    default_url: "/preview/dashboard.html"
roles:
  - report_writer
```

`data` 字段为自定义扩展数据，布局组件会读取其中的配置来初始化预览面板。

## 独立应用布局（solution-app）

`solution-app` 布局将 Solution 作为独立应用运行，具有品牌化的项目列表、创建表单等定制 UI。推荐在 Solution 根目录提供 `ui.json` 配置文件来定制界面；缺失时前端使用默认配置。

### ui.json 配置

`ui.json` 必须包含 `branding` 字段，其他字段可选：

```json
{
  "branding": {
    "name": "智能标书",
    "subtitle": "Smart Bid Assistant",
    "icon_text": "标",
    "icon_gradient": "from-blue-500 to-indigo-600"
  },
  "list": {
    "title": "标书项目",
    "create_button": "新建标书项目",
    "card": {
      "subtitle": "$.meta.buyer",
      "stats": [
        { "label": "已填字段", "value": "$.meta.filled" },
        { "label": "待确认", "value": "$.meta.pending", "color": "amber" }
      ]
    }
  },
  "create": {
    "title": "创建标书项目",
    "description": "说明你要做什么，并上传相关材料",
    "submit_button": "创建标书项目",
    "sections": [
      {
        "id": "intent",
        "title": "你要做什么？",
        "fields": [
          {
            "id": "description",
            "kind": "textarea",
            "label": "任务描述",
            "placeholder": "例如：请根据招标文件自动生成投标文件"
          }
        ]
      },
      {
        "id": "upload",
        "title": "上传项目材料",
        "fields": [
          {
            "id": "files",
            "kind": "file-upload",
            "accept": [".docx", ".pdf", ".zip"],
            "categories": [
              { "label": "招标文件", "description": "招标公告、采购文件", "color": "blue" },
              { "label": "公司资质", "description": "营业执照、资质证书", "color": "amber" }
            ]
          }
        ]
      }
    ]
  }
}
```

`card.stats[].value` 支持 `$.meta.<key>` 格式的引用，从项目的 `.ui/state.json` 中 `meta` 字段动态取值。

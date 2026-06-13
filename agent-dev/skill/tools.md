# 内置系统工具

Blade Agent 提供多个内置系统工具，技能和智能体可以直接调用。

## 通用参数

所有系统工具统一支持 `description` 参数，用于向用户说明本次工具调用的目的。智能体在调用工具时应填写简短的中文描述，帮助用户理解当前操作。

```json
{
  "tool": "bash_tool",
  "input": {
    "description": "检查项目依赖是否安装完成",
    "command": "npm ls --depth=0"
  }
}
```

## RenderHtml 工具

`RenderHtml` 工具用于将 HTML 内容渲染到预览面板中（需要 `blade-coa` 等支持预览的布局）。智能体可以通过该工具动态生成报告、图表、文档等可视化内容。

```json
{
  "tool": "RenderHtml",
  "input": {
    "description": "渲染季度销售报告",
    "html": "<h1>Q1 销售报告</h1><p>总额：120 万</p>"
  }
}
```

## Bash 工具与 `_meta` 输出

Bash 工具执行命令后，除了标准输出外，还支持通过 `_meta` 字段传递结构化元数据。脚本通过向 stdout 输出特定格式的 JSON 来设置 `_meta`。

### `_meta.ui` -- 工具可视化

`_meta.ui` 用于在前端展示工具执行结果的可视化组件。脚本输出带有 `_meta` 的 JSON，前端会根据 `ui` 字段渲染对应的 UI 组件。

```python
import json

result = {
    "data": "实际的工具输出内容",
    "_meta": {
        "ui": {
            "type": "table",
            "title": "查询结果",
            "columns": ["姓名", "部门", "工号"],
            "rows": [
                ["张三", "研发部", "001"],
                ["李四", "产品部", "002"]
            ]
        }
    }
}
print(json.dumps(result, ensure_ascii=False))
```

### `_meta.bridge` -- 宿主通信

`_meta.bridge` 用于工具执行过程中与宿主应用（如 Blade OS 桌面）进行通信。通过 bridge 消息，工具可以触发宿主侧的操作，例如打开文件、跳转页面等。

```python
import json

result = {
    "data": "文件已创建",
    "_meta": {
        "bridge": {
            "action": "open_file",
            "payload": {
                "path": "/workspace/output/report.pdf"
            }
        }
    }
}
print(json.dumps(result, ensure_ascii=False))
```

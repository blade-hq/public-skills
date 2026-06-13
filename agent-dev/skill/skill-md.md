# SKILL.md 编写规范

`SKILL.md` 是技能的核心定义文件，智能体通过它理解技能的用途和使用方法。

## frontmatter 格式

文件顶部必须包含 YAML frontmatter，定义技能的元数据：

```yaml
---
name: my-skill-name
display_name: 我的技能
description: >
  一句话描述技能的用途。
  当用户询问 XXX、需要 YYY 时使用本技能。
---
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 技能唯一标识，与目录名一致 |
| `description` | 是 | 技能描述，用于搜索匹配和智能体理解技能用途 |
| `display_name` | 否 | 技能在 UI 上的显示名称，不填则使用 `name` |

`description` 是技能被发现和选中的关键 -- 技能注册中心通过它进行搜索匹配。写清楚技能解决什么问题、什么场景下触发。

## 内容组织原则

SKILL.md 应该做**路由表**，不堆砌大量内容：

- 顶层说明技能用途和适用场景
- 将详细的参考资料、代码示例放在 `references/` 子目录
- 正文用相对链接指向详细文档，引导智能体按需读取

### 好的示例

```markdown
---
name: agent-kit-sdk
description: "Agent Kit 集成目录：按 React、Vue 前端与 Node.js、Python 后端引导接入 Blade Agent。"
---

# Agent Kit 集成目录

本文件只做目录导航。根据宿主技术栈选择要读的文档。

## React 应用

- [references/react-quickstart.md](references/react-quickstart.md)：最小可复制模板。
- [references/sdk-entrypoints.md](references/sdk-entrypoints.md)：安装、包入口、配置。

## 后端

- [references/backend-quickstart.md](references/backend-quickstart.md)：Node.js 后端模板。
- [references/backend.md](references/backend.md)：完整后端用法。
```

这样做的好处：
- 智能体先看目录，按需读取详细文档，避免一次加载过多内容
- 各参考文档可以独立维护和更新

### 反例

```markdown
---
name: my-skill
description: 做很多事情的技能
---

# 我的技能

（下面堆砌了 500 行代码示例、API 文档、配置说明……）
```

问题：
- `description` 太模糊，搜索时难以匹配
- 所有内容都堆在一个文件里，智能体每次都要处理大量无关信息

## 子技能引用

在 SKILL.md 正文中，可以使用 `[[技能名]]` 语法引用其他技能。当智能体读取当前技能时，被引用的子技能内容也会一并加载。

```markdown
---
name: software-design
description: 软件设计流程技能
---

# 软件设计

本技能负责整体设计流程。

需要使用以下子技能：
- [[prd-writer]] -- 生成 PRD 文档
- [[ui-designer]] -- 生成 UI 设计稿
```

使用场景：当一个技能的执行依赖另一个技能的知识时，通过 `[[子技能名]]` 声明依赖关系，平台会自动加载被引用技能的内容。

## 同组织共用 Python 库

同一组织下的技能可以共享 `_common/` 目录中的 Python 库代码。`_common/` 放在组织的技能根目录下，所有技能均可引用其中的模块。

```
org_a/
├── _common/
│   ├── __init__.py
│   └── utils.py          # 共享工具函数
├── skill-foo/
│   ├── SKILL.md
│   └── scripts/
│       └── run.py         # 可以 import _common.utils
└── skill-bar/
    ├── SKILL.md
    └── scripts/
        └── run.py         # 同样可以 import _common.utils
```

## 资源文件同步

技能目录下的所有文件（不仅是 `SKILL.md`）都会随技能一起同步到运行环境。常见的资源文件组织方式：

```
my-skill/
├── SKILL.md
├── references/            # 参考文档
│   ├── api-guide.md
│   └── examples.md
├── scripts/               # 可执行脚本
│   └── run.py
└── templates/             # 模板文件
    └── report.html
```

在 `SKILL.md` 中用相对路径引用这些文件，智能体可以按需读取。

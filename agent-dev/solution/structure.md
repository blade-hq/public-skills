# 目录结构与 manifest

## v3 目录结构

```
<solution_id>/
├── solution.yaml              # Solution 级配置
├── skills/                    # 本地技能目录（所有角色共享）
│   ├── <skill_id_a>/
│   │   ├── SKILL.md           # 技能定义
│   │   └── references/        # 参考资料（可选）
│   └── <skill_id_b>/
│       └── SKILL.md
└── roles/                     # 业务角色目录
    ├── <biz_role_id_1>/
    │   ├── role.yaml           # 角色运行配置
    │   ├── AGENTS.md.j2        # 角色提示词模板
    │   └── init/run.sh         # 角色初始化脚本（可选）
    └── <biz_role_id_2>/
        ├── role.yaml
        └── AGENTS.md.j2
```

::: tip
新建 Solution 必须使用 `manifest_version: 3`。v1/v2 旧结构仅做兼容读取，不应继续扩展。
:::

## solution.yaml 字段说明

示例：

```yaml
id: software_factory
name: 软件工程工作台
manifest_version: 3
version: 0.3.0
description: 将软件需求从模块拆分、PRD、UI、技术设计到任务分工串联起来
layout_type: default
skill_tools_enabled: true
roles:
  - sf_prd
  - sf_ui_design
```

字段说明：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | string | 是 | - | Solution 唯一标识，非空 |
| `name` | string | 是 | - | Solution 显示名称，非空 |
| `manifest_version` | int | 是 | - | 必须为 `3` |
| `version` | string | 是 | - | 版本号，非空 |
| `description` | string | 否 | `""` | Solution 描述 |
| `layout_type` | string | 否 | `"default"` | 布局类型，可选值：`default`、`skill-editor`、`blade-coa` |
| `initial_mode` | string | 否 | `null` | 默认初始模式，可选值：`planning`、`executing` |
| `initial_message` | string | 否 | `null` | 默认初始消息 |
| `skill_tools_enabled` | bool | 否 | `true` | 是否启用技能工具 |
| `imported_skills` | list[string] | 否 | `[]` | 从技能注册中心引入的全局技能 |
| `roles` | list[string] | 是 | - | 角色 id 列表，至少一个，不允许重复 |
| `data` | dict | 否 | `null` | 自定义扩展数据 |

## 语义规则

- `roles` 列表只填角色 id 字符串，不能是对象。每个 id 必须在 `roles/<role_id>/role.yaml` 中有对应定义。
- 多个角色共用的技能放在解决方案根目录的 `skills/` 下，由各角色的 `local_skills` 引用。
- `layout_type`、`initial_mode`、`initial_message` 可以在 solution 级设置默认值，角色级设置会覆盖。
- 全局技能用 `imported_skills` 引用，不要混入 `local_skills`。
- v3 下禁止在 `roles/<biz_role_id>/skills/` 放置技能。

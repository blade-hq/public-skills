# 业务角色配置

## role.yaml 字段说明

示例：

```yaml
id: sf_prd
name: PRD 需求设计师
version: 0.3.0
description: 以产品经理视角梳理功能需求与业务流程
layout_type: default
initial_mode: executing
initial_message: 请描述你要设计的产品功能。
local_skills:
  - prd_writer
imported_skills:
  - org/global_skill
```

字段说明：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | string | 是 | - | 角色唯一标识，必须与目录名一致 |
| `name` | string | 是 | - | 角色显示名称，非空 |
| `version` | string | 是 | - | 版本号，非空 |
| `description` | string | 否 | `""` | 角色描述 |
| `layout_type` | string | 否 | `null` | 布局类型，覆盖 solution 级设置。可选值：`default`、`skill-editor`、`blade-coa` |
| `initial_mode` | string | 否 | `null` | 初始模式，覆盖 solution 级设置。可选值：`planning`、`executing` |
| `initial_message` | string | 否 | `null` | 初始消息，覆盖 solution 级设置 |
| `local_skills` | list[string] | 否 | `[]` | 引用 Solution 包内 `skills/<skill_id>/` 下的本地技能 |
| `imported_skills` | list[string] | 否 | `[]` | 引用技能注册中心的全局技能 |

## local_skills 与 imported_skills

**local_skills** 引用当前 Solution 包内的技能，路径为 `skills/<skill_id>/SKILL.md`：

```yaml
local_skills:
  - prd_writer      # 对应 skills/prd_writer/SKILL.md
  - code_reviewer   # 对应 skills/code_reviewer/SKILL.md
```

**imported_skills** 引用技能注册中心中的全局技能，格式为 `org/skill_name`：

```yaml
imported_skills:
  - blade/web_search
  - myorg/data_analyzer
```

::: warning
v3 禁止在 `roles/<biz_role_id>/skills/` 下放置技能。如果多个角色需要同一个技能，放在 Solution 级 `skills/` 目录下，然后在各角色的 `local_skills` 中引用。
:::

## initial_mode

控制角色创建会话后的初始工作模式：

- `executing` -- 面向最终用户直接完成任务的角色，创建会话后直接进入干活模式。
- `planning` -- 只做方案拆解、评审或确认前计划的角色，创建会话后进入规划模式。

## initial_message

角色创建会话后自动显示的引导消息，用于提示用户如何开始。例如：

```yaml
initial_message: 请描述你要设计的产品功能。
```

## AGENTS.md.j2 提示词

每个角色目录下可以放置 `AGENTS.md.j2` 文件，作为该角色的系统提示词模板。该文件使用 Jinja2 语法，在创建会话时渲染，写入 session 的 prompt 快照。

文件位置：`roles/<biz_role_id>/AGENTS.md.j2`

::: tip
提示词在创建会话时快照，后续修改文件不会影响已有会话。
:::

## 技能工具开关

Solution 级 `skill_tools_enabled` 控制是否为技能生成对应的工具调用。设置为 `true` 时，智能体可以通过工具调用的方式使用技能；设置为 `false` 时，技能内容仅作为提示词的一部分注入，不生成独立的工具。

该配置在 `solution.yaml` 中设置，影响整个解决方案下所有角色的行为。

# 校验工具

## validate_solution.py

在创建或修改 Solution 包后，可以使用校验脚本快速检查结构是否正确：

```bash
uv run --script skills/solution-structure/scripts/validate_solution.py <solution_dir>
```

脚本使用 inline dependency metadata 声明 `pydantic` 和 `pyyaml`，`uv run --script` 会自动准备依赖，无需手动安装。

校验通过输出：

```
OK: <solution_dir>
```

校验失败时，会逐条列出错误：

```
ERROR: <具体错误信息>
```

## 校验项

脚本会检查以下内容：

- `solution.yaml` 存在且为合法 YAML
- `manifest_version` 为 `3`
- `id`、`name`、`version` 为非空字符串
- `roles` 为非空、无重复的 role id 字符串列表
- `layout_type` 为允许值（`default`、`skill-editor`、`blade-coa`）
- `initial_mode` 为允许值（`planning`、`executing`）
- 每个 `roles/<id>/role.yaml` 存在，`id`/`name`/`version` 完整
- `role.yaml` 的 `id` 与目录名一致
- v3 下不存在 `roles/<id>/skills/` 目录
- `local_skills` 引用的 `skills/<id>/SKILL.md` 文件存在
- 不使用旧字段 `skills`
- 不包含未知字段（使用 `extra="forbid"` 严格校验）

::: info
此脚本只做本地结构校验，不替代平台的加载和运行时校验。
:::

## 常见校验错误及解决

| 错误信息 | 原因 | 解决方法 |
|----------|------|----------|
| `file not found` | `solution.yaml` 或 `role.yaml` 不存在 | 检查路径和文件名是否正确 |
| `id: must be a non-empty string` | `id` 字段为空或缺失 | 填写非空的 `id` 值 |
| `roles: must contain at least one role id` | `roles` 列表为空 | 至少添加一个角色 id |
| `id must match role directory name` | `role.yaml` 中的 `id` 与所在目录名不一致 | 保持 `id` 和目录名一致 |
| `v3 does not support role-local skills` | 在 `roles/<id>/skills/` 下放了技能 | 将技能移到 Solution 级 `skills/` 目录 |
| `local skill ... is missing` | `local_skills` 引用的技能目录下没有 `SKILL.md` | 在 `skills/<id>/` 下创建 `SKILL.md` |
| `Extra inputs are not permitted` | YAML 中包含未知字段 | 移除多余字段或检查拼写 |

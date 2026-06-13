# 校验工具

## 自动校验

在「技能开发」应用（`http://<host>:8020/studio/skill-editor`）中上传解决方案包时，系统会自动校验目录结构和字段合法性。无需手动运行脚本，上传即校验。

校验通过后，解决方案会被加载到调试环境；校验失败时，界面会逐条列出错误信息。

```
+----------------------------------------------------------+
|  技能开发 - 上传解决方案                                    |
+----------------------------------------------------------+
|                                                          |
|  文件: my_solution.zip                    [上传]          |
|                                                          |
|  校验结果:                                                |
|  x role.yaml 中的 id "prd" 与目录名 "sf_prd" 不一致       |
|  x local_skills 引用的 "analyzer" 在 skills/ 下不存在     |
|  x roles 列表为空，至少需要一个角色                         |
|                                                          |
+----------------------------------------------------------+
```

## 校验项

系统会检查以下内容：

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
- 不使用已废弃的旧字段
- 不包含未知字段

## 常见校验错误及解决

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `id` 与目录名不一致 | `role.yaml` 中的 `id` 与所在目录名不同 | 保持 `id` 和目录名一致 |
| 技能路径不存在 | `local_skills` 引用的技能在 `skills/` 下找不到 | 在 `skills/<id>/` 下创建 `SKILL.md` |
| `roles` 列表为空 | `solution.yaml` 中没有定义角色 | 至少添加一个角色 id |
| 包含未知字段 | YAML 中存在不支持的字段 | 移除多余字段或检查拼写 |
| v3 不支持角色级技能目录 | 在 `roles/<id>/skills/` 下放了技能 | 将技能移到 Solution 级 `skills/` 目录 |
| `layout_type` 值不合法 | 使用了不支持的布局类型 | 使用 `default`、`skill-editor` 或 `blade-coa` |

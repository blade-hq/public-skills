# 调试与排查

## 本地运行 Solution

Solution 包放置在 blade-agent 的内置目录下即可加载：

```
host/src/blade_agent/host/solutions/builtin/<solution_id>/
```

启动 blade-agent 后，`SolutionRegistry` 会自动扫描该目录，读取 `solution.yaml` 和各角色的 `role.yaml`。

### Session 创建链路

创建 Solution session 时，平台按以下顺序执行：

1. 读取 `solution.yaml`
2. 根据 `roles` 列表读取每个 `roles/<id>/role.yaml`
3. 解析当前 `biz_role_id`
4. 写入 session setup snapshot（role prompt、name/version、layout、initial mode/message）
5. 同步当前角色可见技能（`local_skills` + `imported_skills`）
6. 执行 `roles/<id>/init/run.sh`（工作目录为用户 workspace）
7. 后续对话使用当前角色的 `AGENTS.md.j2` 提示词

::: warning
提示词和布局在创建会话时快照，修改文件不会影响已有会话。需要新建会话才能生效。
:::

## 在「技能开发」应用中调试 Skill

blade-agent 提供 `skill-editor` 布局类型，可用于技能开发和调试。在该模式下，可以实时编辑 `SKILL.md` 并测试效果。

## 校验 Solution 结构

修改 Solution 后，使用校验脚本检查结构：

```bash
uv run --script skills/solution-structure/scripts/validate_solution.py <solution_dir>
```

常见问题排查：

| 问题 | 排查方向 |
|------|----------|
| v3 加载失败提示 role 缺少字段 | 检查 `roles/<id>/role.yaml` 是否包含 `id`、`name`、`version` |
| local skill 找不到 | 确认路径为 `skills/<skill_id>/SKILL.md`，不是 `roles/<id>/skills/` |
| Skill Registry 引用失败 | 确认技能写在 `imported_skills`，且注册中心能解析该 `org/skill_name` |
| 前端 layout 不符合预期 | 检查 role 级 `layout_type`，它会覆盖 solution 级默认值 |
| 旧 session 行为和新文件不同 | 检查 session setup snapshot；创建后快照不会跟随文件变化 |

## 查看智能体日志

排查智能体运行行为时，可以使用以下方式：

- **Langfuse**：blade-agent 将完整运行链路记录到 Langfuse，包括根/子智能体上下文、模型调用、工具调用等。通过 Langfuse trace/session 可以逆向分析智能体的推理过程。
- **容器日志**：查看 blade-agent 容器的标准输出日志，包含 session 创建、技能同步、错误信息等。

```bash
# 查看容器日志
docker logs <container_name> --tail 100 -f
```

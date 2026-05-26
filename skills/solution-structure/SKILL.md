---
name: solution-structure
description: >
  解释、设计或修改 blade-agent 的 Solution / BizRole 目录结构与 manifest。
  当用户询问 solution.yaml、role.yaml、manifest_version、BizRole、layout_type、
  local_skills、imported_skills、AGENTS.md.j2、init/run.sh、内置 solution 迁移、
  skill_editor 或 software_factory 的 Solution 结构时使用本技能。
---

# Solution 结构说明

本技能用于处理 `blade-agent` 的 Solution 包结构。Solution 是一个业务工作台包；BizRole 是用户实际进入的工作角色。新功能应优先按 `manifest_version: 3` 设计。

## 核心文件

| 文件 | 职责 |
|------|------|
| `host/src/blade_agent/host/solutions/model.py` | `Solution` / `BizRole` 数据模型 |
| `host/src/blade_agent/host/solutions/manifest.py` | `solution.yaml` 与 `role.yaml` 解析和字段校验 |
| `host/src/blade_agent/host/solutions/registry.py` | 扫描内置 Solution，编译 prompt，加载 BizRole |
| `host/src/blade_agent/host/solutions/skill_sync.py` | 创建 session 时同步可见 skills |
| `host/src/blade_agent/host/_engine_session_create.py` | Solution session 创建、setup snapshot、init 执行 |
| `host/src/blade_agent/host/orchestrator/prompt.py` | 渲染 Solution/BizRole `AGENTS.md.j2` |
| `server/src/blade_agent/server/routes/solutions.py` | Solution 与 BizRole 列表 API |

## v3 目录结构

```text
host/src/blade_agent/host/solutions/builtin/<solution_id>/
  solution.yaml
  skills/
    <local_skill_id>/
      SKILL.md
  roles/
    <biz_role_id>/
      role.yaml
      AGENTS.md.j2
      init/run.sh
```

`solution.yaml` 只放 Solution 包级信息和默认值：

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

`roles/<biz_role_id>/role.yaml` 放角色运行配置：

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

## 语义规则

- `solution.yaml.roles` 在 v3 中只能是 role id 字符串列表。
- `role.yaml.id` 必须与目录名、`solution.yaml.roles` 条目一致。
- `role.layout_type` 覆盖 `solution.layout_type`；有效 layout 会写入 session setup snapshot。
- `role.initial_mode` 和 `role.initial_message` 覆盖 solution 默认值。
- `role.local_skills` 只引用当前 Solution 包内的 `solution/skills/<skill_id>/`。
- `role.imported_skills` 引用 Skill Registry 中的全局 skill。
- v3 禁止 `roles/<biz_role_id>/skills/`；共享 skill 必须放在 solution 级 `skills/` 下。
- v1/v2 旧结构仍兼容读取，但不要为新功能继续扩展 v1/v2。

## Session 创建链路

创建 Solution session 时：

1. `SolutionRegistry` 读取 `solution.yaml`。
2. v3 根据 `roles` 列表读取每个 `roles/<id>/role.yaml`。
3. `Engine.create_session()` 解析当前 `biz_role_id`。
4. 写入 session setup snapshot：role prompt source、role name/version、effective layout、initial mode/message。
5. `sync_solution_skills()` 同步当前 role 可见技能：
   - `role.local_skills` → `solution/skills/<id>`
   - `solution.imported_skills` → Skill Registry
   - `role.imported_skills` → Skill Registry
6. 执行 `roles/<id>/init/run.sh`，工作目录是用户 workspace。
7. 后续 prompt 使用当前 role 的 `AGENTS.md.j2`。

## 修改建议

- 新增 Solution 时直接使用 v3。
- 新增可复用技能时放在 `solution/skills/<id>/`，再由各 role 的 `local_skills` 引用。
- 如果多个 role 需要同一个 skill，不要复制到多个 role 目录。
- 如果需要引用技能商店/全局 registry，用 `imported_skills`，不要混入 `local_skills`。
- 修改 layout 或初始消息时优先放 role 级；只有所有角色共享时才放 solution 级。
- 改 manifest/schema 后同步更新测试：`tests/test_solution_manifest.py`、`tests/test_host_sessions.py`、`tests/test_solutions_route.py`、`tests/test_resume_session_solution.py`。

## AI 写作校验流程

当你创建或修改 Solution 包时，完成后必须做一次结构自检：

```bash
python skills/solution-structure/scripts/validate_solution.py <solution_dir>
```

如果当前工作目录不是本仓库，先定位本技能目录，再运行其中的脚本。脚本依赖 `pydantic` 和 `pyyaml`；在 `blade-agent` 仓库中可以用项目自己的 Python 环境运行。这个脚本不替代平台加载校验，但能在 AI 写文件后快速发现常见结构错误。

校验通过后，再根据任务需要运行项目测试。至少检查：

- `solution.yaml` 是 v3，并且 `roles` 是 role id 字符串列表。
- 每个 `roles/<id>/role.yaml` 存在，且 `id/name/version` 完整。
- `role.yaml.id` 与 role 目录名一致。
- v3 下不存在 `roles/<id>/skills/`。
- `local_skills` 引用的 `solution/skills/<id>/SKILL.md` 存在。
- `role.yaml` 不使用旧字段 `skills`。
- `layout_type` 与 `initial_mode` 使用允许值。

## 常见问题

- **v3 加载失败提示 role 缺少字段**：检查 `roles/<id>/role.yaml` 是否包含 `id/name/version`。
- **local skill 找不到**：确认路径是 `solution/skills/<skill_id>/SKILL.md`，不是 `roles/<id>/skills/`。
- **Skill Registry 引用失败**：确认写在 `imported_skills`，并且 registry 能解析该 canonical id。
- **前端 layout 不符合预期**：检查 role 级 `layout_type`，它会覆盖 solution 默认值。
- **旧 session 行为和新文件不同**：优先检查 session setup snapshot；创建后 prompt/layout 快照不会实时追随文件变化。

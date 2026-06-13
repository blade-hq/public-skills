# 技能注册中心

技能注册中心（Skill Registry）是 Blade Agent 的技能管理服务，提供技能的注册、搜索、版本管理和分发能力。

## 搜索机制

注册中心默认使用 **BM25**（jieba 分词）进行全文搜索，可选启用 **Embedding** 语义搜索：

1. BM25 和 Embedding 分别对全部技能全量打分
2. 如指定候选集（`candidates`），先过滤到候选集内
3. 各自在候选集内做 min-max 归一化到 [0, 1]
4. 加权合并：`score = bm25_weight x bm25 + embedding_weight x embedding`
5. 按合并分数降序取 top_k 返回

Embedding 支持三种模式：

| 模式 | 说明 |
|------|------|
| `none` | 纯 BM25，默认模式，无需额外依赖 |
| `local` | 本地模型（默认 `BAAI/bge-small-zh-v1.5`） |
| `openai` | OpenAI 兼容 API |

## 组织与命名空间

技能通过 `org/skill_name` 的命名空间进行隔离。每个组织拥有独立的技能目录：

```
data/
├── org_a/
│   └── skills/
│       ├── skill-foo/
│       │   ├── metadata.json
│       │   └── versions/
│       │       └── 1.0.0/
│       │           └── SKILL.md
│       └── skill-bar/
└── org_b/
    └── skills/
```

在 Solution 的 `imported_skills` 中引用全局技能时，使用完整的 `org/skill_name` 格式。

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /skills?limit=100&offset=0&org=xxx` | 列出技能（支持分页和组织过滤） |
| `GET /skills/search?q=关键词&limit=10` | 搜索技能 |
| `GET /skills/search?q=关键词&candidates=id1&candidates=id2` | 在候选集内搜索 |
| `GET /skills/orgs` | 列出所有组织 |
| `GET /skills/{org}/{name}` | 获取技能详情 |
| `GET /skills/{org}/{name}/versions` | 列出版本 |
| `GET /skills/{org}/{name}/versions/{version}` | 获取指定版本详情 |
| `PUT /skills/{org}/{name}/release` | 设置 release 版本 |
| `GET /skills/{org}/{name}/files` | 列出文件 |
| `GET /skills/{org}/{name}/files/{path}` | 读取文件内容 |
| `GET /skills/{org}/{name}/download` | 下载技能（zip） |

# 发布与版本管理

## 上传流程

技能通过 ZIP 包上传到注册中心：

1. 将技能目录打包为 ZIP 文件（包含 `SKILL.md` 及相关资源）
2. 调用上传接口：

```bash
curl -X POST \
  "http://<registry_host>:8010/skills/{org}/{name}/versions/{version}" \
  -F "file=@skill.zip"
```

3. 注册中心自动解压并创建版本目录
4. 上传成功后，可通过 `PUT /skills/{org}/{name}/release` 设置当前 release 版本

### 上传限制

| 限制项 | 默认值 |
|--------|--------|
| 单次上传 ZIP 最大字节数 | 50 MB |
| ZIP 内最大文件数 | 500 |
| ZIP 解压后最大总字节数 | 200 MB |

## 版本号规范

版本号使用语义化版本（SemVer）格式：`主版本号.次版本号.修订号`

```
1.0.0    # 首次发布
1.1.0    # 新增功能
1.1.1    # 修复问题
2.0.0    # 不兼容变更
```

每个技能可以有多个版本，通过 release 标记指定当前推荐使用的版本。

## 版本管理

| 操作 | 接口 |
|------|------|
| 上传新版本 | `POST /skills/{org}/{name}/versions/{version}` |
| 查看所有版本 | `GET /skills/{org}/{name}/versions` |
| 查看指定版本 | `GET /skills/{org}/{name}/versions/{version}` |
| 设置 release 版本 | `PUT /skills/{org}/{name}/release` |
| 下载技能 | `GET /skills/{org}/{name}/download` |

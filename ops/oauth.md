# Blade OAuth 配置

Blade OAuth 是平台的统一认证服务，运行在 `http://<host>:19000`，管理后台地址为 `http://<host>:19000/admin`。

## 认证方案

Blade OAuth 替代了早期的 Casdoor 方案，提供更轻量的认证能力。所有平台服务（Blade Agent、Blade OS、Skill Registry 等）均通过 Blade OAuth 完成用户认证和鉴权。

## SSO 免登配置

Blade OAuth 支持与企业现有 SSO 系统对接，实现免登录访问。在管理后台的 SSO 配置页面中，设置企业 SSO 的回调地址和参数即可完成对接。

## PAT signing_secret 配置

Personal Access Token（PAT）用于 API 调用的身份认证。需要在 Blade OAuth 配置中设置 `signing_secret`，用于签发和校验 PAT：

```yaml
pat:
  signing_secret: <your-secret-key>
```

`signing_secret` 必须是足够长的随机字符串，生产环境中请使用安全的随机生成器生成。

## 默认账号

::: danger 生产环境必须修改默认密码
以下默认账号仅用于初始部署和测试，生产环境部署后必须立即修改密码。
:::

| 账号类型 | 用户名 | 默认密码 | 用途 |
|---------|--------|---------|------|
| 管理员 | `admin` | `admin123` | Blade OAuth 管理后台 |
| OS 管理员 | `osadmin` | `osadmin123` | Blade OS 系统管理 |

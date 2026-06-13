# 安全与加密

## PyArmor 加密

平台核心代码通过 PyArmor 进行加密保护，防止源码泄露。

加密范围：
- blade-agent 核心引擎代码
- 内置系统工具代码

排除范围：
- `skills/` 目录 -- 技能代码不加密，便于用户自定义和调试
- 配置文件和模板

## Blade OAuth 证书校验

Blade OAuth 签发的 Token 使用非对称加密算法签名。各服务在验证 Token 时需要配置 Blade OAuth 的公钥或证书地址：

- 服务启动时会自动从 Blade OAuth 拉取公钥
- 如果 Blade OAuth 不可达，服务将无法验证用户身份
- 确保各服务到 Blade OAuth（`http://<host>:19000`）的网络连通性

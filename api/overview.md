# API 概览

## 基础地址

所有 HTTP 接口的基础路径为 `/api`，完整 URL 示例：

```
https://blade.example.com/api/sessions
```

Socket.IO 连接地址：

```
wss://blade.example.com/socket.io/
```

## 认证

所有请求（HTTP 和 WebSocket）使用统一的 Bearer Token 认证。

### HTTP 请求

在请求头中携带：

```
Authorization: Bearer sk-blade-v2-xxxxxxxxxx
```

### Socket.IO 连接

在连接握手时通过 `auth` 参数传递：

```json
{
  "token": "sk-blade-v2-xxxxxxxxxx"
}
```

### Token 类型

| 类型 | 格式 | 说明 |
|------|------|------|
| API Key | `sk-blade-v2-...` | 长期有效，推荐后端服务使用 |
| Session JWT | JWT 字符串 | 短期有效，浏览器同源场景 |

API Key 通过 Web 管理界面创建，或调用 `POST /api/user/api-keys/` 接口创建。明文仅在创建时返回一次。

## 通用约定

### 请求格式

- Content-Type：`application/json`（除文件上传外）
- 文件上传使用 `multipart/form-data`

### 响应格式

- 所有响应均为 JSON
- 成功：HTTP 200（或 201/204）
- 错误：HTTP 4xx/5xx，响应体：

```json
{
  "detail": "错误描述"
}
```

### 分页

列表接口统一使用 `limit` + `offset` 分页：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | int | 20 | 每页数量 |
| `offset` | int | 0 | 起始偏移 |

响应中包含 `total` 字段表示总数。

### 日期格式

所有时间字段使用 ISO 8601 格式：`2026-01-01T00:00:00Z`

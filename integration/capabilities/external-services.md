# 外部服务接入（MCP / OpenAPI / GraphQL）

智能体支持对接外部服务，包括 MCP 服务、OpenAPI 接口和 GraphQL 端点。开发者只需提供服务配置，智能体运行时会自动发现并调用。

## 支持的协议

| 协议 | 配置方式 | 说明 |
| --- | --- | --- |
| MCP | MCP server 配置文件 | 符合 Model Context Protocol 的服务端 |
| OpenAPI | OpenAPI spec 文件（JSON/YAML） | REST 风格的 HTTP 接口 |
| GraphQL | GraphQL schema + endpoint | GraphQL 端点 |

## 接入步骤

### 1. 准备配置

开发者需要提供：

- **服务地址**：外部服务的 URL
- **认证信息**（如有）：API Key、Bearer Token、Basic Auth 等
- **协议描述文件**：MCP server 配置 / OpenAPI spec 文件 / GraphQL schema

### 2. 放置配置文件

将配置文件放在技能的资源目录中。智能体运行时会自动扫描并加载这些配置。

```
my-skill/
├── SKILL.md
├── resources/
│   ├── mcp-config.json        # MCP server 配置
│   ├── crm-api.openapi.yaml   # OpenAPI spec
│   └── gis-schema.graphql     # GraphQL schema
└── ...
```

### 3. 智能体自动调用

配置就绪后，智能体在执行任务时会根据上下文自动选择合适的外部服务进行调用，无需开发者编写额外的调用逻辑。

## 使用场景

- **GIS 系统**：对接地理信息服务，查询地图数据、坐标转换
- **CRM 接口**：查询客户信息、更新销售记录
- **内部业务 API**：对接企业内部的审批流、数据查询等服务
- **第三方 SaaS**：对接外部 SaaS 平台的开放 API

## MCP 配置示例

```json
{
  "mcpServers": {
    "my-service": {
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

## OpenAPI 配置示例

将标准的 OpenAPI 3.0+ spec 文件放入资源目录即可。智能体会解析其中的 paths、schemas 和 security 定义，自动生成可调用的工具。

```yaml
openapi: "3.0.0"
info:
  title: CRM API
  version: "1.0"
servers:
  - url: https://crm.example.com/api/v1
paths:
  /customers/{id}:
    get:
      summary: 查询客户信息
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: 客户详情
```

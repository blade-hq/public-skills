# LLM Gateway 配置

LLM Gateway 是统一网关，为内网散落的 LLM 上游（vLLM、sglang、OpenAI 兼容服务等）提供单一入口，同时暴露 OpenAI (`/v1/chat/completions`) 和 Anthropic (`/v1/messages`) 两套协议。

默认运行在 `http://<host>:30000`。

## 上游配置

### 添加 Source

通过 `config/config.yaml` 或管理 API 添加上游：

```yaml
sources:
  - id: vllm-local
    name: 本地 vLLM
    protocol: openai
    base_url: http://192.168.130.8:30020/v1
    enabled: true
    priority: 20
    rescan_interval: 60s

  - id: openai-cloud
    protocol: openai
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY    # 从环境变量读取
    enabled: false
```

通过 API 动态管理：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sources` | 列出所有源（含模型、健康状态） |
| POST | `/api/sources` | 添加源 |
| PATCH | `/api/sources/{id}` | 修改源（enable/url/priority 等） |
| DELETE | `/api/sources/{id}` | 删除源 |
| POST | `/api/sources/{id}/discover` | 手动触发模型重扫 |

每个源独立运行一个 goroutine，定时扫 `/v1/models` 拉模型并跑健康检查。

### 声明模型输入模态

Anthropic 协议的源需手动声明模型列表（无法自动发现）：

```yaml
  - id: anthropic-proxy
    protocol: anthropic
    base_url: http://192.168.130.8:30021
    models: [qwen3.5-122b-int4]    # 手动指定
    enabled: true
```

blade-agent 侧通过 `.env` 配置模型能力：

```bash
# 是否支持视觉输入（默认 true）
SUPPORTS_VISION=true

# 工具结果中图片的呈现方式
#   inline       — 图片嵌入 tool message（Anthropic 原生）
#   user_message — 图片作为 user message 注入（OpenAI 兼容）
#   disabled     — 不返回图片
TOOL_RESULT_IMAGE_MODE=user_message
```

## 模型路由

请求中的 `model` 字段按以下顺序匹配：

### 1. 显式路由

格式：`source_id/model_id`，强制走指定源。

```json
{"model": "vllm-direct/qwen3.5-35b-a3b-nvfp4"}
```

### 2. 别名

命中 `/api/aliases` 映射后递归解析。

```yaml
aliases:
  claude-3-5-sonnet-20241022: vllm-via-sysfix/qwen3.5-122b-int4
```

通过 API 管理别名：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/aliases` | 列出所有别名 |
| POST | `/api/aliases` | 添加/删除别名（target 为空即删除） |

### 3. 裸 ID（按优先级）

按 `priority` 倒序选第一个 healthy 且声明了该模型的源。全部不健康时回退到 degraded 的源。

## 协议转换

Gateway 自动完成 OpenAI 和 Anthropic 协议互转：

- 请求打到 `/v1/messages`（Anthropic），上游只支持 OpenAI 时，自动翻译
- `tool_use` / `tool_result` / streaming SSE / thinking block 完整转换
- 支持 Qwen3 reasoning 的 thinking block 翻译

### 数据面接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 格式（stream / 非 stream） |
| POST | `/v1/messages` | Anthropic 格式 |
| POST | `/v1/messages/count_tokens` | Token 计数（转到上游 `/tokenize`） |
| GET | `/v1/models` | 聚合所有 enabled 源的模型 |

## 健康与熔断

- 每个源独立健康检查，连续失败自动标记 unhealthy
- 路由时跳过 unhealthy 的源
- 健康恢复后自动重新纳入路由

事件流监控：

```
GET /api/events    # SSE，实时推送 health 变化、模型发现、错误
```

## Blade Agent 连接 LLM Gateway

在 blade-agent 的 `.env` 中配置连接地址：

```bash
agent_llm_endpoint: http://127.0.0.1:30000
```

配置后 blade-agent 会通过 LLM Gateway 统一路由所有 LLM 请求，而非直连上游。

## LLM 观测

LLM Gateway 内置请求观测能力，可在 Blade OS 的高级设置中查看 LLM 调用统计，包括：

- 各模型的请求数量、成功率
- Token 用量统计
- 延迟分布
- 错误详情

也可通过事件流接口实时监控：

```
GET /api/events    # SSE，实时推送 health 变化、模型发现、错误
```

## Web 控制台

打开 `http://<host>:30000/` 可访问内置控制台，功能包括：

- 实时显示源和模型状态
- 事件流展示
- 内置 Playground（可直接测试请求）

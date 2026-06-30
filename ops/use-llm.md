# 使用盒子内的大模型

盒子内置了大语言模型（LLM），通过 LLM Gateway 对外提供 OpenAI 兼容接口。你可以直接调用这些接口，将盒子作为 AI 后端接入自己的应用或工具。

在 Blade OS 桌面的「高级设置」中，点击「模型服务网关」可以打开 Gateway 控制台：

![从 Blade OS 桌面打开模型服务网关](/images/llm-gateway-entry.png)

控制台的「模型」页签可以查看可用模型列表和调用方式示例：

![Gateway 控制台 — 模型名称与调用方式](/images/llm-gateway-console.png)

## 接口信息

### 地址与端口

| 项目 | 值 |
|------|------|
| Base URL | `http://<盒子IP>:30000/v1` |
| 协议 | OpenAI Chat Completions 兼容 |
| 认证方式 | API Key（Bearer Token） |
| 默认 API Key | `sk-local` |

::: tip 从盒子本机访问
如果你在盒子桌面上操作，`<盒子IP>` 可以用 `127.0.0.1`。
:::

### 可用模型

| 模型名称 | 说明 | 上下文长度 | 输入模态 |
|----------|------|-----------|---------|
| `qwen3.5-122b-int4` | Qwen3.5 122B（默认主模型） | 128K | 文本、图片 |
| `qwen3-asr` | Qwen3 语音识别模型 | 4K | 音频 |

::: info 模型别名
Gateway 预配置了一组别名，将常见的 Claude 模型名映射到本地模型。如果你的工具硬编码了 `claude-sonnet-4-20250514` 等模型名，无需修改即可使用。
:::

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | 对话补全（支持 stream） |
| GET | `/v1/models` | 查看可用模型列表 |
| GET | `/health` | 健康检查（注意：不带 `/v1` 前缀） |

## 测试样例

### 检查服务状态

```bash
# 健康检查
curl http://<盒子IP>:30000/health

# 查看可用模型
curl http://<盒子IP>:30000/v1/models \
  -H "Authorization: Bearer sk-local"
```

### 基础对话

```bash
curl http://<盒子IP>:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen3.5-122b-int4",
    "messages": [
      {"role": "user", "content": "1+1等于几？只回答数字"}
    ],
    "max_tokens": 16,
    "temperature": 0,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

### 流式输出

```bash
curl http://<盒子IP>:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -N \
  -d '{
    "model": "qwen3.5-122b-int4",
    "messages": [
      {"role": "user", "content": "用三句话介绍人工智能"}
    ],
    "max_tokens": 512,
    "stream": true,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

### Function Calling（工具调用）

盒子内的模型支持 OpenAI 标准的 Function Calling，你可以让模型调用自定义工具：

```bash
curl http://<盒子IP>:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen3.5-122b-int4",
    "messages": [
      {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "查询指定城市的天气",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string",
                "description": "城市名称"
              }
            },
            "required": ["city"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "max_tokens": 256,
    "temperature": 0,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

模型会返回 `tool_calls`，你的程序负责执行工具并将结果回传：

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"city\": \"北京\"}"
        }
      }]
    }
  }]
}
```

### Python（OpenAI SDK）

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://<盒子IP>:30000/v1",
    api_key="sk-local",
)

response = client.chat.completions.create(
    model="qwen3.5-122b-int4",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    max_tokens=512,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
print(response.choices[0].message.content)
```

### JavaScript / TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://<盒子IP>:30000/v1",
  apiKey: "sk-local",
});

const response = await client.chat.completions.create({
  model: "qwen3.5-122b-int4",
  messages: [
    { role: "user", content: "你好，请介绍一下你自己" },
  ],
  max_tokens: 512,
});
console.log(response.choices[0].message.content);
```

## 配置建议

### 关闭思考模式

Qwen3.5 默认开启"思考模式"（thinking），会在回复前生成一段推理过程。如果你不需要这个功能，建议在请求中关闭以加快响应速度、节省 token：

```json
{
  "chat_template_kwargs": {"enable_thinking": false}
}
```

使用 OpenAI Python SDK 时，通过 `extra_body` 传入：

```python
response = client.chat.completions.create(
    model="qwen3.5-122b-int4",
    messages=[...],
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

如果确实需要思考能力（如复杂推理、数学题），可以保持默认开启或显式设置 `"enable_thinking": true`。

### 上下文长度

主模型支持最大 128K token 的上下文。对于大多数应用场景建议：

- **普通对话**：`max_tokens` 设为 512–2048
- **长文生成**：`max_tokens` 可设到 4096–8192
- **长上下文输入**（如文档分析）：模型支持，但输入越长首次响应越慢

### 并发与性能

- 盒子内的模型运行在本地 GPU 上，并发能力有限
- 建议控制同时请求数在 **2–4 个**以内，避免排队导致延迟升高
- 首次请求可能较慢（模型需要预热），后续请求会利用缓存加速
- 相同的 system prompt 和对话前缀会命中前缀缓存（Prefix Caching），大幅加速重复场景

### 接入第三方工具

盒子的 LLM 接口兼容 OpenAI API，大多数支持"自定义 API 地址"的工具都可以直接接入：

| 工具/框架 | 配置方式 |
|----------|---------|
| [Dify](https://dify.ai) | 模型供应商 → OpenAI-API-compatible，填入 Base URL 和 API Key |
| [LobeChat](https://lobehub.com) | 设置 → 模型服务商 → OpenAI，填入 API 地址和密钥 |
| [Cursor](https://cursor.com) | Settings → Models → OpenAI API Key，设置 Base URL |
| LangChain | 使用 `ChatOpenAI(base_url=..., api_key=...)` |
| LlamaIndex | 使用 `OpenAI(api_base=..., api_key=...)` |

::: warning 注意事项
- 部分工具可能不支持 `chat_template_kwargs` 参数，此时模型会默认开启思考模式
- 如果工具要求 HTTPS，需要在盒子前面加反向代理（如 Nginx）
- 盒子默认在内网运行，确保你的工具能访问盒子的 IP 和端口
:::

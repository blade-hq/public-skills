# 环境变量参考

blade-agent 通过 `.env` 文件配置。复制模板后按需修改：

```bash
cp .env.example .env
```

## LLM 提供者

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `API_KEY` | 是 | - | LLM 提供者 API Key |
| `BASE_URL` | 是 | - | LLM API 地址（如 `https://openrouter.ai/api/v1`） |
| `MODEL_ID` | 是 | - | 默认模型 ID |
| `BLADE_ALLOWED_MODELS` | 否 | 全部 | 前端模型选择器白名单，逗号分隔，按子串匹配 |
| `BLADE_MODEL_ALIASES` | 否 | - | 模型显示别名，格式 `实际ID:显示名,实际ID:显示名` |
| `ENABLE_THINKING` | 否 | `true` | 是否启用 LLM 思考/推理 |
| `CONTEXT_WINDOW` | 否 | - | 上下文窗口大小（token），用于前端显示压力百分比 |
| `SUPPORTS_VISION` | 否 | `true` | 是否支持视觉输入 |
| `TOOL_RESULT_IMAGE_MODE` | 否 | `user_message` | 工具结果图片呈现方式：`inline` / `user_message` / `disabled` |
| `LLM_BACKEND` | 否 | 自动探测 | 手动指定后端类型：`sglang` / `vllm` |
| `SSL_VERIFY` | 否 | `false` | 是否校验 HTTPS 证书 |
| `PROVIDER_ORDER` | 否 | - | OpenRouter provider 路由，逗号分隔 |

## 认证

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `OAUTH_CONFIG_YAML_PATH` | 否 | `configs/oauth_config.yaml` | OAuth 配置文件路径 |
| `BLADE_AUTH_SESSION_SECRET` | 是 | - | SessionMiddleware secret，用于 OAuth state 会话 |

OAuth 配置模板：

| 文件 | 场景 |
|------|------|
| `configs/oauth_config.local.yaml` | 本地 Casdoor 统一登录 |
| `configs/oauth_config.box.yaml` | 盒子部署 |
| `configs/oauth_config.mock.yaml` | 本地 mock 模式（不起 Casdoor） |
| `configs/oauth_config.server.yaml` | HTTPS 反代 / 独立 SSO |

## 技能

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SKILL_REGISTRY_URL` | 否 | - | Skill Registry 地址，留空即离线模式 |
| `BLADE_SKILL_PATHS` | 否 | - | 本地技能目录，多个用冒号分隔 |
| `BLADE_SKILL_DOWNLOAD_CACHE` | 否 | 首个可写 skill path | 远程技能下载缓存目录 |

## 可观测性

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `TRACING_BACKENDS` | 否 | 自动 | 启用的 tracing 后端：`helicone,langfuse` |
| `SENTRY_DSN` | 否 | - | Sentry 错误追踪 DSN |
| `POSTHOG_KEY` | 否 | - | PostHog 前端行为打点 Key |
| `POSTHOG_HOST` | 否 | - | PostHog 服务地址 |
| `LANGFUSE_SECRET_KEY` | 否 | - | Langfuse Secret Key |
| `LANGFUSE_PUBLIC_KEY` | 否 | - | Langfuse Public Key |
| `LANGFUSE_HOST` | 否 | - | Langfuse 服务地址 |
| `HELICONE_API_KEY` | 否 | - | Helicone API Key |

## 搜索与网络

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `BRAVE_SEARCH_API_KEY` | 否 | - | 设置后注册 WebSearch 工具 |
| `BRAVE_SEARCH_BASE_URL` | 否 | Brave 官方 | Brave Search API 地址 |
| `JINA_API_KEY` | 否 | - | 设置后注册 WebFetch 工具 |
| `JINA_BASE_URL` | 否 | `https://r.jina.ai` | Jina Reader API 地址 |

## 沙箱

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SANDBOX_IMAGE` | 否 | 阿里云最新稳定版 | 沙箱镜像全名（含 tag） |
| `BLADE_AGENT_HOST_DIR` | 否 | `.` | 宿主机项目根目录（容器部署时需设置） |
| `SANDBOX_MAX_PIPE_CAPTURE_BYTES` | 否 | 10485760 | 单条管道最大缓冲字节数（约 10MiB） |
| `SANDBOX_PIP_INDEX_URL` | 否 | - | 沙箱内 pip 源地址 |
| `SANDBOX_NPM_CONFIG_REGISTRY` | 否 | - | 沙箱内 npm 源地址 |

## 记忆

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `BLADE_MEMORY_CONFIG` | 否 | `workspace/.blade/memory/config.yaml` | 记忆后端配置 YAML 路径 |

记忆配置示例（`configs/memory.example.yaml`）：

```yaml
version: 1
mode: auto          # auto | vector | lexical
vector:
  provider: openai_compatible
  model: text-embedding-v4
  base_url: https://api.siliconflow.cn/v1
  api_key_env: SILICONFLOW_API_KEY
  dims: 1024
lexical:
  tokenizer: simple
  min_score: 0.05
```

## 其他

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `BLADE_OS_PATH` | 否 | `http://localhost:5178/` | BladeOS 地址 |
| `BLADE_GIS_MAP_URL` | 否 | - | GIS 地图 iframe URL |
| `BLADE_AGENT_MCP_ENABLED` | 否 | `true` | MCP 总开关 |
| `BLADE_ENABLE_HTML_RENDER_TOOL` | 否 | `false` | 启用 RenderHtml 工具 |
| `DOCUMENT_READER` | 否 | `light` | 文档读取方案：`light` / `docling` |
| `MULTICA_SERVER_URL` | 否 | `http://localhost:8080` | Multica 服务地址 |
| `ASR_PROVIDER` | 否 | `volcengine` | 语音识别提供者：`volcengine` / `qwen` |

## 平台环境变量桶

平台级环境变量通过管理后台统一配置，对所有会话生效。管理员可在 Blade OS 的系统设置中管理这些变量，无需修改 `.env` 文件或重启服务。

平台环境变量桶适合配置所有用户共享的 API Key、服务地址等。

## 用户自定义环境变量

用户可在 Blade OS 的个人设置中添加自己的环境变量，这些变量仅对当前用户的会话生效，不影响其他用户。

用户自定义变量会覆盖平台环境变量桶中的同名变量。

## 功能开关

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BLADE_DISABLE_SUBAGENT` | `false` | 设为 `true` 禁用子智能体，智能体将不会创建子任务 |
| `BLADE_AGENT_MCP_ENABLED` | `true` | MCP 总开关 |
| `BLADE_ENABLE_HTML_RENDER_TOOL` | `false` | 启用 RenderHtml 工具 |

## 调试

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `AGENT_STREAM_DEBUG` | 否 | - | 设为 `1` 启用流式调试 |
| `AGENT_EVENT_LOG` | 否 | - | 设为 `1` 启用事件日志 |

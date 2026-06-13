# 监控与观测

## Prometheus

Prometheus 运行在 `http://<host>:9090`，负责采集平台各服务的指标数据。

采集目标包括：
- Blade Agent 服务指标
- LLM Gateway 请求指标
- 沙箱容器资源使用

## Grafana

Grafana 运行在 `http://<host>:3000`，提供监控仪表盘的可视化展示。

默认提供以下仪表盘：
- 服务健康概览
- LLM 请求量与延迟
- 资源使用趋势

## LLM 请求观测

在 Blade OS 的高级设置中可以查看 LLM 调用统计，包括：

- 各模型的调用次数和 Token 用量
- 请求成功率和错误分布
- 响应延迟统计

如需更详细的 LLM 调用追踪，可配置 Langfuse 或 Helicone 作为 tracing 后端，参见[环境变量参考](/ops/env)中的可观测性章节。

---
layout: home
title: Blade OS 帮助文档
hero:
  name: Blade OS
  text: 帮助文档
  tagline: 使用入门、智能体开发、应用接入、部署运维
---

<div class="home-sections">

<div class="home-section">
<h2>使用指南</h2>
<div class="card-grid">
<a class="card" href="/public-skills/guide/getting-started.html">
<h3>快速开始</h3>
<p>注册登录、进入桌面、发起第一次对话</p>
</a>
<a class="card" href="/public-skills/guide/blade-os.html">
<h3>Blade OS 桌面</h3>
<p>桌面布局、窗口操作、内置应用</p>
</a>
<a class="card" href="/public-skills/guide/chat.html">
<h3>智能助手</h3>
<p>对话、语音、文件上传、会话管理、记忆、定时任务</p>
</a>
<a class="card" href="/public-skills/guide/solutions-and-roles.html">
<h3>解决方案与角色</h3>
<p>了解解决方案、角色、如何切换</p>
</a>
<a class="card" href="/public-skills/guide/cloud-computer.html">
<h3>云电脑</h3>
<p>持久化沙箱环境，文件和软件跨会话保留</p>
</a>
<a class="card" href="/public-skills/guide/factory.html">
<h3>软件工厂</h3>
<p>从创建项目到发布应用的完整开发工作台</p>
</a>
</div>
</div>

<div class="home-section">
<h2>开发文档</h2>
<div class="card-grid">
<a class="card" href="/public-skills/agent-dev/concepts.html">
<h3>智能体开发</h3>
<p>创建解决方案、编写技能、配置业务角色</p>
</a>
<a class="card" href="/public-skills/integration/concepts.html">
<h3>应用接入</h3>
<p>通过 SDK 或 API 将智能助手嵌入你的系统</p>
</a>
</div>
</div>

<div class="home-section">
<h2>部署与运维</h2>
<div class="card-grid">
<a class="card" href="/public-skills/ops/docker.html">
<h3>Docker 部署</h3>
<p>Docker Compose 配置、服务启动顺序</p>
</a>
<a class="card" href="/public-skills/ops/llm-gateway.html">
<h3>LLM Gateway</h3>
<p>上游配置、模型路由、协议转换</p>
</a>
<a class="card" href="/public-skills/ops/sandbox.html">
<h3>沙箱镜像定制</h3>
<p>自定义 sandbox Docker 镜像</p>
</a>
<a class="card" href="/public-skills/ops/env.html">
<h3>环境变量参考</h3>
<p>全部环境变量说明</p>
</a>
<a class="card" href="/public-skills/ops/oauth.html">
<h3>Blade OAuth</h3>
<p>认证服务配置、SSO 对接、默认账号</p>
</a>
<a class="card" href="/public-skills/ops/monitoring.html">
<h3>监控与观测</h3>
<p>Prometheus、Grafana、LLM 请求观测</p>
</a>
</div>
</div>

</div>

<style>
.home-sections {
  max-width: 1152px;
  margin: 0 auto;
  padding: 0 24px 64px;
}

.home-section {
  margin-top: 48px;
}

.home-section h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  border: none;
  color: var(--vp-c-text-1);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.vp-doc a.card,
.vp-doc a.card:hover {
  display: block;
  padding: 24px;
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  text-decoration: none;
  color: inherit;
  font-weight: normal;
  transition: border-color 0.25s, box-shadow 0.25s;
}

.vp-doc a.card:hover {
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.vp-doc a.card h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.vp-doc a.card p {
  font-size: 14px;
  margin: 0;
  color: var(--vp-c-text-2);
  line-height: 1.5;
  text-decoration: none;
}
</style>

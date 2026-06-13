import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Blade OS 帮助文档",
  description: "使用入门、智能体开发、应用接入、部署运维",
  lang: "zh-CN",
  base: "/public-skills/",

  srcExclude: ["**/node_modules/**", "**/examples/**", "skills/**"],
  ignoreDeadLinks: true,

  markdown: {
    math: false,
  },

  themeConfig: {
    nav: [
      { text: "使用指南", link: "/guide/getting-started" },
      { text: "智能体开发", link: "/agent-dev/concepts" },
      { text: "应用接入", link: "/integration/concepts" },
      { text: "API 参考", link: "/api/overview" },
      { text: "部署与运维", link: "/ops/docker" },
      {
        text: "v0.5.16",
        items: [
          { text: "v0.5.16（当前）", link: "/" },
        ],
      },
    ],

    sidebar: {
      "/guide/": [
        {
          text: "使用指南",
          items: [
            { text: "快速开始", link: "/guide/getting-started" },
            { text: "Blade OS 桌面", link: "/guide/blade-os" },
            { text: "和智能体对话", link: "/guide/chat" },
            { text: "解决方案与角色", link: "/guide/solutions-and-roles" },
          ],
        },
      ],
      "/agent-dev/": [
        {
          text: "智能体开发指南",
          items: [
            { text: "核心概念", link: "/agent-dev/concepts" },
          ],
        },
        {
          text: "解决方案开发（Solution）",
          items: [
            { text: "目录结构与 manifest", link: "/agent-dev/solution/structure" },
            { text: "业务角色配置", link: "/agent-dev/solution/bizrole" },
            { text: "校验工具", link: "/agent-dev/solution/validation" },
          ],
        },
        {
          text: "技能开发（Skill）",
          items: [
            { text: "SKILL.md 编写规范", link: "/agent-dev/skill/skill-md" },
            { text: "技能注册中心", link: "/agent-dev/skill/registry" },
            { text: "发布与版本管理", link: "/agent-dev/skill/publish" },
          ],
        },
        {
          text: "调试与排查",
          items: [
            { text: "调试指南", link: "/agent-dev/debugging" },
          ],
        },
      ],
      "/integration/": [
        {
          text: "应用接入指南",
          items: [
            { text: "核心概念", link: "/integration/concepts" },
          ],
        },
        {
          text: "前端 SDK 接入",
          items: [
            { text: "React", link: "/integration/frontend/react" },
            { text: "Vue", link: "/integration/frontend/vue" },
            { text: "聊天 UI 与自渲染", link: "/integration/frontend/chat-ui" },
            { text: "宿主页面联动", link: "/integration/frontend/host-integration" },
          ],
        },
        {
          text: "后端接入",
          items: [
            { text: "Node.js", link: "/integration/backend/nodejs" },
            { text: "Python", link: "/integration/backend/python" },
            { text: "鉴权与 Token", link: "/integration/backend/auth" },
            { text: "文件上传", link: "/integration/backend/file-upload" },
          ],
        },
        {
          text: "智能体能力集成",
          items: [
            { text: "工作模式", link: "/integration/capabilities/work-modes" },
            { text: "指定解决方案与角色", link: "/integration/capabilities/solution-role" },
            { text: "会话技能上传", link: "/integration/capabilities/session-skill" },
          ],
        },
        {
          text: "调试与排查",
          items: [
            { text: "调试指南", link: "/integration/debugging" },
          ],
        },
      ],
      "/api/": [
        {
          text: "API 参考",
          items: [
            { text: "概览", link: "/api/overview" },
            { text: "REST 接口", link: "/api/rest" },
            { text: "WebSocket 接口", link: "/api/websocket" },
            { text: "核心类型", link: "/api/types" },
            { text: "会话生命周期", link: "/api/session-lifecycle" },
            { text: "Chat 流程", link: "/api/chat-flow" },
          ],
        },
      ],
      "/ops/": [
        {
          text: "部署与运维",
          items: [
            { text: "Docker 部署", link: "/ops/docker" },
            { text: "LLM Gateway 配置", link: "/ops/llm-gateway" },
            { text: "沙箱镜像定制", link: "/ops/sandbox" },
            { text: "环境变量参考", link: "/ops/env" },
          ],
        },
      ],
    },

    search: { provider: "local" },
    outline: { level: [2, 3], label: "目录" },
    docFooter: { prev: "上一页", next: "下一页" },
    lastUpdated: { text: "最后更新" },
    returnToTopLabel: "返回顶部",
    sidebarMenuLabel: "菜单",
    darkModeSwitchLabel: "主题",
  },
});

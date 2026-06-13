import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Blade Agent 开发文档",
  description: "SDK 集成、API 协议、Solution 结构、运维工具",
  lang: "zh-CN",
  base: "/public-skills/",

  srcExclude: ["**/node_modules/**", "**/examples/**"],
  ignoreDeadLinks: true,

  themeConfig: {
    nav: [
      {
        text: "Agent Kit SDK",
        items: [
          { text: "JavaScript", link: "/skills/agent-kit-sdk/docs/" },
          { text: "Python", link: "/skills/agent-kit-sdk/references/backend" },
        ],
      },
      { text: "Solution 结构", link: "/skills/solution-structure/SKILL" },
      { text: "沙箱镜像", link: "/skills/sandbox-image-customizer/SKILL" },
    ],

    sidebar: {
      "/skills/agent-kit-sdk/": [
        {
          text: "快速开始",
          items: [
            { text: "概览", link: "/skills/agent-kit-sdk/docs/" },
            {
              text: "React 快速接入",
              link: "/skills/agent-kit-sdk/references/react-quickstart",
            },
            {
              text: "后端快速接入",
              link: "/skills/agent-kit-sdk/references/backend-quickstart",
            },
          ],
        },
        {
          text: "API 协议（中文）",
          collapsed: true,
          items: [
            { text: "API 概览", link: "/skills/agent-kit-sdk/docs/API概览" },
            { text: "REST 接口", link: "/skills/agent-kit-sdk/docs/REST接口" },
            {
              text: "WebSocket 接口",
              link: "/skills/agent-kit-sdk/docs/WebSocket接口",
            },
            { text: "核心类型", link: "/skills/agent-kit-sdk/docs/核心类型" },
            {
              text: "会话生命周期",
              link: "/skills/agent-kit-sdk/docs/会话生命周期",
            },
            { text: "Chat 流程", link: "/skills/agent-kit-sdk/docs/Chat流程" },
          ],
        },
        {
          text: "API Protocol (English)",
          collapsed: true,
          items: [
            {
              text: "API Overview",
              link: "/skills/agent-kit-sdk/docs/api-overview",
            },
            {
              text: "REST API",
              link: "/skills/agent-kit-sdk/docs/rest-api",
            },
            {
              text: "WebSocket API",
              link: "/skills/agent-kit-sdk/docs/websocket-api",
            },
            {
              text: "Core Types",
              link: "/skills/agent-kit-sdk/docs/core-types",
            },
            {
              text: "Session Lifecycle",
              link: "/skills/agent-kit-sdk/docs/session-lifecycle",
            },
            {
              text: "Chat Flow",
              link: "/skills/agent-kit-sdk/docs/chat-flow",
            },
          ],
        },
        {
          text: "SDK 集成指南",
          items: [
            {
              text: "鉴权与 Token",
              link: "/skills/agent-kit-sdk/references/auth-token",
            },
            {
              text: "SDK 入口与安装",
              link: "/skills/agent-kit-sdk/references/sdk-entrypoints",
            },
            {
              text: "聊天 UI 与自渲染",
              link: "/skills/agent-kit-sdk/references/chat-ui",
            },
            {
              text: "会话与运行时",
              link: "/skills/agent-kit-sdk/references/session-runtime",
            },
            {
              text: "事件与数据结构",
              link: "/skills/agent-kit-sdk/references/events-and-types",
            },
            {
              text: "后端集成",
              link: "/skills/agent-kit-sdk/references/backend",
            },
            {
              text: "工作模式",
              link: "/skills/agent-kit-sdk/references/work-modes",
            },
            {
              text: "文件上传",
              link: "/skills/agent-kit-sdk/references/file-upload",
            },
            {
              text: "宿主页面联动",
              link: "/skills/agent-kit-sdk/references/host-app-integration",
            },
            {
              text: "Session Skill 上传",
              link: "/skills/agent-kit-sdk/references/session-skill-upload",
            },
            {
              text: "故障排查",
              link: "/skills/agent-kit-sdk/references/troubleshooting",
            },
          ],
        },
        {
          text: "AI Skill 导航",
          collapsed: true,
          items: [
            {
              text: "SKILL.md（AI 路由）",
              link: "/skills/agent-kit-sdk/SKILL",
            },
          ],
        },
      ],
      "/skills/solution-structure/": [
        {
          text: "Solution 结构",
          items: [
            {
              text: "规范说明",
              link: "/skills/solution-structure/SKILL",
            },
          ],
        },
      ],
      "/skills/sandbox-image-customizer/": [
        {
          text: "沙箱镜像定制",
          items: [
            {
              text: "操作指南",
              link: "/skills/sandbox-image-customizer/SKILL",
            },
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

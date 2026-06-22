import { defineConfig } from "vitepress";
import { createWriteStream } from "node:fs";
import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { ZipArchive } from "archiver";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const docRoot = path.resolve(__dirname, "..");

// 打进 skills.zip 的文档目录（剔除 .vitepress / lock / node_modules 等噪音）
const DOC_DIRS = ["guide", "agent-dev", "integration", "api", "ops", "skills"];

const base = process.env.VITEPRESS_BASE || "/public-skills/";

const integrationSidebar = [
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
      { text: "外部服务接入", link: "/integration/capabilities/external-services" },
    ],
  },
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
  {
    text: "调试与排查",
    items: [
      { text: "调试指南", link: "/integration/debugging" },
    ],
  },
];

const sidebar = {
  "/guide/": [
    {
      text: "使用指南",
      items: [
        { text: "快速开始", link: "/guide/getting-started" },
        { text: "Blade OS 桌面", link: "/guide/blade-os" },
        { text: "解决方案与角色", link: "/guide/solutions-and-roles" },
        { text: "云电脑", link: "/guide/cloud-computer" },
        { text: "软件工厂", link: "/guide/factory" },
        {
          text: "智能助手",
          collapsed: true,
          items: [
            { text: "对话与交互", link: "/guide/chat" },
            { text: "会话管理", link: "/guide/sessions" },
            { text: "记忆功能", link: "/guide/memory" },
            { text: "定时任务", link: "/guide/scheduled-tasks" },
            { text: "浏览器插件", link: "/guide/browser-extension" },
          ],
        },
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
        { text: "解决方案应用", link: "/agent-dev/solution/app" },
        { text: "校验工具", link: "/agent-dev/solution/validation" },
      ],
    },
    {
      text: "技能开发（Skill）",
      items: [
        { text: "SKILL.md 编写规范", link: "/agent-dev/skill/skill-md" },
        { text: "技能注册中心", link: "/agent-dev/skill/registry" },
        { text: "发布与版本管理", link: "/agent-dev/skill/publish" },
        { text: "内置系统工具", link: "/agent-dev/skill/tools" },
      ],
    },
    {
      text: "调试与排查",
      items: [
        { text: "调试指南", link: "/agent-dev/debugging" },
      ],
    },
  ],
  "/integration/": integrationSidebar,
  "/api/": integrationSidebar,
  "/ops/": [
    {
      text: "部署与运维",
      items: [
        { text: "Docker 部署", link: "/ops/docker" },
        { text: "Blade OAuth", link: "/ops/oauth" },
        { text: "LLM Gateway 配置", link: "/ops/llm-gateway" },
        { text: "沙箱镜像定制", link: "/ops/sandbox" },
        { text: "环境变量参考", link: "/ops/env" },
        { text: "监控与观测", link: "/ops/monitoring" },
        { text: "安全与加密", link: "/ops/security" },
      ],
    },
  ],
};

// 把 sidebar 数据展开成 llms.txt 的纯文本索引，链接指向真实 .html 路径
function buildLlmsTxt(): string {
  const lines: string[] = [
    "# Blade OS 帮助文档",
    "",
    "> 使用入门、智能体开发、应用接入、部署运维。本文件为 AI 智能体提供全站索引。",
    "",
    `需要完整内容时，下载本站 \`${base}skills.zip\`，解压后用 Grep/Read 按需查阅，避免整包读入上下文。`,
    "",
  ];

  const emitItems = (items: any[], indent: string) => {
    for (const it of items) {
      if (it.link) {
        const href = `${base}${it.link.replace(/^\//, "")}.html`;
        lines.push(`${indent}- [${it.text}](${href})`);
      } else if (it.items) {
        lines.push(`${indent}- ${it.text}`);
      }
      if (it.items) emitItems(it.items, indent + "  ");
    }
  };

  const seenGroups = new Set<string>();
  for (const groups of Object.values(sidebar)) {
    for (const group of groups as any[]) {
      if (seenGroups.has(group.text)) continue;
      seenGroups.add(group.text);
      lines.push(`## ${group.text}`);
      lines.push("");
      emitItems(group.items, "");
      lines.push("");
    }
  }

  return lines.join("\n");
}

// 把文档源 md 打包成 skills.zip，写进构建产物根目录（与站点同源部署，断网可下载）
function buildSkillsZip(outDir: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const output = createWriteStream(path.join(outDir, "skills.zip"));
    const archive = new ZipArchive({ zlib: { level: 9 } });
    output.on("close", () => resolve());
    archive.on("error", reject);
    archive.pipe(output);

    archive.file(path.join(docRoot, "index.md"), { name: "index.md" });
    for (const dir of DOC_DIRS) {
      archive.glob(
        "**/*.md",
        { cwd: path.join(docRoot, dir), ignore: ["**/node_modules/**"] },
        { prefix: dir },
      );
    }
    archive.finalize();
  });
}

export default defineConfig({
  title: "Blade OS 帮助文档",
  description: "使用入门、智能体开发、应用接入、部署运维",
  lang: "zh-CN",
  base,

  vite: { server: { strictPort: true } },
  srcExclude: ["**/node_modules/**", "**/examples/**", "skills/**"],
  ignoreDeadLinks: true,

  markdown: {
    math: false,
  },

  async buildEnd(siteConfig) {
    await buildSkillsZip(siteConfig.outDir);
    await writeFile(path.join(siteConfig.outDir, "llms.txt"), buildLlmsTxt());
  },

  themeConfig: {
    nav: [
      { text: "使用指南", link: "/guide/getting-started" },
      { text: "智能体开发", link: "/agent-dev/concepts" },
      { text: "应用接入", link: "/integration/concepts" },
      { text: "部署与运维", link: "/ops/docker" },
      {
        text: "v0.5.16",
        items: [
          { text: "v0.5.16（当前）", link: "/" },
        ],
      },
    ],

    sidebar,

    search: { provider: "local" },
    outline: { level: [2, 3], label: "目录" },
    docFooter: { prev: "上一页", next: "下一页" },
    lastUpdated: { text: "最后更新" },
    returnToTopLabel: "返回顶部",
    sidebarMenuLabel: "菜单",
    darkModeSwitchLabel: "主题",
  },
});

import type { ContentBlock, ToolCall } from "../composables/useBladeChat"

/** 从 blocks 中提取纯文本 */
export function extractText(blocks: ContentBlock[]): string {
  return blocks
    .filter((b) => b.type === "text")
    .map((b) => String(b.content ?? ""))
    .join("")
}

/**
 * 格式化 JSON 用于展示。
 * arguments 是 JSON 字符串 —— parse 后再 stringify 可以：
 * 1. 美化缩进
 * 2. 把 \uXXXX 转义还原成中文（JS JSON.stringify 默认不转义非 ASCII）
 */
export function prettyJson(value: unknown): string {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2)
    } catch {
      return value
    }
  }
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function isAskUserQuestionTool(call: ToolCall): boolean {
  return call.tool_name.includes("AskUserQuestion")
}

export function isAgentTool(call: ToolCall): boolean {
  const n = call.tool_name.toLowerCase()
  return n.includes("agent") || n.includes("fork")
}

export function statusColor(status: string): string {
  switch (status) {
    case "done":
      return "bg-green-600"
    case "error":
      return "bg-red-600"
    case "cancelled":
      return "bg-gray-500"
    case "awaiting_answer":
      return "bg-amber-500"
    default:
      return "bg-blue-500"
  }
}

export function statusText(status: string): string {
  switch (status) {
    case "pending":
      return "运行中"
    case "done":
      return "完成"
    case "error":
      return "错误"
    case "cancelled":
      return "已取消"
    case "awaiting_answer":
      return "等待回答"
    default:
      return status
  }
}

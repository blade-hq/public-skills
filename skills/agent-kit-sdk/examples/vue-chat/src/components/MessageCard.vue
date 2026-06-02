<script setup lang="ts">
import { computed } from "vue"
import type { Turn, useBladeChat } from "../composables/useBladeChat"
import ToolCallCard from "./ToolCallCard.vue"
import AskUserQuestion from "./AskUserQuestion.vue"
import AgentLoop from "./AgentLoop.vue"
import { extractText, isAgentTool, isAskUserQuestionTool } from "./utils"

const props = defineProps<{ turn: Turn; chat: ReturnType<typeof useBladeChat> }>()

const text = computed(() => extractText(props.turn.blocks))
const thinking = computed(() => {
  const block = props.turn.blocks.find((b) => b.type === "thinking")
  return typeof block?.content === "string" ? block.content.trim() : ""
})
const isUser = computed(() => props.turn.role === "user")
// ask_user_answer / mode_change 等纯系统 turn 不需要渲染
const isSystemOnly = computed(() => {
  const types = new Set(props.turn.blocks.map((b) => b.type))
  types.delete("ask_user_answer")
  types.delete("mode_change")
  types.delete("planning_enter")
  types.delete("planning_exit")
  return types.size === 0 && props.turn.tool_calls.length === 0
})
const statusLabel = computed(() => {
  const s = props.turn.status
  if (s === "streaming") return "输出中..."
  if (s === "failed") return "失败"
  if (s === "interrupted") return "已中断"
  return ""
})
</script>

<template>
  <article
    v-if="!isSystemOnly"
    class="rounded-lg border p-3 text-sm"
    :class="isUser ? 'ml-auto max-w-[80%] bg-blue-50' : 'mr-auto max-w-[90%] bg-white'"
  >
    <!-- 角色 + 状态 -->
    <div class="mb-1 text-[10px] font-medium uppercase text-gray-400">
      {{ turn.role }}
      <span v-if="statusLabel" class="ml-1 text-amber-500">{{ statusLabel }}</span>
    </div>

    <!-- 思考过程（折叠） -->
    <details v-if="thinking" class="mb-2 rounded border border-gray-200 px-2 py-1">
      <summary class="cursor-pointer text-xs font-medium text-gray-500">思考过程</summary>
      <pre class="mt-1 whitespace-pre-wrap font-sans text-xs text-gray-600">{{ thinking }}</pre>
    </details>

    <!-- 正文 -->
    <pre v-if="text" class="whitespace-pre-wrap font-sans">{{ text }}</pre>

    <!-- 工具调用 -->
    <template v-for="call in turn.tool_calls" :key="call.id">
      <!-- AskUserQuestion -->
      <AskUserQuestion
        v-if="isAskUserQuestionTool(call)"
        :tool-call="call"
        :chat="props.chat"
      />
      <!-- 子智能体 -->
      <AgentLoop
        v-else-if="isAgentTool(call)"
        :tool-call="call"
        :chat="props.chat"
      />
      <!-- 普通工具 -->
      <ToolCallCard v-else :tool-call="call" />
    </template>

    <!-- 兜底：既无文本也无工具调用时显示原始数据 -->
    <pre
      v-if="!text && !thinking && turn.tool_calls.length === 0"
      class="overflow-x-auto whitespace-pre-wrap text-[10px] text-gray-400"
    >{{ JSON.stringify({ blocks: turn.blocks }, null, 2) }}</pre>
  </article>
</template>

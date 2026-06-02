<script setup lang="ts">
import { computed, ref } from "vue"
import type { ToolCall, useBladeChat } from "../composables/useBladeChat"
import MessageCard from "./MessageCard.vue"
import { prettyJson, statusColor, statusText } from "./utils"

const props = defineProps<{
  toolCall: ToolCall
  chat: ReturnType<typeof useBladeChat>
}>()

const expanded = ref(false)
const autoExpand = computed(() => props.toolCall.status === "awaiting_answer")

const childTurns = computed(() => props.chat.childTurns(props.toolCall.id))

const description = computed(() => {
  try {
    const args = JSON.parse(props.toolCall.arguments)
    return args.description || args.prompt || ""
  } catch {
    return ""
  }
})

const result = computed(() =>
  props.toolCall.result != null && props.toolCall.result !== ""
    ? prettyJson(props.toolCall.result)
    : "",
)
</script>

<template>
  <div class="mt-2 rounded border border-purple-300 bg-purple-50 px-2 py-1.5">
    <!-- 头部：点击展开/折叠 -->
    <div
      class="flex cursor-pointer items-center gap-2"
      @click="expanded = !expanded"
    >
      <span class="text-xs text-purple-500">{{ expanded || autoExpand ? "▼" : "▶" }}</span>
      <span class="rounded bg-purple-600 px-1.5 py-0.5 text-[10px] font-medium text-white">
        子智能体
      </span>
      <span
        class="rounded px-1.5 py-0.5 text-[10px] font-medium text-white"
        :class="statusColor(toolCall.status)"
      >
        {{ statusText(toolCall.status) }}
      </span>
      <span v-if="toolCall.duration_ms != null" class="text-[10px] text-gray-400">
        {{ toolCall.duration_ms }}ms
      </span>
    </div>

    <!-- 描述 -->
    <div v-if="description" class="mt-1 text-xs text-gray-600">{{ description }}</div>

    <!-- 展开时：子 turn 列表 -->
    <div v-if="expanded || autoExpand" class="mt-2 space-y-2 border-l-2 border-purple-200 pl-2">
      <p v-if="childTurns.length === 0" class="text-xs text-gray-400">
        {{ toolCall.status === "pending" ? "子智能体运行中..." : "无子消息" }}
      </p>
      <MessageCard
        v-for="child in childTurns"
        :key="child.turn_id"
        :turn="child"
        :chat="chat"
      />
    </div>

    <!-- 折叠时：简略结果 -->
    <div v-if="!expanded && !autoExpand && result" class="mt-1">
      <pre class="max-h-24 overflow-auto whitespace-pre-wrap text-xs text-gray-500">{{ result }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import type { ToolCall } from "../composables/useBladeChat"
import { prettyJson, statusColor, statusText } from "./utils"

const props = defineProps<{ toolCall: ToolCall }>()

const name = computed(() => props.toolCall.display_name || props.toolCall.tool_name)
const args = computed(() => prettyJson(props.toolCall.arguments))
const result = computed(() =>
  props.toolCall.result != null && props.toolCall.result !== ""
    ? prettyJson(props.toolCall.result)
    : "",
)
</script>

<template>
  <div class="mt-2 rounded border bg-gray-50 px-2 py-1.5">
    <!-- 工具名 + 状态 + 耗时 -->
    <div class="flex flex-wrap items-center gap-2">
      <span class="rounded bg-gray-700 px-1.5 py-0.5 text-[10px] font-medium text-white">
        {{ name }}
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

    <!-- 参数 -->
    <div v-if="args" class="mt-1">
      <div class="text-[10px] font-medium text-gray-400">参数</div>
      <pre class="overflow-x-auto whitespace-pre-wrap text-xs">{{ args }}</pre>
    </div>

    <!-- 结果 -->
    <div v-if="result" class="mt-1">
      <div class="text-[10px] font-medium text-gray-400">结果</div>
      <pre class="max-h-48 overflow-auto whitespace-pre-wrap text-xs">{{ result }}</pre>
    </div>
  </div>
</template>

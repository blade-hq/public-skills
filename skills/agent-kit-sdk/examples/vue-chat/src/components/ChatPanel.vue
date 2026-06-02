<script setup lang="ts">
import { ref, nextTick, watch } from "vue"
import type { useBladeChat } from "../composables/useBladeChat"
import MessageCard from "./MessageCard.vue"

const props = defineProps<{ chat: ReturnType<typeof useBladeChat> }>()

const draft = ref("")
const listEl = ref<HTMLElement>()

function handleSend() {
  const text = draft.value.trim()
  if (!text || props.chat.streaming.value) return
  props.chat.send(text)
  draft.value = ""
}

watch(
  () => props.chat.turns.value.length,
  () => nextTick(() => listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: "smooth" })),
)
</script>

<template>
  <div class="flex flex-col overflow-hidden rounded-lg border bg-white">
    <!-- 消息列表 -->
    <div ref="listEl" class="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
      <p v-if="chat.rootTurns().length === 0 && !chat.streaming.value" class="text-sm text-gray-400">
        发送消息开始对话
      </p>
      <MessageCard
        v-for="turn in chat.rootTurns()"
        :key="turn.turn_id"
        :turn="turn"
        :chat="chat"
      />
      <div v-if="chat.error.value" class="rounded bg-red-50 p-2 text-xs text-red-600">
        {{ chat.error.value }}
      </div>
    </div>

    <!-- 输入区 -->
    <div class="border-t p-3">
      <textarea
        v-model="draft"
        class="min-h-20 w-full resize-none rounded border bg-gray-50 p-2 text-sm outline-none focus:ring-2 focus:ring-blue-400"
        placeholder="输入消息，Ctrl+Enter 发送..."
        @keydown.ctrl.enter="handleSend"
        @keydown.meta.enter="handleSend"
      />
      <div class="mt-2 flex justify-end gap-2">
        <button
          class="rounded border px-3 py-1 text-sm disabled:opacity-40"
          :disabled="!chat.streaming.value"
          @click="chat.stop()"
        >
          停止
        </button>
        <button
          class="rounded bg-blue-600 px-3 py-1 text-sm text-white disabled:opacity-40"
          :disabled="!draft.trim() || chat.streaming.value"
          @click="handleSend"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

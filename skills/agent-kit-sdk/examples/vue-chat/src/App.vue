<script setup lang="ts">
import { ref, onUnmounted } from "vue"
import { BladeClient } from "@blade-hq/agent-kit/client"
import ChatPanel from "./components/ChatPanel.vue"
import { useBladeChat } from "./composables/useBladeChat"

const token = (((import.meta as any).env.VITE_BLADE_AGENT_TOKEN as string) ?? "").trim()
const client = new BladeClient({ baseUrl: window.location.origin, token: () => token })
const chat = useBladeChat(client)
const ready = ref(false)
const initError = ref("")

async function init() {
  if (!token) {
    initError.value = "缺少 VITE_BLADE_AGENT_TOKEN，请在 .env 中配置"
    return
  }
  try {
    await chat.createSession("vue chat example")
    ready.value = true
  } catch (e: any) {
    initError.value = e?.message ?? "创建会话失败"
  }
}

init()
onUnmounted(() => chat.destroy())
</script>

<template>
  <div class="mx-auto flex h-screen max-w-3xl flex-col p-4">
    <header class="mb-3 flex items-center justify-between">
      <h1 class="text-lg font-semibold">Vue Chat Example</h1>
      <span v-if="chat.sessionId.value" class="text-xs text-gray-400">
        {{ chat.sessionId.value.slice(0, 8) }}
      </span>
    </header>

    <div v-if="initError" class="rounded bg-red-50 p-4 text-sm text-red-700">{{ initError }}</div>

    <ChatPanel v-else-if="ready" :chat="chat" class="min-h-0 flex-1" />

    <div v-else class="flex flex-1 items-center justify-center text-sm text-gray-400">
      正在创建会话...
    </div>
  </div>
</template>

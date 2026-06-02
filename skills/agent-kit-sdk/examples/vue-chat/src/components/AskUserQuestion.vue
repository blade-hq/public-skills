<script setup lang="ts">
import { ref, computed, reactive } from "vue"
import type { ToolCall, AskUserQuestionData, AskUserAnswerData, useBladeChat } from "../composables/useBladeChat"

const props = defineProps<{
  toolCall: ToolCall
  chat: ReturnType<typeof useBladeChat>
}>()

const awaiting = computed(() => props.toolCall.status === "awaiting_answer")
const submitted = ref(false)

const questionData = computed<AskUserQuestionData | null>(() => {
  try {
    return JSON.parse(props.toolCall.arguments)
  } catch {
    return null
  }
})

// 每个问题的选中项（question index → Set of option indices）
const selections = reactive(new Map<number, Set<number>>())
// 每个问题的自定义文本
const customTexts = reactive(new Map<number, string>())

function toggleOption(qIdx: number, oIdx: number, multi: boolean) {
  if (!awaiting.value || submitted.value) return
  if (!selections.has(qIdx)) selections.set(qIdx, new Set())
  const set = selections.get(qIdx)!
  if (multi) {
    set.has(oIdx) ? set.delete(oIdx) : set.add(oIdx)
  } else {
    set.clear()
    set.add(oIdx)
  }
}

function allAnswered(): boolean {
  if (!questionData.value) return false
  return questionData.value.questions.every((_, i) => {
    const sel = selections.get(i)
    const custom = customTexts.get(i)?.trim()
    return (sel && sel.size > 0) || !!custom
  })
}

function submit() {
  if (!questionData.value || !allAnswered()) return

  const answer: AskUserAnswerData = { selections: {}, custom: {} }
  const textParts: string[] = []

  questionData.value.questions.forEach((q, i) => {
    const sel = selections.get(i)
    const custom = customTexts.get(i)?.trim()
    if (sel && sel.size > 0) {
      answer.selections[i] = [...sel]
      const labels = [...sel].map((oi) => q.options[oi]?.label ?? `选项${oi}`)
      textParts.push(`- ${q.question} -> ${labels.join(", ")}`)
    }
    if (custom) {
      answer.custom[i] = custom
      if (!sel || sel.size === 0) textParts.push(`- ${q.question} -> ${custom}`)
    }
  })

  const message = `用户的回答如下：\n${textParts.join("\n")}`
  props.chat.send(message, { tool_call_id: props.toolCall.id, ...answer })
  submitted.value = true
}
</script>

<template>
  <div class="mt-2 rounded border border-amber-300 bg-amber-50 px-3 py-2">
    <div class="mb-2 text-xs font-semibold text-amber-700">需要你的回答</div>

    <template v-if="questionData">
      <div v-for="(q, qi) in questionData.questions" :key="qi" class="mb-3 last:mb-0">
        <div class="mb-1 text-sm font-medium">{{ q.question }}</div>

        <!-- 选项 -->
        <div class="flex flex-wrap gap-2">
          <button
            v-for="(opt, oi) in q.options"
            :key="oi"
            class="rounded border px-2 py-1 text-xs transition"
            :class="
              selections.get(qi)?.has(oi)
                ? 'border-blue-500 bg-blue-100 text-blue-700'
                : 'border-gray-300 bg-white hover:bg-gray-100'
            "
            :disabled="!awaiting || submitted"
            @click="toggleOption(qi, oi, !!q.multiSelect)"
          >
            <span class="font-medium">{{ opt.label }}</span>
            <span v-if="opt.description" class="ml-1 text-gray-500">{{ opt.description }}</span>
          </button>
        </div>

        <!-- 自定义输入（"其他"） -->
        <input
          :value="customTexts.get(qi) ?? ''"
          class="mt-1 w-full rounded border px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-blue-400"
          placeholder="或输入自定义回答..."
          :disabled="!awaiting || submitted"
          @input="customTexts.set(qi, ($event.target as HTMLInputElement).value)"
        />
      </div>
    </template>

    <!-- 无法解析参数时的兜底 -->
    <pre v-else class="text-xs text-gray-500">{{ toolCall.arguments }}</pre>

    <!-- 提交按钮 -->
    <button
      v-if="awaiting && !submitted"
      class="mt-2 rounded bg-amber-600 px-3 py-1 text-xs text-white disabled:opacity-40"
      :disabled="!allAnswered()"
      @click="submit"
    >
      确认
    </button>
    <div v-else-if="submitted" class="mt-1 text-[10px] text-gray-400">已提交</div>
    <div v-else-if="toolCall.status === 'done'" class="mt-1 text-[10px] text-green-600">已回答</div>
  </div>
</template>

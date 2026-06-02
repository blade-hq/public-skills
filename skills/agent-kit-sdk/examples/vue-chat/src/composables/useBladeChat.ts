import { ref, shallowRef, readonly, triggerRef } from "vue"
import { BladeClient } from "@blade-hq/agent-kit/client"

// SDK 导出的投影类型；Vue 只读取不写入，用 any 兜底亦可
export interface Turn {
  turn_id: string
  role: "user" | "assistant" | "system"
  status: string
  blocks: ContentBlock[]
  tool_calls: ToolCall[]
  loop_id?: string
  parent_fork_tool_call_id?: string | null
  duration_ms?: number
  model?: string | null
}

export interface ContentBlock {
  type: string
  content: unknown
  tool_call_id?: string | null
  tool_name?: string | null
  display_name?: string | null
}

export interface ToolCall {
  id: string
  tool_name: string
  display_name: string
  arguments: string // JSON 字符串
  status: "pending" | "done" | "error" | "cancelled" | "awaiting_answer"
  result?: unknown
  duration_ms?: number | null
  pending_question_ref?: {
    child_loop_name: string
    child_tool_call_id: string
    description?: string | null
  } | null
}

export interface AskUserQuestionData {
  questions: {
    question: string
    header?: string
    options: { label: string; description: string }[]
    multiSelect?: boolean
  }[]
  source_loop?: { loop_name: string; description: string } | null
}

export interface AskUserAnswerData {
  selections: Record<number, number[]>
  custom: Record<number, string>
}

/**
 * 管理一个 Blade Agent 会话的响应式状态。
 *
 * 用法：
 *   const chat = useBladeChat(client)
 *   await chat.createSession("你好")
 *   chat.send("帮我分析一下")
 */
export function useBladeChat(client: BladeClient) {
  const sessionId = ref("")
  const turns = shallowRef<Turn[]>([])
  const streaming = ref(false)
  const error = ref("")

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let socket: any = null

  function upsertTurn(turn: Turn) {
    const list = [...turns.value]
    const idx = list.findIndex((t) => t.turn_id === turn.turn_id)
    if (idx >= 0) list[idx] = turn
    else list.push(turn)
    turns.value = list
    triggerRef(turns)
  }

  async function createSession(intent: string) {
    const { session_id } = await client.sessions.createSession(intent)
    sessionId.value = session_id

    socket = client.socket()

    socket.on("turn:start", (p: Turn) => {
      upsertTurn(p)
      streaming.value = true
    })

    // turn:patch 的 data.turn 带完整 turn 快照（patch_type "sync"），直接替换即可实现流式
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    socket.on("turn:patch", (p: any) => {
      if (p?.data?.turn) upsertTurn(p.data.turn)
    })

    socket.on("turn:end", (p: Turn) => {
      upsertTurn(p)
    })

    // chat:end 时用 REST 刷一次，保证最终状态完整
    socket.on("chat:end", async () => {
      streaming.value = false
      try {
        const fresh = await client.sessions.getSessionTurns(session_id)
        turns.value = fresh as Turn[]
        triggerRef(turns)
      } catch {
        // 刷新失败不影响已有数据
      }
    })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    socket.on("system:error", (p: any) => {
      error.value = p?.message ?? "未知错误"
      streaming.value = false
    })

    socket.connect()
    socket.emit("session:subscribe", { session_id })
  }

  function send(message: string, askuserAnswer?: { tool_call_id: string } & AskUserAnswerData) {
    if (!socket || !sessionId.value) return
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const payload: any = { session_id: sessionId.value, message }
    if (askuserAnswer) payload.askuser_answer = askuserAnswer
    socket.emit("chat:send", payload)
    streaming.value = true
    error.value = ""
  }

  function stop() {
    if (!socket || !sessionId.value) return
    socket.emit("chat:stop", { session_id: sessionId.value })
  }

  function destroy() {
    if (socket) {
      if (sessionId.value) socket.emit("session:unsubscribe", { session_id: sessionId.value })
      socket.disconnect()
      socket = null
    }
  }

  /** 只返回顶层 turn（不含子智能体的 turn） */
  function rootTurns() {
    return turns.value.filter((t) => !t.parent_fork_tool_call_id)
  }

  /** 查找属于某个 Agent 工具调用的子 turn */
  function childTurns(parentToolCallId: string) {
    return turns.value.filter((t) => t.parent_fork_tool_call_id === parentToolCallId)
  }

  return {
    sessionId: readonly(sessionId),
    turns: readonly(turns),
    streaming: readonly(streaming),
    error: readonly(error),
    createSession,
    send,
    stop,
    destroy,
    rootTurns,
    childTurns,
  }
}

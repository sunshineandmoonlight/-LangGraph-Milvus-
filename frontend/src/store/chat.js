import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { executeAgent, getAgentStatus } from '@/api'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref([])
  const currentSessionId = ref(null)
  const isExecuting = ref(false)
  const executionStatus = ref(null)

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)

  // 添加用户消息
  const addUserMessage = (content) => {
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })
  }

  // 添加 Assistant 消息
  const addAssistantMessage = (content, agentType = 'assistant') => {
    messages.value.push({
      role: 'assistant',
      agent_type: agentType,
      content,
      timestamp: new Date().toISOString()
    })
  }

  // 添加系统消息
  const addSystemMessage = (content) => {
    messages.value.push({
      role: 'system',
      content,
      timestamp: new Date().toISOString()
    })
  }

  // 执行 Agent 任务
  const execute = async (query) => {
    if (isExecuting.value) {
      return
    }

    try {
      isExecuting.value = true
      addUserMessage(query)
      addSystemMessage('正在启动 Multi-Agent 系统...')

      const response = await executeAgent(query, currentSessionId.value)

      // 更新会话 ID
      if (response.session_id) {
        currentSessionId.value = response.session_id
      }

      // 处理执行结果
      if (response.final_answer) {
        addAssistantMessage(response.final_answer, 'supervisor')
      }

      // 更新执行状态
      if (response.execution_trace) {
        executionStatus.value = response.execution_trace
      }

      return response
    } catch (error) {
      addSystemMessage(`执行失败: ${error.message}`)
      throw error
    } finally {
      isExecuting.value = false
    }
  }

  // 轮询获取 Agent 状态
  const pollStatus = async (threadId, callback) => {
    const interval = setInterval(async () => {
      try {
        const status = await getAgentStatus(threadId)
        callback(status)

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval)
        }
      } catch (error) {
        clearInterval(interval)
        throw error
      }
    }, 2000) // 每 2 秒轮询一次

    return interval
  }

  // 清空消息
  const clearMessages = () => {
    messages.value = []
    currentSessionId.value = null
    executionStatus.value = null
  }

  return {
    // 状态
    messages,
    currentSessionId,
    isExecuting,
    executionStatus,
    // 计算属性
    hasMessages,
    // 方法
    addUserMessage,
    addAssistantMessage,
    addSystemMessage,
    execute,
    pollStatus,
    clearMessages
  }
})

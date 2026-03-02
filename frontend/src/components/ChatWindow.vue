<template>
  <div class="chat-window flex-1 flex flex-col bg-dark-bg" :class="{ 'has-sources-panel': chatMode === 'agent' && sources.length > 0 && sourcesPanelOpen }">
    <!-- Header -->
    <div class="glassmorphism border-b border-dark-border px-4 py-3">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="min-w-max">
          <h2 class="text-base font-semibold text-white">对话</h2>
          <p class="text-xs text-dark-muted">AI 多智能体协作系统</p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <el-button size="small" @click="conversationDialogVisible = true" :disabled="conversations.length === 0">
            <el-icon class="mr-1"><Clock /></el-icon>
            会话历史 ({{ conversations.length }})
          </el-button>
          <el-button size="small" @click="newChat">
            <el-icon class="mr-1"><Plus /></el-icon>
            新对话
          </el-button>

          <!-- 模式选择 -->
          <el-radio-group v-model="chatMode" size="small">
            <el-radio-button label="agent">多智能体</el-radio-button>
            <el-radio-button label="rag">RAG</el-radio-button>
            <el-radio-button label="normal">普通</el-radio-button>
          </el-radio-group>

          <div class="flex items-center gap-2 px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs whitespace-nowrap">
            <div class="w-2 h-2 rounded-full bg-green-500"></div>
            在线
          </div>
        </div>
      </div>
    </div>

    <!-- Messages Area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
      <!-- Thought Process -->
      <ThoughtProcess v-if="thoughtSteps.length > 0" :steps="thoughtSteps" />

      <!-- Messages -->
      <transition-group name="fade">
        <div
          v-for="message in messages"
          :key="message.id"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div class="message-bubble" :class="message.role === 'user' ? 'message-user' : 'message-ai'">
            <div v-if="message.role === 'assistant'" class="prose prose-invert max-w-full overflow-x-auto" v-html="renderMarkdown(message.content)"></div>
            <p v-else class="text-sm whitespace-pre-wrap">{{ message.content }}</p>
            <p class="text-xs opacity-50 mt-2">{{ message.timestamp }}</p>
          </div>
        </div>
      </transition-group>

      <!-- Loading Indicator -->
      <div v-if="isTyping" class="flex justify-start">
        <div class="message-bubble message-ai flex items-center gap-2">
          <div class="spinner text-primary-500"></div>
          <span class="text-sm text-dark-muted">AI 正在思考...</span>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="glassmorphism border-t border-dark-border p-3 flex-shrink-0">
      <div class="flex gap-2">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="1"
          placeholder="输入您的问题... (Shift + Enter 换行)"
          @keydown.enter.prevent="handleEnter"
          class="flex-1"
        />
        <el-button type="primary" :loading="isLoading" :disabled="!inputMessage.trim()" @click="sendMessage">
          发送
        </el-button>
      </div>

      <!-- Quick Actions -->
      <div class="flex gap-2 mt-3">
        <el-button v-for="action in quickActions" :key="action.label" size="small" @click="quickSend(action.query)">
          {{ action.label }}
        </el-button>
      </div>
    </div>

    <!-- Conversation History Dialog -->
    <el-dialog v-model="conversationDialogVisible" title="会话历史" width="70%" :close-on-click-modal="false">
      <div v-if="conversations.length === 0" class="text-center py-8 text-dark-muted">
        暂无会话历史
      </div>
      <div v-else class="space-y-3 max-h-[60vh] overflow-y-auto">
        <div
          v-for="conv in conversations"
          :key="conv.session_id"
          class="p-4 rounded-lg border transition-colors cursor-pointer"
          :class="conv.session_id === currentConversationId ? 'bg-primary-500/20 border-primary-500' : 'bg-dark-bg border-dark-border hover:border-primary-500'"
          @click="switchConversation(conv.session_id)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <h3 class="font-semibold text-white">{{ conv.title }}</h3>
                <el-tag v-if="conv.session_id === currentConversationId" size="small" type="success">当前</el-tag>
              </div>
              <p class="text-xs text-dark-muted mb-2">
                创建时间: {{ new Date(conv.createdAt).toLocaleString('zh-CN') }}
              </p>
              <p class="text-xs text-dark-muted">
                消息数量: {{ conv.messages.length }}
              </p>
            </div>
            <el-button
              text
              size="small"
              class="text-red-400 hover:text-red-500 hover:bg-red-500/10"
              @click.stop="deleteConversation(conv.session_id)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="conversationDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Sources Panel -->
    <SourcesPanel
      v-if="chatMode === 'agent' && sources.length > 0"
      ref="sourcesPanelRef"
      :sources="sources"
      :key="sources.length"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { ElNotification, ElMessageBox } from 'element-plus'
import { Clock, Plus, Delete } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import ThoughtProcess from './ThoughtProcess.vue'
import SourcesPanel from './SourcesPanel.vue'
import { getSessions, getSession, deleteSession as deleteSessionApi, executeAgent } from '../api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface Settings {
  apiUrl: string
  timeout: number
  maxTokens: number
  temperature: number
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
}

const messagesContainer = ref<HTMLElement>()
const inputMessage = ref('')
const messages = ref<Message[]>([])
const isTyping = ref(false)
const isLoading = ref(false)
const thoughtSteps = ref<Array<{ agent: string; action: string; status: string }>>([])
const sources = ref<Array<{ title: string; url: string; snippet: string }>>([])
const settings = ref<Settings>({
  apiUrl: '',  // 使用空字符串，让 Vite proxy 处理
  timeout: 300,  // 增加到5分钟（300秒），适合多智能体模式
  maxTokens: 2000,
  temperature: 0.7
})

// 多会话管理
const conversations = ref<Conversation[]>([])
const currentConversationId = ref<string>('')
const conversationDialogVisible = ref(false)

// 聊天模式: agent(多智能体), rag(仅知识库), normal(普通对话)
const chatMode = ref<'agent' | 'rag' | 'normal'>('agent')

// Sources Panel 状态
const sourcesPanelRef = ref<{ isOpen?: { value: boolean } } | null>(null)
const sourcesPanelOpen = ref(true)

// 监听 Sources Panel 状态变化
watch(() => sourcesPanelRef.value?.isOpen, (isOpen) => {
  if (isOpen !== undefined) {
    sourcesPanelOpen.value = isOpen.value
  }
}, { immediate: true })

// 流式输出开关（仅在多智能体模式有效）
const useStreaming = ref(false)  // 暂时禁用流式输出以测试

const md = MarkdownIt({
  highlight: (str: string, lang: string) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  },
  // 配置链接默认在新标签页打开
  html: false,
  linkify: true,
  typographer: true
})

// 自定义链接渲染，确保所有链接都在新标签页打开
const defaultLinkOpen = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  // 添加 target="_blank" 和 rel="noopener noreferrer"
  const token = tokens[idx]
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}

const quickActions = [
  { label: '介绍一下最近新闻', query: '请介绍一下最近的新闻动态' },
  { label: '什么是机器学习？', query: '什么是机器学习？' }
]

// 加载设置和会话历史
onMounted(async () => {
  const savedSettings = localStorage.getItem('settings')
  if (savedSettings) {
    settings.value = JSON.parse(savedSettings)
  }

  // 检查用户是否已登录
  const token = localStorage.getItem('token')
  if (token) {
    // 从后端加载会话列表
    await loadConversationsFromBackend()

    // 加载当前会话
    if (currentConversationId.value) {
      await loadCurrentConversationFromBackend()
    } else if (conversations.value.length > 0) {
      currentConversationId.value = conversations.value[0].session_id
      await loadCurrentConversationFromBackend()
    }
  }

  nextTick(() => scrollToBottom())
})

const renderMarkdown = (content: string) => md.render(content)

// ==================== 会话管理函数 ====================

// 从后端加载会话列表
const loadConversationsFromBackend = async () => {
  try {
    const response = await getSessions({ page: 1, page_size: 50 })

    // 转换后端数据格式为前端格式
    conversations.value = response.sessions.map((session: any) => ({
      id: session.session_id,
      session_id: session.session_id,
      title: session.title || '新对话',
      messages: (session.messages || []).map((msg: any) => ({
        id: `${session.session_id}-${msg.timestamp}`,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp).toLocaleTimeString('zh-CN')
      })),
      createdAt: session.created_at,
      updatedAt: session.updated_at
    }))
  } catch (error: any) {
    console.error('Failed to load conversations:', error)
    // 只在非401错误时显示通知
    if (error.response?.status !== 401) {
      ElNotification({
        title: '加载失败',
        message: '无法加载会话列表',
        type: 'warning'
      })
    }
  }
}

// 从后端加载当前会话详情
const loadCurrentConversationFromBackend = async () => {
  if (!currentConversationId.value) {
    messages.value = []
    return
  }

  try {
    const session = await getSession(currentConversationId.value)

    // 转换消息格式
    messages.value = (session.messages || []).map((msg: any) => ({
      id: `${session.session_id}-${msg.timestamp}`,
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp).toLocaleTimeString('zh-CN')
    }))
  } catch (error) {
    console.error('Failed to load conversation:', error)
    messages.value = []
  }
}

const switchConversation = async (conversationId: string) => {
  // 切换到新会话
  currentConversationId.value = conversationId
  await loadCurrentConversationFromBackend()

  nextTick(() => scrollToBottom())
  conversationDialogVisible.value = false

  ElNotification({
    title: '切换成功',
    message: '已切换到会话: ' + conversations.value.find(c => c.session_id === conversationId)?.title,
    type: 'success'
  })
}

const deleteConversation = async (conversationId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '确认删除', {
      type: 'warning'
    })

    // 调用后端 API 删除会话
    await deleteSessionApi(conversationId)

    // 从本地列表中移除
    conversations.value = conversations.value.filter(c => c.session_id !== conversationId)

    // 如果删除的是当前会话，切换到第一个会话或清空
    if (conversationId === currentConversationId.value) {
      if (conversations.value.length > 0) {
        currentConversationId.value = conversations.value[0].session_id
        await loadCurrentConversationFromBackend()
      } else {
        currentConversationId.value = ''
        messages.value = []
      }
    }

    ElNotification({
      title: '删除成功',
      message: '会话已删除',
      type: 'success'
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElNotification({
        title: '删除失败',
        message: '无法删除会话',
        type: 'error'
      })
    }
  }
}

const handleEnter = (event: KeyboardEvent) => {
  if (!event.shiftKey) sendMessage()
}

const quickSend = (query: string) => {
  inputMessage.value = query
  sendMessage()
}

const saveChatHistory = (query: string, response: string) => {
  // 保存到 Sidebar 的历史记录（用于查看历史对话）
  const historyItem = {
    query,
    response,
    timestamp: new Date().toLocaleString('zh-CN')
  }

  const savedHistory = localStorage.getItem('chatHistory')
  const history = savedHistory ? JSON.parse(savedHistory) : []
  history.unshift(historyItem)

  // 只保留最近50条
  if (history.length > 50) {
    history.pop()
  }

  localStorage.setItem('chatHistory', JSON.stringify(history))
}

const sendMessage = async () => {
  const query = inputMessage.value.trim()
  if (!query || isLoading.value) return

  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: query,
    timestamp: new Date().toLocaleTimeString('zh-CN')
  })

  inputMessage.value = ''
  isLoading.value = true
  isTyping.value = true

  await nextTick()
  scrollToBottom()

  try {
    // 准备对话历史（最近10条）
    const history = messages.value
      .slice(-10)
      .map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }))

    // 使用新的 API 调用
    const data = await executeAgent(
      query,
      currentConversationId.value,
      chatMode.value,
      history
    )

    if (!data || !data.final_answer) {
      throw new Error('无效的响应数据')
    }

    // 更新 session_id（后端会返回实际的session_id）
    if (data.session_id && data.session_id !== currentConversationId.value) {
      currentConversationId.value = data.session_id
    }

    const aiMessage = {
      id: Date.now().toString() + '-ai',
      role: 'assistant' as const,
      content: data.final_answer,
      timestamp: new Date().toLocaleTimeString('zh-CN')
    }

    messages.value.push(aiMessage)

    // 保存参考来源（立即设置，使用 nextTick 确保 DOM 更新）
    console.log('[ChatWindow] 收到响应 data:', data)
    console.log('[ChatWindow] sources:', data.sources)
    console.log('[ChatWindow] sources 数量:', data.sources?.length || 0)

    await nextTick()  // 等待消息添加到 DOM

    if (data.sources && data.sources.length > 0) {
      sources.value = [...data.sources]  // 创建新数组引用，确保响应式更新
      console.log('[ChatWindow] 已设置 sources，当前长度:', sources.value.length)
      console.log('[ChatWindow] chatMode:', chatMode.value)
      console.log('[ChatWindow] Sources Panel 应该显示:', chatMode.value === 'agent' && sources.value.length > 0)
    } else {
      console.log('[ChatWindow] 没有 sources 或 sources 为空')
      sources.value = []  // 确保清空旧的 sources
    }

    // 重新加载会话列表以更新标题和消息数
    await loadConversationsFromBackend()

    // 保存到历史记录（延迟执行，避免影响 sources 显示）
    await nextTick()
    saveChatHistory(query, data.final_answer)

  } catch (error: any) {
    console.error('Error:', error)

    let errorMessage = '请检查后端服务状态'
    if (error.name === 'AbortError') {
      errorMessage = '请求超时，请稍后重试'
    } else if (error.message) {
      errorMessage = error.message
    }

    ElNotification({
      title: '请求失败',
      message: errorMessage,
      type: 'error',
      duration: 5000
    })

    messages.value.push({
      id: Date.now().toString() + '-ai',
      role: 'assistant',
      content: `抱歉，处理您的请求时出现错误：${errorMessage}`,
      timestamp: new Date().toLocaleTimeString('zh-CN')
    })
  } finally {
    isTyping.value = false
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const newChat = () => {
  // 清空当前会话ID（下次发送消息时会自动创建新会话）
  currentConversationId.value = ''
  messages.value = []
  inputMessage.value = ''
  thoughtSteps.value = []
  sources.value = []

  ElNotification({
    title: '新对话',
    message: '已创建新对话，开始第一条消息后将自动保存',
    type: 'success'
  })
}
</script>

<style scoped>
.chat-window {
  min-height: 0;
  background: linear-gradient(to bottom right, #f8fafc, #e2e8f0);
  max-width: 100%;
  overflow: hidden;
}

.chat-window.has-sources-panel {
  margin-right: 380px;
  transition: margin-right 0.3s ease;
}

/* 消息气泡样式 */
.message-bubble {
  max-width: 70%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-user {
  max-width: 60%;
}

.message-ai {
  max-width: 80%;
}

/* Header响应式处理 */
.glassmorphism {
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .message-bubble {
    max-width: 85%;
  }

  .message-ai {
    max-width: 90%;
  }
}

/* 消息内容美化 */
.prose :deep(pre) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.prose :deep(code) {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  color: #1e40af;
  font-weight: 500;
  border: 1px solid #bfdbfe;
}

.prose :deep(a) {
  color: #2563eb;
  text-decoration: none;
  transition: color 0.2s;
  border-bottom: 1px dotted #2563eb;
  cursor: pointer;
}

.prose :deep(a:hover) {
  color: #1d4ed8;
  border-bottom-style: solid;
  background: rgba(59, 130, 246, 0.05);
  padding: 0 4px;
  margin: 0 -4px;
  border-radius: 2px;
}

/* 标题美化 */
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  color: #1e293b;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.prose :deep(h1) {
  font-size: 1.875rem;
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.prose :deep(h2) {
  font-size: 1.5rem;
  color: #334155;
}

.prose :deep(h3) {
  font-size: 1.25rem;
  color: #475569;
}

/* 列表美化 */
.prose :deep(ul),
.prose :deep(ol) {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.prose :deep(li) {
  margin: 0.5rem 0;
  color: #334155;
}

.prose :deep(li::marker) {
  color: #3b82f6;
  font-weight: bold;
}

/* 引用块美化 */
.prose :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #64748b;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  padding: 1rem;
  border-radius: 0.5rem;
}

/* 表格美化 */
.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.prose :deep(th) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
}

.prose :deep(td) {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
}

.prose :deep(tr:hover) {
  background: #f8fafc;
}

/* 加载指示器美化 */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #dbeafe;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 输入框美化增强 */
:deep(.el-textarea__inner) {
  background: white !important;
  border: 2px solid #e2e8f0 !important;
  border-radius: 0.75rem !important;
  padding: 0.75rem 1rem !important;
  color: #1e293b !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
}

:deep(.el-textarea__inner):focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 2px 8px rgba(0, 0, 0, 0.05) !important;
}

:deep(.el-textarea__inner)::placeholder {
  color: #94a3b8 !important;
}

</style>

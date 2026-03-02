<template>
  <div class="sidebar h-full bg-white border-r border-gray-200 flex flex-col">
    <!-- Logo -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
          <el-icon class="text-white text-xl"><MagicStick /></el-icon>
        </div>
        <div>
          <h1 class="text-xl font-bold text-gray-800">DeepInsight</h1>
          <p class="text-xs text-gray-500">AI Research Platform</p>
        </div>
      </div>
    </div>

    <!-- Knowledge Base Upload -->
    <div class="flex-1 p-6 overflow-y-auto">
      <div class="mb-6">
        <h2 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <el-icon><FolderOpened /></el-icon>
          知识库上传
        </h2>

        <!-- Upload Area -->
        <el-upload
          drag
          action="http://localhost:8000/api/v1/knowledge/upload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          :show-file-list="false"
          accept=".txt,.md,.pdf,.doc,.docx"
          class="w-full"
        >
          <div class="upload-area border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-500 transition-colors cursor-pointer bg-gray-50">
            <div class="mb-4">
              <el-icon class="text-5xl text-gray-400"><Upload /></el-icon>
            </div>
            <p class="text-sm text-gray-700 mb-2">拖拽文件到此处或点击上传</p>
            <p class="text-xs text-gray-500">支持 TXT, MD, PDF, DOC, DOCX</p>
          </div>
        </el-upload>

        <!-- Upload History -->
        <div v-if="uploadHistory.length > 0" class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xs font-semibold text-gray-500">最近上传</h3>
            <el-button text size="small" class="text-gray-500 hover:text-red-500" @click="clearAllHistory">
              清空全部
            </el-button>
          </div>
          <div class="space-y-2">
            <div
              v-for="file in uploadHistory"
              :key="file.id"
              class="flex items-center gap-2 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group"
            >
              <el-icon class="text-primary-500"><Document /></el-icon>
              <span class="flex-1 text-sm text-gray-700 truncate">{{ file.name }}</span>
              <el-icon class="text-green-500 text-sm"><CircleCheck /></el-icon>
              <el-button
                text
                size="small"
                class="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-500"
                @click="deleteDocument(file.name)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Knowledge Base Stats -->
      <div class="glassmorphism rounded-xl p-4 bg-white border border-gray-200">
        <h3 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <el-icon><DataAnalysis /></el-icon>
          知识库统计
        </h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">文档片段</span>
            <span class="text-sm font-semibold text-gray-800">{{ stats.docCount }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">文件数量</span>
            <span class="text-sm font-semibold text-gray-800">{{ stats.uniqueFileCount }}</span>
          </div>
          <el-button size="small" class="w-full" @click="showDocuments" :loading="isLoadingDocuments">
            <el-icon class="mr-1" v-if="!isLoadingDocuments"><FolderOpened /></el-icon>
            {{ isLoadingDocuments ? '加载中...' : '查看所有文档' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- Settings -->
    <div class="p-6 border-t border-gray-200">
      <!-- User Info -->
      <div v-if="currentUser" class="mb-4 p-3 rounded-lg bg-gray-50 border border-gray-200">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
            <el-icon class="text-white text-sm"><User /></el-icon>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-gray-800 truncate">{{ currentUser.full_name || currentUser.username }}</p>
            <p class="text-xs text-gray-500 truncate">{{ currentUser.email }}</p>
          </div>
        </div>
        <el-button
          text
          size="small"
          class="w-full justify-start text-gray-600 hover:text-red-500 hover:bg-red-50"
          @click="handleLogout"
        >
          <el-icon class="mr-2"><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>

      <!-- Login Button (if not logged in) -->
      <el-button
        v-else
        type="primary"
        class="w-full mb-3"
        @click="goToLogin"
      >
        <el-icon class="mr-2"><User /></el-icon>
        登录 / 注册
      </el-button>

      <el-button text class="w-full justify-start text-gray-600 hover:text-primary-600 hover:bg-gray-50 mb-2" @click="showHistory">
        <el-icon class="mr-2"><Clock /></el-icon>
        历史记录
      </el-button>
      <el-button text class="w-full justify-start text-gray-600 hover:text-primary-600 hover:bg-gray-50" @click="showSettings">
        <el-icon class="mr-2"><Setting /></el-icon>
        设置
      </el-button>
    </div>

    <!-- History Dialog -->
    <el-dialog v-model="historyDialogVisible" title="历史记录" width="70%" :close-on-click-modal="false">
      <div v-if="chatHistory.length === 0" class="text-center py-8 text-gray-500">
        暂无历史记录
      </div>
      <div v-else class="space-y-4 max-h-[60vh] overflow-y-auto">
        <div
          v-for="(item, index) in chatHistory"
          :key="index"
          class="p-4 rounded-lg bg-gray-50 border border-gray-200"
        >
          <div class="flex items-start gap-3 mb-2">
            <el-icon class="text-primary-500 mt-1"><User /></el-icon>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-800 mb-1">用户</p>
              <p class="text-sm text-gray-700">{{ item.query }}</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <el-icon class="text-green-500 mt-1"><MagicStick /></el-icon>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-800 mb-1">AI助手</p>
              <p class="text-sm text-gray-700">{{ item.response }}</p>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2 text-right">{{ item.timestamp }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="clearHistory" :disabled="chatHistory.length === 0">清空历史</el-button>
        <el-button type="primary" @click="historyDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Documents Dialog -->
    <el-dialog v-model="documentsDialogVisible" title="知识库文档" width="70%" :close-on-click-modal="false">
      <!-- 加载状态 -->
      <div v-if="isLoadingDocuments" class="text-center py-12">
        <el-icon class="is-loading text-primary-500 text-5xl mb-4"><Loading /></el-icon>
        <p class="text-dark-muted">正在加载文档列表...</p>
        <p class="text-xs text-dark-muted mt-2">如果 Milvus 刚启动，请耐心等待</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="allDocuments.length === 0" class="text-center py-8 text-dark-muted">
        <el-icon class="text-4xl mb-2"><FolderOpened /></el-icon>
        <p>暂无文档</p>
        <p class="text-xs mt-2">请先上传文档到知识库</p>
      </div>

      <!-- 文档列表 -->
      <div v-else class="space-y-3 max-h-[60vh] overflow-y-auto">
        <div
          v-for="doc in allDocuments"
          :key="doc.id"
          class="p-4 rounded-lg bg-gray-50 border border-gray-200 hover:border-primary-500 transition-colors"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2 flex-1">
              <el-icon class="text-primary-500"><Document /></el-icon>
              <span class="font-semibold text-gray-800">{{ doc.filename }}</span>
            </div>
            <el-button
              text
              size="small"
              class="text-red-400 hover:text-red-500 hover:bg-red-500/10"
              @click="deleteDocumentByFilename(doc.filename)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
          <p class="text-sm text-gray-700 mt-2 line-clamp-3">{{ doc.text_preview }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="documentsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Settings Dialog -->
    <el-dialog v-model="settingsDialogVisible" title="设置" width="50%" :close-on-click-modal="false">
      <el-form label-position="left" label-width="120px">
        <el-form-item label="API地址">
          <el-input v-model="settings.apiUrl" placeholder="http://localhost:8000" />
        </el-form-item>
        <el-form-item label="请求超时(秒)">
          <el-input-number v-model="settings.timeout" :min="10" :max="300" />
        </el-form-item>
        <el-form-item label="最大Token数">
          <el-input-number v-model="settings.maxTokens" :min="100" :max="8000" step="100" />
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="settings.temperature" :min="0" :max="1" :step="0.1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settingsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification, ElMessageBox } from 'element-plus'
import { Loading, Document, Delete, FolderOpened, User, SwitchButton } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const uploadHistory = ref<Array<{ id: string; name: string }>>([])
const currentUser = ref<any>(null)  // 当前登录用户信息
const chatHistory = ref<Array<{ query: string; response: string; timestamp: string }>>([])
const historyDialogVisible = ref(false)
const settingsDialogVisible = ref(false)
const stats = reactive({
  docCount: 0,
  uniqueFileCount: 0
})
const allDocuments = ref<Array<{ id: number; filename: string; text_preview: string }>>([])
const documentsDialogVisible = ref(false)
const isLoadingDocuments = ref(false)  // 添加加载状态

const settings = reactive({
  apiUrl: 'http://localhost:8000',
  timeout: 120,
  maxTokens: 2000,
  temperature: 0.7
})

// 从localStorage加载设置和历史
onMounted(async () => {
  loadUserInfo()  // 先加载用户信息
  loadSettings()
  loadHistory()

  // 只在用户登录后才获取统计数据和文档
  if (currentUser.value) {
    fetchStats()

    // 预加载文档列表（但不显示对话框）
    // 延迟3秒执行，确保 Milvus 有时间启动
    setTimeout(async () => {
      console.log('[Sidebar] 预加载文档列表...')
      await fetchAllDocuments()
    }, 3000)
  } else {
    console.log('[Sidebar] 用户未登录，跳过文档加载')
  }
})

// 加载用户信息
const loadUserInfo = () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      currentUser.value = JSON.parse(userStr)
    } catch (e) {
      console.error('Failed to parse user info:', e)
      currentUser.value = null
    }
  }
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '确认', {
    type: 'warning'
  }).then(() => {
    // 清除本地存储
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    currentUser.value = null

    ElNotification({
      title: '已退出登录',
      message: '您已成功退出登录',
      type: 'success'
    })

    // 跳转到登录页
    router.push('/login')
  }).catch(() => {})
}

// 跳转到登录页
const goToLogin = () => {
  router.push('/login')
}

const loadSettings = () => {
  const saved = localStorage.getItem('settings')
  if (saved) {
    Object.assign(settings, JSON.parse(saved))
  }
}

const saveSettings = () => {
  localStorage.setItem('settings', JSON.stringify(settings))
  ElNotification({
    title: '保存成功',
    message: '设置已保存',
    type: 'success'
  })
  settingsDialogVisible.value = false
}

const loadHistory = () => {
  const saved = localStorage.getItem('chatHistory')
  if (saved) {
    chatHistory.value = JSON.parse(saved)
  }
}

const showHistory = () => {
  loadHistory()
  historyDialogVisible.value = true
}

const clearHistory = () => {
  ElMessageBox.confirm('确定要清空所有历史记录吗？', '确认', {
    type: 'warning'
  }).then(() => {
    chatHistory.value = []
    localStorage.removeItem('chatHistory')
    ElNotification({
      title: '清空成功',
      message: '历史记录已清空',
      type: 'success'
    })
  }).catch(() => {})
}

const showSettings = () => {
  settingsDialogVisible.value = true
}

const beforeUpload = (file: File) => {
  const isValid = ['text/plain', 'text/markdown', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type) ||
                   file.name.endsWith('.txt') || file.name.endsWith('.md') || file.name.endsWith('.pdf') || file.name.endsWith('.docx')

  if (!isValid) {
    ElNotification({
      title: '文件格式不支持',
      message: '请上传 TXT, MD, PDF, DOCX 格式的文件',
      type: 'warning'
    })
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElNotification({
      title: '文件过大',
      message: '文件大小不能超过 10MB',
      type: 'warning'
    })
    return false
  }

  return true
}

const handleUploadSuccess = (response: any) => {
  ElNotification({
    title: '上传成功',
    message: `已成功上传文档: ${response.filename}`,
    type: 'success'
  })

  uploadHistory.value.unshift({
    id: Date.now().toString(),
    name: response.filename
  })

  // 保存到localStorage
  localStorage.setItem('uploadHistory', JSON.stringify(uploadHistory.value))

  // 重新获取统计信息和文档列表
  fetchStats()
  fetchAllDocuments()
}

const deleteDocumentByFilename = async (filename: string) => {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${filename}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await axios.delete(`http://localhost:8000/api/v1/knowledge/documents/filename/${encodeURIComponent(filename)}`)

    ElNotification({
      title: '删除成功',
      message: `文档 "${filename}" 已删除`,
      type: 'success'
    })

    // 从上传历史中移除
    uploadHistory.value = uploadHistory.value.filter(f => f.name !== filename)
    localStorage.setItem('uploadHistory', JSON.stringify(uploadHistory.value))

    // 从所有文档列表中移除
    allDocuments.value = allDocuments.value.filter(d => d.filename !== filename)

    // 重新获取统计信息
    fetchStats()

  } catch (error: any) {
    if (error !== 'cancel') {
      ElNotification({
        title: '删除失败',
        message: error.response?.data?.detail || '请检查网络连接',
        type: 'error'
      })
    }
  }
}

const handleUploadError = () => {
  ElNotification({
    title: '上传失败',
    message: '请检查网络连接和后端服务状态',
    type: 'error'
  })
}

const deleteDocument = async (filename: string) => {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${filename}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await axios.delete(`http://localhost:8000/api/v1/knowledge/documents/filename/${encodeURIComponent(filename)}`)

    // 从上传历史中移除
    uploadHistory.value = uploadHistory.value.filter(f => f.name !== filename)
    localStorage.setItem('uploadHistory', JSON.stringify(uploadHistory.value))

    ElNotification({
      title: '删除成功',
      message: `文档 "${filename}" 已删除`,
      type: 'success'
    })

    fetchStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElNotification({
        title: '删除失败',
        message: error.response?.data?.detail || '请检查网络连接',
        type: 'error'
      })
    }
  }
}

const clearAllHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有上传记录吗？', '确认', {
      type: 'warning'
    })

    uploadHistory.value = []
    localStorage.removeItem('uploadHistory')

    ElNotification({
      title: '清空成功',
      message: '上传记录已清空',
      type: 'success'
    })
  } catch {
    // 用户取消
  }
}

const fetchStats = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/v1/knowledge/stats')
    stats.docCount = response.data.num_entities || 0  // 文档片段总数
    stats.uniqueFileCount = response.data.num_files || 0  // 唯一文件数量
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchAllDocuments = async (retryCount = 0) => {
  isLoadingDocuments.value = true

  try {
    const response = await axios.get('http://localhost:8000/api/v1/knowledge/documents?limit=100', {
      timeout: 10000  // 10秒超时
    })

    // 处理文档数据，过滤掉没有filename的文档，或者生成一个默认名称
    const processedDocs = response.data.documents
      .filter((doc: any) => doc.metadata?.filename) // 只保留有filename的文档
      .map((doc: any) => ({
        id: doc.id,
        filename: doc.metadata?.filename || '未知文件',
        text_preview: doc.text_preview || ''
      }))

    allDocuments.value = processedDocs
    stats.uniqueFileCount = response.data.unique_files?.length || 0
    isLoadingDocuments.value = false

    if (processedDocs.length === 0 && response.data.total_documents > 0) {
      ElNotification({
        title: '提示',
        message: '知识库中有文档，但没有文件名信息',
        type: 'warning'
      })
    }

    return true  // 返回成功
  } catch (error: any) {
    console.error('Failed to fetch documents:', error)

    // 如果是 Milvus 还没准备好，尝试重试（最多重试3次）
    if (retryCount < 3 && error.code === 'ECONNABORTED') {
      console.log(`文档加载失败，重试第 ${retryCount + 1} 次...`)
      await new Promise(resolve => setTimeout(resolve, 2000))  // 等待2秒后重试
      return fetchAllDocuments(retryCount + 1)
    }

    isLoadingDocuments.value = false

    // 给用户更友好的错误提示
    let errorMessage = '无法加载知识库文档列表'
    if (error.code === 'ECONNABORTED') {
      errorMessage = '知识库服务响应超时，请确保 Milvus 已启动'
    } else if (error.response?.status === 404) {
      errorMessage = '知识库中暂无文档'
    } else if (error.response?.status === 500) {
      errorMessage = '知识库服务错误，请检查后端日志'
    }

    ElNotification({
      title: '加载失败',
      message: errorMessage,
      type: 'error',
      duration: 5000
    })

    return false  // 返回失败
  }
}

const showDocuments = async () => {
  // 先加载数据，成功后再打开对话框
  const success = await fetchAllDocuments()
  if (success) {
    documentsDialogVisible.value = true
  }
}
</script>

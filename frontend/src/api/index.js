import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000, // 60 秒超时 (Agent 执行可能需要较长时间)
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取认证 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
      console.log('[API] 添加 Authorization header，token前缀:', token.substring(0, 20) + '...')
    } else {
      console.log('[API] 未找到 token，跳过 Authorization header')
    }

    // 从 localStorage 获取 OpenAI API Key
    const openaiKey = localStorage.getItem('openaiKey')
    if (openaiKey) {
      config.headers['X-OpenAI-API-Key'] = openaiKey
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 如果是401未授权错误，不显示错误消息（可能在页面加载时发生）
    if (error.response?.status === 401) {
      console.log('API: 未授权请求，可能需要登录')
      return Promise.reject(error)
    }

    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// ============================
// Agent 相关 API
// ============================

/**
 * 执行 Agent 任务
 * @param {string} query - 用户查询
 * @param {string} session_id - 会话 ID (可选)
 * @param {string} mode - 执行模式: agent/rag/normal (默认: agent)
 * @param {Array} history - 对话历史 (可选)
 */
export const executeAgent = (query, session_id = null, mode = 'agent', history = []) => {
  return api.post('/agent/execute', {
    query,
    session_id,
    mode,
    history
  })
}

/**
 * 获取 Agent 执行状态
 * @param {string} thread_id - 线程 ID
 */
export const getAgentStatus = (thread_id) => {
  return api.get(`/agent/status/${thread_id}`)
}

/**
 * 获取 Agent 执行历史
 */
export const getAgentHistory = (params = {}) => {
  return api.get('/agent/history', { params })
}

// ============================
// 知识库相关 API
// ============================

/**
 * 上传文档到知识库
 * @param {FormData} data - 包含文件和元数据的表单数据
 */
export const uploadDocument = (data) => {
  return api.post('/knowledge/upload', data, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 搜索知识库
 * @param {string} query - 搜索查询
 * @param {number} top_k - 返回结果数量
 */
export const searchKnowledge = (query, top_k = 5) => {
  return api.post('/knowledge/search', {
    query,
    top_k
  })
}

/**
 * 获取知识库统计信息
 */
export const getKnowledgeStats = () => {
  return api.get('/knowledge/stats')
}

/**
 * 删除知识库文档
 * @param {number} doc_id - 文档 ID
 */
export const deleteDocument = (doc_id) => {
  return api.delete(`/knowledge/documents/${doc_id}`)
}

// ============================
// 会话相关 API
// ============================

/**
 * 获取会话列表
 */
export const getSessions = (params = {}) => {
  return api.get('/sessions', { params })
}

/**
 * 获取会话详情
 * @param {string} session_id - 会话 ID
 */
export const getSession = (session_id) => {
  return api.get(`/sessions/${session_id}`)
}

/**
 * 删除会话
 * @param {string} session_id - 会话 ID
 */
export const deleteSession = (session_id) => {
  return api.delete(`/sessions/${session_id}`)
}

// ============================
// 系统相关 API
// ============================

/**
 * 获取系统健康状态
 */
export const getHealth = () => {
  return api.get('/health')
}

/**
 * 获取 Milvus 状态
 */
export const getMilvusStatus = () => {
  return api.get('/system/milvus-status')
}

export default api

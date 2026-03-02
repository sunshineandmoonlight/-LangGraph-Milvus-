<template>
  <div class="knowledge-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="12">
          <el-statistic title="文件数量" :value="stats.num_files" />
        </el-col>
        <el-col :span="12">
          <el-statistic title="Collection" :value="stats.collection_name" />
        </el-col>
      </el-row>

      <!-- 搜索框 -->
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索知识库..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <el-divider>搜索结果</el-divider>
        <el-card
          v-for="(result, index) in searchResults"
          :key="index"
          class="result-card"
          shadow="hover"
        >
          <template #header>
            <div class="result-header">
              <el-tag type="success" size="small">
                相似度: {{ (result.score * 100).toFixed(2) }}%
              </el-tag>
            </div>
          </template>
          <div class="result-content">
            <p class="result-text">{{ result.text }}</p>
            <el-collapse v-if="result.metadata">
              <el-collapse-item title="元数据" name="metadata">
                <pre>{{ JSON.stringify(result.metadata, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".txt,.md,.json,.doc,.docx,.pdf"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .txt, .md, .json, .doc, .docx, .pdf 文件，文件大小不超过 10MB
          </div>
        </template>
      </el-upload>

      <el-form label-width="80px" style="margin-top: 20px">
        <el-form-item label="元数据">
          <el-input
            v-model="uploadMetadata"
            type="textarea"
            :rows="3"
            placeholder='JSON 格式，例如: {"category": "技术文档", "author": "张三"}'
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadDocument, searchKnowledge, getKnowledgeStats } from '@/api'

const showUploadDialog = ref(false)
const uploading = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const uploadFile = ref(null)
const uploadMetadata = ref('')

const stats = reactive({
  num_files: 0,
  collection_name: ''
})

const loadStats = async () => {
  try {
    const response = await getKnowledgeStats()
    stats.num_files = response.num_files
    stats.collection_name = response.collection_name
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    return
  }

  try {
    const response = await searchKnowledge(searchQuery.value)
    searchResults.value = response.results
    ElMessage.success(`找到 ${response.total} 条相关结果`)
  } catch (error) {
    ElMessage.error('搜索失败')
  }
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

const handleUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    if (uploadMetadata.value) {
      formData.append('metadata', uploadMetadata.value)
    }

    await uploadDocument(formData)
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false
    uploadFile.value = null
    uploadMetadata.value = ''
    loadStats()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.knowledge-view {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.search-section {
  margin: 20px 0;
}

.search-results {
  margin-top: 20px;
}

.result-card {
  margin-bottom: 15px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-text {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

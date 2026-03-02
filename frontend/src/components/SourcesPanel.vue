<template>
  <div
    v-if="sources.length > 0"
    class="sources-panel glassmorphism border-l border-dark-border"
    :class="{ 'panel-open': isOpen, 'panel-closed': !isOpen }"
  >
    <!-- Header -->
    <div class="panel-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <el-icon class="text-primary-500"><Link /></el-icon>
          <h3 class="font-semibold text-gray-800">参考来源</h3>
          <el-tag size="small" type="info">{{ sources.length }}</el-tag>
        </div>
        <el-button
          :icon="isOpen ? Close : ArrowLeft"
          size="small"
          @click="togglePanel"
          text
        />
      </div>
    </div>

    <!-- Sources List -->
    <div class="panel-content" v-show="isOpen">
      <div class="sources-list space-y-3">
        <div
          v-for="(source, index) in sources"
          :key="index"
          class="source-item glassmorphism-inner"
        >
          <div class="source-header">
            <div class="flex items-start gap-2">
              <div class="source-icon">
                <!-- 显示网站favicon -->
                <img
                  v-if="shouldShowImage(source, index)"
                  :src="source.favicon_url"
                  class="favicon-img"
                  @error="() => handleImageError(index)"
                />
                <!-- favicon加载失败或不显示时显示首字母 -->
                <span v-else class="source-fallback">
                  {{ getSourceInitial(source) }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <!-- 显示来源（域名） -->
                <div v-if="source.source" class="source-source">
                  {{ source.source }}
                </div>
                <!-- 有 URL 时显示链接 -->
                <a
                  v-if="source.url"
                  :href="source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="source-title"
                  @mouseenter="showPreview(source, $event)"
                  @mouseleave="hidePreview"
                >
                  {{ source.title || source.url }}
                </a>
                <!-- 没有 URL 时显示文本（知识库文档） -->
                <span v-else class="source-title-text">
                  {{ source.title }}
                </span>
              </div>
              <el-button
                :icon="Close"
                size="small"
                text
                @click="removeSource(index)"
                class="text-gray-400 hover:text-red-400"
              />
            </div>
          </div>
          <p v-if="source.snippet" class="source-snippet">
            {{ source.snippet }}
          </p>
          <div class="source-footer" v-if="source.url">
            <el-link
              :href="source.url"
              target="_blank"
              rel="noopener noreferrer"
              type="primary"
              :underline="false"
              class="text-xs"
            >
              访问链接
              <el-icon class="ml-1"><TopRight /></el-icon>
            </el-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Link Preview Tooltip -->
    <teleport to="body">
      <div
        v-if="previewSource"
        ref="previewTooltip"
        class="link-preview-tooltip"
        :style="previewPosition"
      >
        <div class="preview-header">
          <el-icon class="text-primary-500"><Link /></el-icon>
          <span class="font-medium text-white">{{ previewSource.title || '链接预览' }}</span>
        </div>
        <p class="preview-url">{{ previewSource.url }}</p>
        <p v-if="previewSource.snippet" class="preview-snippet">
          {{ previewSource.snippet }}
        </p>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Link, Close, ArrowLeft, Document, TopRight } from '@element-plus/icons-vue'

interface Source {
  title: string
  url: string
  snippet: string
  source?: string
  favicon_url?: string
}

interface Props {
  sources: Source[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const isOpen = ref(true)
const previewSource = ref<Source | null>(null)
const previewPosition = ref({
  position: 'fixed',
  left: '0px',
  top: '0px'
})

// 跟踪每个来源的图片加载状态
const imageLoadErrors = ref<Record<number, boolean>>({})

const togglePanel = () => {
  isOpen.value = !isOpen.value
}

// 暴露 isOpen 给父组件
defineExpose({
  isOpen
})

const removeSource = (index: number) => {
  emit('close')
}

const showPreview = (source: Source, event: MouseEvent) => {
  previewSource.value = source

  const target = event.target as HTMLElement
  const rect = target.getBoundingClientRect()

  previewPosition.value = {
    position: 'fixed',
    left: `${rect.left + rect.width / 2 - 200}px`,
    top: `${rect.bottom + 10}px`
  }
}

const hidePreview = () => {
  previewSource.value = null
}

const handleImageError = (index: number) => {
  // 标记图片加载失败
  imageLoadErrors.value[index] = true
}

const shouldShowImage = (source: Source, index: number) => {
  // 如果没有 favicon_url，不显示图片
  if (!source.favicon_url) return false
  // 如果图片加载失败，不显示图片
  if (imageLoadErrors.value[index]) return false
  // 否则显示图片
  return true
}

const getSourceInitial = (source: Source) => {
  // 获取来源的首字母作为备用图标
  if (source.source) {
    return source.source.charAt(0).toUpperCase()
  }
  if (source.title) {
    return source.title.charAt(0).toUpperCase()
  }
  return '?'
}
</script>

<style scoped>
.sources-panel {
  position: fixed;
  right: 0;
  top: 0;
  height: 100vh;
  width: 380px;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 100;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-left: 1px solid #e2e8f0;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1);
}

.panel-open {
  transform: translateX(0);
}

.panel-closed {
  transform: translateX(100%);
}

.panel-header {
  padding: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.source-item {
  padding: 1.25rem;
  border-radius: 0.75rem;
  background: white;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.source-item:hover {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  border-color: #3b82f6;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.source-header {
  margin-bottom: 0.75rem;
}

.source-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  border-radius: 0.75rem;
  color: #2563eb;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  overflow: hidden;
}

.favicon-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
  flex-shrink: 0;
}

.source-fallback {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
  text-transform: uppercase;
  flex-shrink: 0;
}

.source-source {
  font-size: 0.75rem;
  color: #3b82f6;
  font-weight: 600;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.source-title {
  color: #1e293b;
  text-decoration: none;
  font-weight: 600;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s;
}

.source-title:hover {
  color: #2563eb;
}

.source-title-text {
  color: #1e293b;
  font-weight: 600;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-snippet {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
  margin: 0.75rem 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  background: #f8fafc;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border-left: 3px solid #3b82f6;
}

.source-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

/* Link Preview Tooltip */
.link-preview-tooltip {
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.25rem;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  animation: fadeIn 0.2s ease;
  backdrop-filter: blur(20px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: #1e293b;
}

.preview-url {
  font-size: 0.75rem;
  color: #64748b;
  word-break: break-all;
  margin-bottom: 0.75rem;
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 0.375rem;
}

.preview-snippet {
  font-size: 0.875rem;
  color: #475569;
  line-height: 1.6;
  background: #f8fafc;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border-left: 3px solid #3b82f6;
}

/* Scrollbar Styling */
.panel-content::-webkit-scrollbar {
  width: 8px;
}

.panel-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

</style>

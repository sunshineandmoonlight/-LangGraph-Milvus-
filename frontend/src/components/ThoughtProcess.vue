<template>
  <div class="thought-process space-y-3">
    <transition-group name="slide-up">
      <div
        v-for="step in thoughts"
        :key="step.id"
        class="glassmorphism rounded-xl p-4 border-l-4"
        :class="getStepColor(step.status)"
      >
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <div v-if="step.status === 'running'" class="spinner text-primary-500"></div>
            <el-icon v-else-if="step.status === 'completed'" class="text-green-500">
              <CircleCheck />
            </el-icon>
            <el-icon v-else class="text-dark-muted">
              <Clock />
            </el-icon>
          </div>

          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-dark-text mb-1">{{ step.label }}</p>
            <div v-if="step.status === 'running'" class="w-full bg-dark-bg rounded-full h-1 overflow-hidden">
              <div class="bg-gradient-to-r from-primary-500 to-primary-600 h-full animate-pulse"></div>
            </div>
            <p v-if="step.details" class="text-xs text-dark-muted mt-1">{{ step.details }}</p>
          </div>

          <span class="text-xs text-dark-muted">{{ step.timestamp }}</span>
        </div>
      </div>
    </transition-group>

    <el-button
      v-if="thoughts.length > 0"
      text
      size="small"
      @click="isExpanded = !isExpanded"
      class="w-full text-dark-muted hover:text-white"
    >
      <el-icon class="mr-1">
        <component :is="isExpanded ? 'ArrowUp' : 'ArrowDown'" />
      </el-icon>
      {{ isExpanded ? '收起思考过程' : '展开思考过程' }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Clock, CircleCheck, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{
  steps: Array<{
    agent: string
    action: string
    status: string
    details?: string
  }>
}>()

const isExpanded = ref(true)

const thoughts = computed(() => {
  const icons: Record<string, string> = {
    'Supervisor': '🎯',
    'Researcher': '🔍',
    'Writer': '✍️',
    'Tavily': '🌐',
    'RAG': '📚'
  }

  return props.steps.map((step, index) => {
    const icon = icons[step.agent] || '⚙️'
    const timestamp = new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })

    return {
      id: `${step.agent}-${index}`,
      label: `${icon} ${step.agent}: ${step.action}`,
      status: step.status,
      details: step.details,
      timestamp
    }
  })
})

const getStepColor = (status: string) => {
  const colors = {
    'running': 'border-l-primary-500',
    'completed': 'border-l-green-500',
    'failed': 'border-l-red-500',
    'pending': 'border-l-dark-muted'
  }
  return colors[status] || colors.pending
}
</script>

<style scoped>
.thought-process {
  max-height: 400px;
  overflow-y: auto;
}
</style>

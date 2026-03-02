<template>
  <div class="agents-view">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="agent-card">
          <template #header>
            <div class="card-header">
              <el-icon><Avatar /></el-icon>
              <span>Supervisor</span>
            </div>
          </template>
          <div class="agent-info">
            <el-tag type="success">在线</el-tag>
            <p class="agent-desc">任务协调员，负责调度其他 Agent</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="agent-card">
          <template #header>
            <div class="card-header">
              <el-icon><Reading /></el-icon>
              <span>Researcher</span>
            </div>
          </template>
          <div class="agent-info">
            <el-tag type="success">在线</el-tag>
            <p class="agent-desc">研究专家，负责信息收集和分析</p>
            <div class="agent-tools">
              <el-tag size="small">Milvus 搜索</el-tag>
              <el-tag size="small">网络搜索</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="agent-card">
          <template #header>
            <div class="card-header">
              <el-icon><EditPen /></el-icon>
              <span>Writer</span>
            </div>
          </template>
          <div class="agent-info">
            <el-tag type="success">在线</el-tag>
            <p class="agent-desc">写作专家，负责撰写报告</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="workflow-card" style="margin-top: 20px">
      <template #header>
        <span>工作流程</span>
      </template>
      <div class="workflow-diagram">
        <el-steps direction="vertical" :space="200">
          <el-step title="用户输入" description="用户提出问题或任务" />
          <el-step title="Supervisor 调度" description="分析任务，决定调用哪个 Agent" />
          <el-step title="Researcher 研究" description="使用工具收集信息" />
          <el-step title="Writer 撰写" description="根据研究结果撰写报告" />
          <el-step title="返回结果" description="Supervisor 判断完成，返回最终答案" />
        </el-steps>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// Agent 状态监控页面
</script>

<style scoped>
.agents-view {
  height: 100%;
}

.agent-card {
  height: 200px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
}

.agent-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-desc {
  color: #606266;
  margin: 0;
}

.agent-tools {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.workflow-card {
  height: calc(100% - 220px);
}

.workflow-diagram {
  padding: 20px;
}
</style>

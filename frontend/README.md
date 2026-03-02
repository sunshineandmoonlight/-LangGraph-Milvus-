# DeepInsight AI - 前端项目

## 🎨 项目简介

为 "Enterprise Multi-Agent System" 开发的现代化前端界面，采用 Vue 3 + Tailwind CSS 构建，具有科技感和交互美感。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
npm run preview
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # 组件
│   │   ├── Sidebar.vue      # 侧边栏（上传、统计）
│   │   ├── ChatWindow.vue   # 聊天窗口
│   │   └── ThoughtProcess.vue # 思考过程展示
│   ├── App.vue              # 根组件
│   ├── main.ts              # 入口文件
│   └── style.css            # 全局样式
├── index.html               # HTML 模板
├── package.json             # 依赖配置
├── vite.config.ts           # Vite 配置
├── tailwind.config.js       # Tailwind 配置
└── postcss.config.js        # PostCSS 配置
```

## 🎯 核心功能

- ✅ 响应式深色主题
- ✅ 知识库文件上传（拖拽支持）
- ✅ 实时 AI 对话
- ✅ Markdown 渲染和代码高亮
- ✅ 思考过程可视化
- ✅ 玻璃态 (Glassmorphism) 设计
- ✅ 打字机效果

## 🔗 API 集成

前端通过 Vite 代理连接后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

**CORS 配置**: 后端已启用 CORS，无需额外配置。

## 📦 依赖说明

- **Vue 3**: 渐进式框架
- **Vite**: 快速构建工具
- **Tailwind CSS**: 实用优先 CSS 框架
- **Element Plus**: Vue 3 UI 组件库
- **Pinia**: 状态管理
- **Markdown-it**: Markdown 渲染
- **Highlight.js**: 代码高亮

## 🎨 UI 特性

1. **深色主题**: 护眼且科技感强
2. **玻璃态效果**: 现代化的半透明设计
3. **平滑动画**: 过渡效果和微交互
4. **响应式布局**: 自适应不同屏幕

## 📝 开发说明

### 添加新页面

在 `src/views/` 创建 Vue 组件，然后在路由中注册。

### 修改主题

编辑 `src/style.css` 和 `tailwind.config.js`。

### API 调用

使用 `axios` 或 `fetch` 调用后端 API，通过 `/api` 前缀代理到后端。

## 🔧 故障排除

### Q: 端口被占用
修改 `vite.config.ts` 中的 `server.port`

### Q: CORS 错误
确保后端服务运行在 http://localhost:8000

### Q: 样式不生效
检查 Tailwind CSS 配置和 `style.css` 导入

<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-card glassmorphism">
        <!-- Logo -->
        <div class="text-center mb-8">
          <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
            <el-icon class="text-white text-4xl"><MagicStick /></el-icon>
          </div>
          <h1 class="text-3xl font-bold text-gray-800">DeepInsight</h1>
          <p class="text-gray-500 mt-2">企业级 AI 多智能体平台</p>
        </div>

        <!-- Login/Register Toggle -->
        <el-tabs v-model="activeTab" class="w-full custom-tabs">
          <!-- Login Tab -->
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-position="top"
              class="mt-6"
            >
              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="loginForm.email"
                  type="email"
                  placeholder="请输入邮箱"
                  :prefix-icon="Message"
                  size="large"
                />
              </el-form-item>

              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="w-full"
                  :loading="isLoading"
                  @click="handleLogin"
                >
                  {{ isLoading ? '登录中...' : '登录' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- Register Tab -->
          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
              class="mt-6"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  size="large"
                />
              </el-form-item>

              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="registerForm.email"
                  type="email"
                  placeholder="请输入邮箱"
                  :prefix-icon="Message"
                  size="large"
                />
              </el-form-item>

              <el-form-item label="姓名（可选）" prop="full_name">
                <el-input
                  v-model="registerForm.full_name"
                  placeholder="请输入真实姓名"
                  :prefix-icon="UserFilled"
                  size="large"
                />
              </el-form-item>

              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码（至少6位）"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>

              <el-form-item label="确认密码" prop="confirm_password">
                <el-input
                  v-model="registerForm.confirm_password"
                  type="password"
                  placeholder="请再次输入密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                  @keyup.enter="handleRegister"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="w-full"
                  :loading="isLoading"
                  @click="handleRegister"
                >
                  {{ isLoading ? '注册中...' : '注册' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <!-- Tips -->
        <div class="mt-6 text-center text-sm">
          <p class="text-gray-700 font-medium mb-3">💡 提示：注册后即可使用所有功能</p>
          <el-divider class="my-4"></el-divider>
          <el-button
            type="success"
            size="large"
            class="w-full"
            @click="handleDemoLogin"
            plain
          >
            <el-icon class="mr-2"><MagicStick /></el-icon>
            测试模式快速体验
          </el-button>
          <p class="text-xs text-gray-600 mt-2">无需注册，使用测试账号直接进入</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import { Message, Lock, User, UserFilled, MagicStick } from '@element-plus/icons-vue'
import axios from 'axios'
import api from '@/api'

const router = useRouter()
const activeTab = ref('login')
const isLoading = ref(false)

// Login form
const loginFormRef = ref()
const loginForm = reactive({
  email: '',
  password: ''
})

const loginRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

// Register form
const registerFormRef = ref()
const registerForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// Login handler
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    isLoading.value = true

    // 使用 OAuth2PasswordRequestForm 格式
    const formData = new FormData()
    formData.append('username', loginForm.email)
    formData.append('password', loginForm.password)

    const response = await axios.post('http://localhost:8000/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000  // 30秒超时
    })

    // 保存 token 和用户信息
    const { access_token, user } = response.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(user))

    ElNotification({
      title: '登录成功',
      message: `欢迎回来，${user.full_name || user.username}！`,
      type: 'success'
    })

    // 跳转到主页
    router.push('/')
  } catch (error: any) {
    console.error('Login error:', error)
    ElNotification({
      title: '登录失败',
      message: error.response?.data?.detail || '请检查邮箱和密码',
      type: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

// Register handler
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    isLoading.value = true

    const response = await axios.post('http://localhost:8000/api/v1/auth/register', {
      email: registerForm.email,
      username: registerForm.username,
      full_name: registerForm.full_name || undefined,
      password: registerForm.password
    }, {
      timeout: 30000  // 30秒超时
    })

    // 保存 token 和用户信息
    const { access_token, user } = response.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(user))

    ElNotification({
      title: '注册成功',
      message: `欢迎加入，${user.full_name || user.username}！`,
      type: 'success'
    })

    // 跳转到主页
    router.push('/')
  } catch (error: any) {
    console.error('Register error:', error)
    ElNotification({
      title: '注册失败',
      message: error.response?.data?.detail || '请稍后重试',
      type: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

// Demo login handler - 测试模式快速体验
const handleDemoLogin = async () => {
  isLoading.value = true

  try {
    // 使用项目中配置好的 api 实例
    const response = await api.post('/auth/demo-login')

    // 保存 token 和用户信息 (api 实例的响应拦截器已自动返回 response.data)
    const { access_token, user } = response
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(user))

    ElNotification({
      title: '欢迎进入测试模式',
      message: `测试账号：${user.full_name || user.username}`,
      type: 'success',
      duration: 2000
    })

    // 跳转到主页
    router.push('/')
  } catch (error: any) {
    console.error('Demo login error:', error)
    ElNotification({
      title: '登录失败',
      message: error.response?.data?.detail || error.message || '测试模式暂时不可用',
      type: 'error',
      duration: 3000
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 450px;
}

.login-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
}

.glassmorphism {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

/* 修改标签页文字颜色 */
:deep(.custom-tabs .el-tabs__item) {
  color: #606266;
  font-weight: 500;
  font-size: 16px;
}

:deep(.custom-tabs .el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
}

:deep(.custom-tabs .el-tabs__item:hover) {
  color: #409eff;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: #409eff;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
}

:deep(.el-button--large) {
  border-radius: 12px;
  height: 48px;
  font-size: 16px;
}
</style>

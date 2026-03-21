<template>
  <div class="scan-exam-container">
    <el-card class="scan-card">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><loading /></el-icon>
        <p>正在验证二维码...</p>
      </div>

      <!-- Invalid -->
      <div v-else-if="examInfo && !examInfo.valid" class="invalid-state">
        <el-result icon="error" :title="examInfo.reason">
          <template #extra>
            <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
          </template>
        </el-result>
      </div>

      <!-- Valid -->
      <div v-else-if="examInfo && examInfo.valid" class="valid-state">
        <el-result icon="success" :title="examInfo.exam_title">
          <template #sub-title>
            <div class="exam-details">
              <p><strong>考试时长：</strong>{{ examInfo.duration }} 分钟</p>
              <p><strong>及格分数：</strong>{{ examInfo.pass_score }} 分</p>
              <p><strong>题目数量：</strong>{{ examInfo.question_count }} 道</p>
              <p><strong>考试时间：</strong></p>
              <p>{{ formatTime(examInfo.start_time) }} ~ {{ formatTime(examInfo.end_time) }}</p>
            </div>
          </template>
          <template #extra>
            <el-form v-if="!userStore.token" :model="loginForm" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入工号"
                  prefix-icon="User"
                  size="large"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                  clearable
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-button
                type="primary"
                size="large"
                style="width: 100%"
                @click="handleLogin"
                :loading="loggingIn"
              >
                登录并开始考试
              </el-button>
            </el-form>
            <div v-else class="logged-in">
              <p>您已登录，确认开始考试</p>
              <el-button type="success" size="large" @click="startExam" :loading="starting">
                开始考试
              </el-button>
            </div>
          </template>
        </el-result>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <el-result icon="error" title="二维码无效">
          <template #sub-title>
            <p>{{ error }}</p>
          </template>
          <template #extra>
            <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { examsAPI } from '../api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const loggingIn = ref(false)
const starting = ref(false)
const examInfo = ref(null)
const error = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const formRef = ref(null)

// Verify QR code
const verifyQRCode = async () => {
  const token = route.query.token
  console.log('QR Token:', token)
  if (!token) {
    error.value = '无效的二维码'
    loading.value = false
    return
  }

  try {
    const url = `https://lab-exam-api.onrender.com/api/qrcode/exam/verify/${token}`
    console.log('Verifying URL:', url)
    const response = await fetch(url)
    console.log('Response status:', response.status)
    const data = await response.json()
    console.log('Response data:', data)
    examInfo.value = data
    loading.value = false
  } catch (err) {
    console.error('Verify error:', err)
    error.value = '验证二维码失败，请稍后重试'
    loading.value = false
  }
}

// Login and start exam
const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loggingIn.value = true
    try {
      await userStore.login(loginForm.username, loginForm.password)
      ElMessage.success('登录成功')
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
    } finally {
      loggingIn.value = false
    }
  })
}

// Start exam
const startExam = async () => {
  const token = route.query.token
  if (!token) {
    ElMessage.error('无效的二维码')
    return
  }

  starting.value = true
  try {
    const response = await fetch('https://lab-exam-api.onrender.com/api/qrcode/exam/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`
      },
      body: JSON.stringify({ qr_token: token })
    })

    if (!response.ok) {
      const errorData = await response.json()
      ElMessage.error(errorData.detail || '验证失败')
      return
    }

    const data = await response.json()
    if (data.success) {
      // Start the exam
      await examsAPI.start(data.exam_id)
      router.push(`/exam/${data.exam_id}`)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '开始考试失败')
  } finally {
    starting.value = false
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// Initialize
verifyQRCode()
</script>

<style scoped>
.scan-exam-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.scan-card {
  width: 100%;
  max-width: 600px;
}

.loading-state,
.invalid-state,
.valid-state,
.error-state {
  padding: 40px 20px;
  text-align: center;
}

.loading-state {
  color: #666;
}

.exam-details {
  text-align: left;
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.exam-details p {
  margin: 8px 0;
  color: #666;
}

.exam-details strong {
  color: #333;
}

.logged-in {
  margin-top: 20px;
}

.logged-in p {
  color: #67c23a;
  font-size: 16px;
  margin-bottom: 15px;
}

:deep(.el-result__icon) {
  font-size: 80px;
}

:deep(.el-result__title) {
  font-size: 22px;
  margin-top: 20px;
}

:deep(.el-result__subtitle) {
  font-size: 14px;
  margin-top: 10px;
  color: #666;
}
</style>

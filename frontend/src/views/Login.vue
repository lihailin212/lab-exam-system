<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <el-tabs v-model="loginMode" class="login-tabs">
            <el-tab-pane label="账号密码登录" name="password"></el-tab-pane>
            <el-tab-pane label="扫码登录" name="qrcode"></el-tab-pane>
          </el-tabs>
        </div>
      </template>

      <!-- Password Login -->
      <div v-show="loginMode === 'password'">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="工号" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入工号"
              prefix-icon="User"
              size="large"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              style="width: 100%"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- QR Code Login -->
      <div v-show="loginMode === 'qrcode'" class="qrcode-section">
        <div v-if="qrCodeData.qr_image" class="qrcode-container">
          <img :src="qrCodeData.qr_image" alt="扫码登录" class="qrcode-image" />
          <div class="qrcode-status">
            <el-tag v-if="qrStatus === 'pending'" type="info">
              请使用手机扫描二维码
            </el-tag>
            <el-tag v-else-if="qrStatus === 'scanned'" type="warning">
              已扫描，请确认登录
            </el-tag>
            <el-tag v-else-if="qrStatus === 'confirmed'" type="success">
              登录成功，正在跳转...
            </el-tag>
            <el-tag v-else-if="qrStatus === 'expired'" type="danger">
              二维码已过期
            </el-tag>
          </div>
        </div>
        <div v-else class="qrcode-loading">
          <el-icon class="is-loading"><loading /></el-icon>
          <p>正在生成二维码...</p>
        </div>
        <div class="qrcode-refresh">
          <el-button v-if="qrStatus === 'expired'" type="primary" @click="generateQRCode">
            刷新二维码
          </el-button>
        </div>
      </div>

      <div class="tips">
        <p v-if="loginMode === 'password'">默认管理员账号: admin / admin123</p>
        <p v-else>请确保手机和电脑在同一网络下</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const loginMode = ref('password')

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// QR Code Login
const qrCodeData = ref({
  qr_token: '',
  qr_image: ''
})
const qrStatus = ref('pending')
let pollingInterval = null
let checkInterval = null

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      ElMessage.success('登录成功')

      if (userStore.isAdmin()) {
        router.push('/admin')
      } else {
        router.push('/')
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
    } finally {
      loading.value = false
    }
  })
}

const generateQRCode = async () => {
  try {
    const response = await fetch('https://lab-exam-api.onrender.com/api/qrcode/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    const data = await response.json()

    qrCodeData.value = {
      qr_token: data.qr_token,
      qr_image: data.qr_image
    }
    qrStatus.value = 'pending'

    // Start polling for status
    startPolling(data.qr_token)
  } catch (error) {
    ElMessage.error('生成二维码失败')
    console.error(error)
  }
}

const startPolling = (qrToken) => {
  // Clear previous intervals
  stopPolling()

  // Check status every 2 seconds
  checkInterval = setInterval(async () => {
    try {
      const response = await fetch(`https://lab-exam-api.onrender.com/api/qrcode/status/${qrToken}`)
      const data = await response.json()

      qrStatus.value = data.status

      if (data.status === 'confirmed' && data.token) {
        // Login successful
        stopPolling()
        await userStore.setToken(data.token)
        await userStore.fetchUserInfo()

        ElMessage.success('登录成功')
        router.push('/')
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (checkInterval) {
    clearInterval(checkInterval)
    checkInterval = null
  }
}

// Watch login mode change
watch(loginMode, (newMode) => {
  if (newMode === 'qrcode') {
    generateQRCode()
  } else {
    stopPolling()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 500px;
}

.card-header h2 {
  text-align: center;
  margin: 0;
  color: #333;
}

.login-tabs {
  width: 100%;
}

.qrcode-section {
  text-align: center;
  padding: 20px;
}

.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.qrcode-image {
  width: 200px;
  height: 200px;
  border: 1px solid #e0e0e0;
  padding: 10px;
  background: white;
}

.qrcode-status {
  padding: 10px;
}

.qrcode-loading {
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #909399;
}

.qrcode-refresh {
  margin-top: 20px;
}

.tips {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin-top: 10px;
}
</style>

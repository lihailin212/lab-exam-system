<template>
  <div class="scan-container">
    <el-card class="scan-card">
      <template #header>
        <div class="card-header">
          <h3>扫码登录确认</h3>
        </div>
      </template>

      <!-- Scan Step -->
      <div v-if="step === 'scan'" class="scan-step">
        <el-result icon="info" title="请输入工号" sub-title="验证您的身份以确认登录">
          <template #sub-title>
            <p>请输入您的工号以确认登录</p>
          </template>
        </el-result>

        <el-form :model="scanForm" :rules="rules" ref="scanFormRef" @submit.prevent="handleScan">
          <el-form-item prop="username">
            <el-input
              v-model="scanForm.username"
              placeholder="请输入工号"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            @click="handleScan"
            :loading="scanning"
          >
            确认扫码
          </el-button>
        </el-form>
      </div>

      <!-- Password Step -->
      <div v-else-if="step === 'password'" class="password-step">
        <el-result icon="warning" title="请输入密码" :sub-title="`确认用户：${userName}`">
          <template #icon>
            <el-icon style="font-size: 64px"><user /></el-icon>
          </template>
        </el-result>

        <el-form :model="passwordForm" :rules="rules" ref="passwordFormRef" @submit.prevent="handleConfirm">
          <el-form-item prop="password">
            <el-input
              v-model="passwordForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
              clearable
              @keyup.enter="handleConfirm"
            />
          </el-form-item>
          <el-button
            type="success"
            size="large"
            style="width: 100%"
            @click="handleConfirm"
            :loading="confirming"
          >
            确认登录
          </el-button>
        </el-form>

        <el-button
          type="danger"
          plain
          size="large"
          style="width: 100%; margin-top: 10px"
          @click="handleCancel"
        >
          取消
        </el-button>
      </div>

      <!-- Success Step -->
      <div v-else-if="step === 'success'" class="success-step">
        <el-result icon="success" title="登录成功" sub-title="您已成功确认登录">
          <template #extra>
            <p>请返回电脑继续操作</p>
          </template>
        </el-result>
      </div>

      <!-- Error Step -->
      <div v-else-if="step === 'error'" class="error-step">
        <el-result icon="error" :title="errorMessage" sub-title="请返回重新扫码">
          <template #extra>
            <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const step = ref('scan') // scan, password, success, error
const scanning = ref(false)
const confirming = ref(false)
const errorMessage = ref('')

const scanForm = reactive({
  qr_token: '',
  username: ''
})

const passwordForm = reactive({
  password: ''
})

const userName = ref('')

const rules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const scanFormRef = ref(null)
const passwordFormRef = ref(null)

onMounted(() => {
  const token = route.query.token
  if (token) {
    scanForm.qr_token = token
  } else {
    errorMessage.value = '无效的二维码'
    step.value = 'error'
  }
})

const handleScan = async () => {
  if (!scanFormRef.value) return

  await scanFormRef.value.validate(async (valid) => {
    if (!valid) return

    scanning.value = true
    try {
      const response = await fetch('https://lab-exam-api.onrender.com/api/qrcode/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          qr_token: scanForm.qr_token,
          username: scanForm.username
        })
      })

      const data = await response.json()

      if (data.status === 'scanned') {
        userName.value = data.name || data.username
        step.value = 'password'
        ElMessage.success('已确认用户，请输入密码')
      }
    } catch (error) {
      const errorData = error.response?.data || {}
      errorMessage.value = errorData.detail || '扫码失败'
      step.value = 'error'
    } finally {
      scanning.value = false
    }
  })
}

const handleConfirm = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    confirming.value = true
    try {
      const response = await fetch('https://lab-exam-api.onrender.com/api/qrcode/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          qr_token: scanForm.qr_token,
          username: scanForm.username,
          password: passwordForm.password
        })
      })

      const data = await response.json()

      if (data.status === 'confirmed') {
        step.value = 'success'
        ElMessage.success('登录确认成功')
      }
    } catch (error) {
      const errorData = error.response?.data || {}
      ElMessage.error(errorData.detail || '密码错误')
    } finally {
      confirming.value = false
    }
  })
}

const handleCancel = async () => {
  try {
    await fetch('https://lab-exam-api.onrender.com/api/qrcode/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        qr_token: scanForm.qr_token
      })
    })
  } catch (error) {
    console.error('Cancel error:', error)
  }

  step.value = 'scan'
  passwordForm.password = ''
}
</script>

<style scoped>
.scan-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.scan-card {
  width: 100%;
  max-width: 450px;
}

.card-header h3 {
  text-align: center;
  margin: 0;
  color: #333;
}

.scan-step,
.password-step,
.success-step,
.error-step {
  text-align: center;
  padding: 20px;
}

.el-form {
  margin-top: 30px;
}

:deep(.el-result__icon) {
  font-size: 80px;
}

:deep(.el-result__title) {
  font-size: 20px;
  margin-top: 20px;
}

:deep(.el-result__subtitle) {
  font-size: 14px;
  margin-top: 10px;
  color: #666;
}
</style>

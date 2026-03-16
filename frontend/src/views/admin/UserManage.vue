<template>
  <el-container class="admin-container">
    <el-aside width="200px">
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/admin/dashboard">
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <span>员工管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/exams">
          <span>考核管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/scores">
          <span>成绩统计</span>
        </el-menu-item>
        <el-menu-item index="/">
          <span>返回首页</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <h3>员工管理</h3>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>员工列表</span>
              <div>
                <el-button type="primary" @click="showAddDialog">添加员工</el-button>
                <el-button type="success" @click="showImportDialog">批量导入</el-button>
              </div>
            </div>
          </template>
          
          <el-table :data="users" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="工号" width="120" />
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
                  {{ row.role === 'admin' ? '管理员' : '员工' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
                <el-button size="small" type="warning" @click="showResetPwdDialog(row)">重置密码</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
    
    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑员工' : '添加员工'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="工号" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="员工" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- Reset Password Dialog -->
    <el-dialog v-model="pwdDialogVisible" title="重置密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item label="新密码" prop="password">
          <el-input v-model="pwdForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPwd" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog v-model="importDialogVisible" title="批量导入员工" width="600px">
      <div class="import-tip">
        <p>请上传 Excel 文件进行批量导入</p>
        <p>文件格式：工号,姓名,密码,角色,状态</p>
        <p>示例：1001,张三,123456,员工,启用</p>
        <el-button type="primary" link @click="downloadUserTemplate">
          下载导入模板
        </el-button>
      </div>

      <el-upload
        v-if="!importResult"
        ref="importRef"
        :auto-upload="false"
        :on-change="handleImportFileChange"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls 格式
          </div>
        </template>
      </el-upload>

      <div v-if="selectedFile" class="selected-file">
        <p>已选择文件: <strong>{{ selectedFile.name }}</strong></p>
        <el-button
          v-if="!importing && !importResult"
          type="success"
          @click="handleImport"
          :loading="importing"
        >
          开始导入
        </el-button>
      </div>

      <div v-if="importResult" class="import-result">
        <el-alert
          :title="importResult.success ? '导入成功' : '导入完成'"
          :type="importResult.success ? 'success' : 'warning'"
          :description="importResult.message"
          show-icon
        />
        <div v-if="importResult.errors && importResult.errors.length" class="import-errors">
          <h4>错误列表（前10条）:</h4>
          <ul>
            <li v-for="(err, idx) in importResult.errors" :key="idx">
              第{{ err.row }}行: {{ err.error }}
            </li>
          </ul>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeImportDialog">关闭</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { usersAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const pwdDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const currentUser = ref(null)

// Import
const importDialogVisible = ref(false)
const importRef = ref(null)
const selectedFile = ref(null)
const importing = ref(false)
const importResult = ref(null)

const form = reactive({
  username: '',
  name: '',
  password: '',
  role: 'user',
  is_active: true
})

const pwdForm = reactive({
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur', min: 6 }]
}

const pwdRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur', min: 6 }]
}

onMounted(() => {
  fetchUsers()
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const data = await usersAPI.list()
    users.value = data
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    username: '',
    name: '',
    password: '',
    role: 'user',
    is_active: true
  })
  dialogVisible.value = true
}

const showEditDialog = (user) => {
  isEdit.value = true
  currentUser.value = user
  Object.assign(form, {
    username: user.username,
    name: user.name,
    password: '',
    role: user.role,
    is_active: user.is_active
  })
  dialogVisible.value = true
}

const showResetPwdDialog = (user) => {
  currentUser.value = user
  pwdForm.password = ''
  pwdDialogVisible.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (isEdit.value) {
      await usersAPI.update(currentUser.value.id, {
        name: form.name,
        role: form.role,
        is_active: form.is_active
      })
      ElMessage.success('更新成功')
    } else {
      await usersAPI.create(form)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleResetPwd = async () => {
  if (!pwdForm.password || pwdForm.password.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  
  submitting.value = true
  try {
    await usersAPI.resetPassword(currentUser.value.id, pwdForm.password)
    ElMessage.success('密码重置成功')
    pwdDialogVisible.value = false
  } catch (error) {
    ElMessage.error('重置密码失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(`确定要删除员工 ${user.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await usersAPI.delete(user.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {}
}

// Import functions
const showImportDialog = () => {
  importDialogVisible.value = true
}

const handleImportFileChange = (file) => {
  selectedFile.value = file.raw
  importResult.value = null
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  importing.value = true
  try {
    const res = await usersAPI.import(selectedFile.value)
    importResult.value = res
    if (res.imported_count > 0) {
      ElMessage.success(res.message)
      fetchUsers()
    } else if (res.error_count > 0) {
      ElMessage.warning(res.message)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const downloadUserTemplate = () => {
  const templateContent = `工号,姓名,密码,角色,状态
1001,张三,123456,员工,启用
1002,李四,123456,员工,启用
1003,王五,123456,管理员,是`

  const link = document.createElement('a')
  link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent('\uFEFF' + templateContent)
  link.download = '员工导入模板.csv'
  link.click()
}

const closeImportDialog = () => {
  importDialogVisible.value = false
  selectedFile.value = null
  importResult.value = null
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
}

.el-aside {
  background-color: #304156;
}

.el-header {
  background-color: #409eff;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-tip {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.import-tip p {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
}

.selected-file {
  margin-top: 20px;
  padding: 15px;
  background: #f0f9eb;
  border-radius: 4px;
}

.selected-file p {
  margin: 0 0 10px 0;
}

.import-result {
  margin-top: 20px;
}

.import-errors {
  margin-top: 15px;
  max-height: 200px;
  overflow-y: auto;
}

.import-errors h4 {
  margin: 10px 0;
  color: #f56c6c;
}

.import-errors ul {
  margin: 0;
  padding-left: 20px;
  color: #909399;
  font-size: 13px;
}
</style>

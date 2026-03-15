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
          <h3>考核管理</h3>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>考核列表</span>
              <el-button type="primary" @click="showAddDialog">创建考核</el-button>
            </div>
          </template>
          
          <el-table :data="exams" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="title" label="考核名称" />
            <el-table-column prop="duration" label="时长(分钟)" width="100" />
            <el-table-column prop="pass_score" label="及格分数" width="100" />
            <el-table-column prop="question_count" label="题目数" width="80" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间">
              <template #default="{ row }">
                {{ formatTime(row.start_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="end_time" label="结束时间">
              <template #default="{ row }">
                {{ formatTime(row.end_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="manageQuestions(row)">题目</el-button>
                <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
                <el-button 
                  size="small" 
                  type="success" 
                  v-if="row.status === 'draft'"
                  @click="handlePublish(row)"
                >
                  发布
                </el-button>
                <el-button 
                  size="small" 
                  type="warning" 
                  v-if="row.status === 'published'"
                  @click="handleClose(row)"
                >
                  关闭
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
    
    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑考核' : '创建考核'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="考核名称" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="考核描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="form.start_time" type="datetime" placeholder="选择开始时间" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker v-model="form.end_time" type="datetime" placeholder="选择结束时间" />
        </el-form-item>
        <el-form-item label="考核时长" prop="duration">
          <el-input-number v-model="form.duration" :min="1" :max="180" />
          <span style="margin-left: 10px">分钟</span>
        </el-form-item>
        <el-form-item label="及格分数" prop="pass_score">
          <el-input-number v-model="form.pass_score" :min="0" :max="100" />
          <span style="margin-left: 10px">%</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { examsAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const exams = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

const form = reactive({
  title: '',
  description: '',
  start_time: '',
  end_time: '',
  duration: 60,
  pass_score: 60
})

const rules = {
  title: [{ required: true, message: '请输入考核名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

onMounted(() => {
  fetchExams()
})

const fetchExams = async () => {
  loading.value = true
  try {
    const data = await examsAPI.list()
    exams.value = data
  } catch (error) {
    ElMessage.error('获取考核列表失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getStatusType = (status) => {
  const types = { draft: 'info', published: 'success', closed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { draft: '草稿', published: '已发布', closed: '已关闭' }
  return texts[status] || status
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    duration: 60,
    pass_score: 60
  })
  dialogVisible.value = true
}

const showEditDialog = (exam) => {
  isEdit.value = true
  Object.assign(form, {
    id: exam.id,
    title: exam.title,
    description: exam.description,
    start_time: new Date(exam.start_time),
    end_time: new Date(exam.end_time),
    duration: exam.duration,
    pass_score: exam.pass_score
  })
  dialogVisible.value = true
}

const manageQuestions = (exam) => {
  router.push(`/admin/questions/${exam.id}`)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const data = {
      ...form,
      start_time: form.start_time.toISOString(),
      end_time: form.end_time.toISOString()
    }
    
    if (isEdit.value) {
      await examsAPI.update(form.id, data)
      ElMessage.success('更新成功')
    } else {
      await examsAPI.create(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchExams()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handlePublish = async (exam) => {
  try {
    await examsAPI.publish(exam.id)
    ElMessage.success('发布成功')
    fetchExams()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

const handleClose = async (exam) => {
  try {
    await examsAPI.close(exam.id)
    ElMessage.success('已关闭')
    fetchExams()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (exam) => {
  try {
    await ElMessageBox.confirm(`确定要删除考核 "${exam.title}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await examsAPI.delete(exam.id)
    ElMessage.success('删除成功')
    fetchExams()
  } catch {}
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
</style>

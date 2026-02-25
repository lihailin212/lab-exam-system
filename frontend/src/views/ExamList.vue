<template>
  <div class="exam-list-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>医学实验室考核系统</h2>
          <div class="user-info">
            <span>{{ userStore.user?.name }}</span>
            <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <div v-if="userStore.isAdmin()" class="admin-links">
          <el-button type="primary" @click="$router.push('/admin')">管理后台</el-button>
        </div>
        
        <h3 class="section-title">可参加的考核</h3>
        
        <el-empty v-if="!exams.length" description="暂无考核" />
        
        <div v-else class="exam-grid">
          <el-card 
            v-for="exam in exams" 
            :key="exam.id" 
            class="exam-card"
            shadow="hover"
          >
            <template #header>
              <div class="exam-header">
                <span class="exam-title">{{ exam.title }}</span>
                <el-tag :type="getStatusType(exam.status)">{{ getStatusText(exam.status) }}</el-tag>
              </div>
            </template>
            
            <div class="exam-info">
              <p><strong>考核时间：</strong>{{ formatTime(exam.start_time) }} - {{ formatTime(exam.end_time) }}</p>
              <p><strong>时长：</strong>{{ exam.duration }}分钟</p>
              <p><strong>及格分数：</strong>{{ exam.pass_score }}分</p>
              <p><strong>题目数量：</strong>{{ exam.question_count }}道</p>
            </div>
            
            <div class="exam-actions">
              <el-button 
                type="primary" 
                @click="startExam(exam.id)"
                :disabled="!canStart(exam)"
              >
                {{ getStartButtonText(exam) }}
              </el-button>
            </div>
          </el-card>
        </div>
        
        <h3 class="section-title" style="margin-top: 40px">我的成绩</h3>
        
        <el-table :data="myRecords" style="width: 100%">
          <el-table-column prop="exam_id" label="考核ID" width="80" />
          <el-table-column prop="score" label="得分" width="100">
            <template #default="{ row }">
              {{ row.score }}/{{ row.total_score }}
            </template>
          </el-table-column>
          <el-table-column prop="percentage" label="得分率" width="100">
            <template #default="{ row }">
              {{ row.percentage }}%
            </template>
          </el-table-column>
          <el-table-column prop="is_passed" label="是否及格" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_passed ? 'success' : 'danger'">
                {{ row.is_passed ? '及格' : '不及格' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="submitted_at" label="提交时间">
            <template #default="{ row }">
              {{ row.submitted_at ? formatTime(row.submitted_at) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { examsAPI, recordsAPI } from '../api'

const router = useRouter()
const userStore = useUserStore()

const exams = ref([])
const myRecords = ref([])

onMounted(async () => {
  await fetchData()
})

const fetchData = async () => {
  try {
    const [examRes, recordRes] = await Promise.all([
      examsAPI.list(),
      recordsAPI.my()
    ])
    exams.value = examRes
    myRecords.value = recordRes
  } catch (error) {
    ElMessage.error('获取数据失败')
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
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
  const texts = { draft: '草稿', published: '进行中', closed: '已结束' }
  return texts[status] || status
}

const canStart = (exam) => {
  const now = new Date()
  const start = new Date(exam.start_time)
  const end = new Date(exam.end_time)
  return exam.status === 'published' && now >= start && now <= end
}

const getStartButtonText = (exam) => {
  if (exam.status !== 'published') return '未发布'
  const now = new Date()
  if (now < new Date(exam.start_time)) return '未开始'
  if (now > new Date(exam.end_time)) return '已结束'
  return '开始考试'
}

const startExam = async (examId) => {
  try {
    await examsAPI.start(examId)
    router.push(`/exam/${examId}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '无法开始考试')
  }
}
</script>

<style scoped>
.exam-list-container {
  min-height: 100vh;
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

.header-content h2 {
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-main {
  padding: 20px;
}

.admin-links {
  margin-bottom: 20px;
}

.section-title {
  margin-bottom: 20px;
  color: #333;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.exam-card {
  margin-bottom: 20px;
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exam-title {
  font-weight: bold;
  font-size: 16px;
}

.exam-info p {
  margin: 8px 0;
  color: #666;
}

.exam-actions {
  margin-top: 15px;
  text-align: center;
}
</style>

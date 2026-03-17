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
          <h3>成绩统计</h3>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>选择考核查看统计</span>
              <el-select v-model="selectedExam" placeholder="请选择考核" @change="handleExamChange">
                <el-option 
                  v-for="exam in exams" 
                  :key="exam.id" 
                  :label="exam.title" 
                  :value="exam.id" 
                />
              </el-select>
            </div>
          </template>
          
          <div v-if="selectedExamStats">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="参加人数" :value="selectedExamStats.total_participants" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="平均分" :value="selectedExamStats.avg_score" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="及格率" :value="selectedExamStats.pass_rate" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="最高分" :value="selectedExamStats.max_score" suffix="%" />
              </el-col>
            </el-row>
            
            <div ref="scoreChart" style="height: 350px; margin-top: 30px"></div>
          </div>
          
          <el-empty v-else description="请选择一个考核" />
        </el-card>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>成绩明细</span>
              <el-button type="primary" @click="exportScores" :disabled="!records.length">
                导出成绩
              </el-button>
            </div>
          </template>
          
          <el-table :data="records" v-loading="loading">
            <el-table-column prop="username" label="工号" width="120" />
            <el-table-column prop="user_name" label="姓名" width="120" />
            <el-table-column prop="exam_title" label="考核名称" />
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
                {{ formatTime(row.submitted_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { examsAPI, recordsAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const exams = ref([])
const records = ref([])
const selectedExam = ref(null)
const selectedExamStats = ref(null)
const loading = ref(false)
const scoreChart = ref(null)

let chartInstance = null

onMounted(async () => {
  await fetchExams()
})

const fetchExams = async () => {
  try {
    const data = await examsAPI.list()
    exams.value = data
    if (data.length > 0) {
      selectedExam.value = data[0].id
    }
  } catch (error) {
    console.error('Failed to fetch exams', error)
  }
}

const handleExamChange = async (examId) => {
  await Promise.all([
    fetchExamStats(examId),
    fetchRecords(examId)
  ])
}

const fetchExamStats = async (examId) => {
  try {
    selectedExamStats.value = await recordsAPI.getExamStats(examId)
    updateChart()
  } catch (error) {
    console.error('Failed to fetch stats', error)
  }
}

const fetchRecords = async (examId) => {
  loading.value = true
  try {
    records.value = await recordsAPI.list({ exam_id: examId })
  } catch (error) {
    console.error('Failed to fetch records', error)
  } finally {
    loading.value = false
  }
}

const updateChart = () => {
  if (!scoreChart.value || !selectedExamStats.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(scoreChart.value)
  }
  
  const passing = Math.round(selectedExamStats.value.total_participants * selectedExamStats.value.pass_rate / 100)
  const failing = selectedExamStats.value.total_participants - passing
  
  const option = {
    title: {
      text: '及格/不及格分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      bottom: 10,
      left: 'center'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}人'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: passing, name: '及格', itemStyle: { color: '#67c23a' } },
          { value: failing, name: '不及格', itemStyle: { color: '#f56c6c' } }
        ]
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const exportScores = () => {
  if (!records.value.length || !selectedExamStats.value) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  // Create CSV content
  const exam = exams.value.find(e => e.id === selectedExam.value)
  const csvRows = []

  // Add header with exam info
  csvRows.push(`考核名称：${exam ? exam.title : '未知'}`)
  csvRows.push(`统计日期：${new Date().toLocaleString('zh-CN')}`)
  csvRows.push('')

  // Add statistics summary
  csvRows.push('统计摘要')
  csvRows.push(`参加人数：${selectedExamStats.value.total_participants}`)
  csvRows.push(`平均分：${selectedExamStats.value.avg_score}%`)
  csvRows.push(`及格率：${selectedExamStats.value.pass_rate}%`)
  csvRows.push(`最高分：${selectedExamStats.value.max_score}%`)
  csvRows.push(`最低分：${selectedExamStats.value.min_score}%`)
  csvRows.push('')

  // Add table header
  csvRows.push('工号,姓名,得分/总分,得分率,是否及格,提交时间')

  // Add data rows
  records.value.forEach(record => {
    const row = [
      record.username,
      record.user_name,
      `${record.score}/${record.total_score}`,
      `${record.percentage}%`,
      record.is_passed ? '及格' : '不及格',
      formatTime(record.submitted_at)
    ]
    csvRows.push(row.join(','))
  })

  // Create CSV file
  const csvContent = '\uFEFF' + csvRows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')

  const fileName = `${exam ? exam.title : '成绩'}_${new Date().getTime()}.csv`
  link.href = URL.createObjectURL(blob)
  link.download = fileName
  link.click()

  ElMessage.success('导出成功')
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

watch(selectedExam, (newVal) => {
  if (newVal) {
    handleExamChange(newVal)
  }
})
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

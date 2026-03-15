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
          <h3>管理后台</h3>
          <div class="user-info">
            <span>{{ userStore.user?.name }}</span>
            <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic title="员工总数" :value="stats.total_users" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic title="考核总数" :value="stats.total_exams" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic title="考试记录" :value="stats.total_records" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <el-statistic title="平均分" :value="stats.avg_score" suffix="%" />
            </el-card>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>及格率</span>
              </template>
              <div ref="passRateChart" style="height: 300px"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>快速操作</span>
              </template>
              <el-space direction="vertical" :size="15" style="width: 100%">
                <el-button type="primary" style="width: 100%" @click="$router.push('/admin/exams')">
                  创建新考核
                </el-button>
                <el-button type="success" style="width: 100%" @click="$router.push('/admin/users')">
                  添加员工
                </el-button>
                <el-button type="info" style="width: 100%" @click="$router.push('/admin/scores')">
                  查看成绩统计
                </el-button>
              </el-space>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { recordsAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const passRateChart = ref(null)

const stats = ref({
  total_users: 0,
  total_exams: 0,
  total_records: 0,
  avg_score: 0,
  pass_rate: 0
})

onMounted(async () => {
  await fetchStats()
  initChart()
})

const fetchStats = async () => {
  try {
    const data = await recordsAPI.getStats()
    stats.value = data
  } catch (error) {
    console.error('Failed to fetch stats', error)
  }
}

const initChart = () => {
  if (!passRateChart.value) return
  
  const chart = echarts.init(passRateChart.value)
  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        splitNumber: 8,
        axisLine: {
          lineStyle: {
            width: 6,
            color: [
              [0.3, '#fd666d'],
              [0.7, '#e6a23c'],
              [1, '#67c23a']
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '12%',
          width: 20,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: 'auto'
          }
        },
        axisTick: {
          length: 12,
          lineStyle: {
            color: 'auto',
            width: 2
          }
        },
        splitLine: {
          length: 20,
          lineStyle: {
            color: 'auto',
            width: 5
          }
        },
        axisLabel: {
          color: '#464646',
          fontSize: 12,
          distance: -60
        },
        title: {
          offsetCenter: [0, '-10%'],
          fontSize: 16
        },
        detail: {
          fontSize: 30,
          offsetCenter: [0, '0%'],
          valueAnimation: true,
          formatter: '{value}%',
          color: 'auto'
        },
        data: [
          {
            value: stats.value.pass_rate,
            name: '及格率'
          }
        ]
      }
    ]
  }
  chart.setOption(option)
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

.el-menu {
  border: none;
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

.header-content h3 {
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-main {
  background-color: #f0f2f5;
}
</style>

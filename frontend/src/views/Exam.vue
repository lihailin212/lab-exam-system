<template>
  <div class="exam-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h3>{{ examInfo?.title }}</h3>
          <div class="timer">
            <el-tag :type="timeLeft < 300 ? 'danger' : 'primary'" size="large">
              剩余时间: {{ formatDuration(timeLeft) }}
            </el-tag>
          </div>
        </div>
      </el-header>
      
      <el-main v-if="questions.length">
        <div class="progress-bar">
          <span>进度: {{ currentIndex + 1 }} / {{ questions.length }}</span>
          <el-progress 
            :percentage="((currentIndex + 1) / questions.length) * 100" 
            :stroke-width="8"
          />
        </div>
        
        <el-card class="question-card">
          <template #header>
            <div class="question-header">
              <span class="question-type">
                {{ getQuestionTypeText(questions[currentIndex].question_type) }}
              </span>
              <span class="question-score">({{ questions[currentIndex].score }}分)</span>
            </div>
          </template>
          
          <div class="question-content" v-html="questions[currentIndex].content"></div>
          
          <div class="options">
            <template v-if="questions[currentIndex].question_type === 'single'">
              <el-radio-group v-model="answers[questions[currentIndex].id]">
                <el-radio
                  v-for="opt in questions[currentIndex].options"
                  :key="opt.id"
                  :label="opt.id"
                  class="option-item"
                >
                  <span class="option-id">{{ opt.id }}.</span>
                  <span v-html="opt.content"></span>
                </el-radio>
              </el-radio-group>
            </template>

            <template v-else-if="questions[currentIndex].question_type === 'multiple'">
              <el-checkbox-group v-model="multipleAnswers[questions[currentIndex].id]">
                <el-checkbox
                  v-for="opt in questions[currentIndex].options"
                  :key="opt.id"
                  :label="opt.id"
                  class="option-item"
                >
                  <span class="option-id">{{ opt.id }}.</span>
                  <span v-html="opt.content"></span>
                </el-checkbox>
              </el-checkbox-group>
              <p class="multi-tip">（多选题，可选择多个答案）</p>
            </template>

            <template v-else-if="questions[currentIndex].question_type === 'judgment'">
              <el-radio-group v-model="answers[questions[currentIndex].id]">
                <el-radio label="true" class="option-item">正确</el-radio>
                <el-radio label="false" class="option-item">错误</el-radio>
              </el-radio-group>
            </template>

            <template v-else-if="questions[currentIndex].question_type === 'shared_option'">
              <div class="shared-option-container">
                <el-select
                  v-model="answers[questions[currentIndex].id]"
                  placeholder="请选择答案"
                  size="large"
                  style="width: 100%"
                >
                  <el-option
                    v-for="opt in questions[currentIndex].options"
                    :key="opt.id"
                    :label="`${opt.id}. ${opt.content}`"
                    :value="opt.id"
                  />
                </el-select>
                <p class="option-tip">（请从下拉框中选择正确答案）</p>
              </div>
            </template>
          </div>
        </el-card>
        
        <div class="navigation">
          <el-button @click="prevQuestion" :disabled="currentIndex === 0">
            上一题
          </el-button>
          
          <div class="question-dots">
            <span 
              v-for="(q, idx) in questions" 
              :key="q.id"
              :class="['dot', { active: idx === currentIndex, answered: isAnswered(q.id) }]"
              @click="goToQuestion(idx)"
            >
              {{ idx + 1 }}
            </span>
          </div>
          
          <el-button 
            v-if="currentIndex < questions.length - 1" 
            type="primary" 
            @click="nextQuestion"
          >
            下一题
          </el-button>
          
          <el-button 
            v-else 
            type="success" 
            @click="handleSubmit"
            :loading="submitting"
          >
            交卷
          </el-button>
        </div>
      </el-main>
      
      <el-main v-else>
        <el-empty description="暂无题目" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { examsAPI, recordsAPI } from '../api'

const router = useRouter()
const route = useRoute()

const examId = route.params.id
const examInfo = ref(null)
const questions = ref([])
const currentIndex = ref(0)
const answers = reactive({})
const multipleAnswers = reactive({})
const timeLeft = ref(0)
const submitting = ref(false)
let timer = null

onMounted(async () => {
  await fetchExam()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const fetchExam = async () => {
  try {
    const [examRes, startRes, questionsRes] = await Promise.all([
      examsAPI.get(examId),
      examsAPI.start(examId),
      examsAPI.getQuestions(examId)
    ])

    examInfo.value = examRes
    const allQuestions = questionsRes

    // 如果设置了随机抽取题目数量，随机选择题目
    if (examRes.total_questions && examRes.total_questions < allQuestions.length) {
      // 随机打乱题目数组
      const shuffled = [...allQuestions].sort(() => Math.random() - 0.5)
      // 选择指定数量的题目
      questions.value = shuffled.slice(0, examRes.total_questions)
    } else {
      questions.value = allQuestions
    }

    // Calculate time left
    const startResult = await examsAPI.start(examId)
    timeLeft.value = startResult.duration * 60

    // Start timer
    timer = setInterval(() => {
      timeLeft.value--
      if (timeLeft.value <= 0) {
        clearInterval(timer)
        autoSubmit()
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取考试信息失败')
    router.push('/')
  }
}

const formatDuration = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const getQuestionTypeText = (type) => {
  const texts = { single: '单选题', multiple: '多选题', judgment: '判断题', shared_option: '共用选项题' }
  return texts[type] || type
}

const isAnswered = (questionId) => {
  if (multipleAnswers[questionId]?.length) return true
  return !!answers[questionId]
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
  }
}

const prevQuestion = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const goToQuestion = (index) => {
  currentIndex.value = index
}

const handleSubmit = async () => {
  try {
    await ElMessageBox.confirm('确认提交试卷？提交后将无法修改', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await submitExam()
  } catch {}
}

const autoSubmit = async () => {
  ElMessage.warning('考试时间到，自动提交')
  await submitExam()
}

const submitExam = async () => {
  if (timer) clearInterval(timer)
  submitting.value = true
  
  try {
    // Convert answers to submit format
    const submitAnswers = []
    for (const q of questions.value) {
      let answer = answers[q.id] || ''
      
      if (q.question_type === 'multiple') {
        const multiAns = multipleAnswers[q.id] || []
        answer = multiAns.join(',')
      }
      
      submitAnswers.push({
        question_id: q.id,
        answer: answer
      })
    }
    
    const result = await recordsAPI.submit({
      exam_id: parseInt(examId),
      answers: submitAnswers
    })
    
    ElMessage.success(`考试完成！得分：${result.score}/${result.total_score} (${result.percentage}%)`)
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.exam-container {
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

.header-content h3 {
  margin: 0;
}

.el-main {
  max-width: 800px;
  margin: 0 auto;
}

.progress-bar {
  margin-bottom: 20px;
}

.question-card {
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.question-type {
  font-weight: bold;
  color: #409eff;
}

.question-score {
  color: #f56c6c;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 20px;
}

.question-content :deep(img) {
  max-width: 100%;
}

.options {
  margin-top: 20px;
}

.option-item {
  display: block;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100%;
}

.option-item:hover {
  background-color: #f5f7fa;
}

.option-id {
  font-weight: bold;
  margin-right: 5px;
}

.multi-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

.shared-option-container {
  margin-top: 20px;
}

.option-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

.navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.question-dots {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: center;
}

.dot {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
}

.dot.active {
  background-color: #409eff;
  color: white;
}

.dot.answered {
  background-color: #67c23a;
  color: white;
}
</style>

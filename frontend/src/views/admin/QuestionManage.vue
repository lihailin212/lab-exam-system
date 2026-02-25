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
          <h3>题目管理 - {{ examInfo?.title }}</h3>
          <div>
            <el-button type="primary" @click="showAddDialog">添加题目</el-button>
            <el-button @click="$router.push('/admin/exams')">返回</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <el-table :data="questions" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="question_type" label="题型" width="100">
              <template #default="{ row }">
                <el-tag>{{ getTypeText(row.question_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="题干">
              <template #default="{ row }">
                <div v-html="truncate(row.content, 50)"></div>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="分值" width="80" />
            <el-table-column label="答案" width="100">
              <template #default="{ row }">
                <el-tag type="success">{{ row.answer }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
    
    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑题目' : '添加题目'" width="700px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="题型" prop="question_type">
          <el-radio-group v-model="form.question_type">
            <el-radio label="single">单选题</el-radio>
            <el-radio label="multiple">多选题</el-radio>
            <el-radio label="judgment">判断题</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="题干" prop="content">
          <el-input 
            v-model="form.content" 
            type="textarea" 
            :rows="4" 
            placeholder="支持HTML格式，可插入图片"
          />
          <el-button size="small" @click="showImageUploader = true">插入图片</el-button>
        </el-form-item>
        
        <el-form-item label="选项" v-if="form.question_type !== 'judgment'">
          <div v-for="(opt, idx) in form.options" :key="idx" class="option-row">
            <el-input v-model="opt.id" placeholder="选项ID" style="width: 80px" />
            <el-input v-model="opt.content" placeholder="选项内容" style="flex: 1" />
            <el-button type="danger" @click="removeOption(idx)">删除</el-button>
          </div>
          <el-button type="primary" plain @click="addOption">添加选项</el-button>
        </el-form-item>
        
        <el-form-item label="正确答案" prop="answer">
          <el-input 
            v-model="form.answer" 
            :placeholder="getAnswerPlaceholder()"
          />
          <div class="form-tip">
            单选/判断：输入选项ID（如A）；多选：输入多个选项ID，用逗号分隔（如A,B,C）
          </div>
        </el-form-item>
        
        <el-form-item label="分值" prop="score">
          <el-input-number v-model="form.score" :min="1" :max="100" />
        </el-form-item>
        
        <el-form-item label="解析">
          <el-input v-model="form.explanation" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- Image Uploader Dialog -->
    <el-dialog v-model="showImageUploader" title="上传图片" width="400px">
      <el-upload
        :auto-upload="false"
        :on-change="handleImageChange"
        :limit="1"
        accept="image/*"
      >
        <el-button type="primary">选择图片</el-button>
      </el-upload>
      <div v-if="uploadedImageUrl" class="uploaded-image">
        <img :src="uploadedImageUrl" alt="uploaded" />
        <el-button size="small" @click="insertImage">插入图片</el-button>
      </div>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { examsAPI, questionsAPI } from '../api'

const router = useRouter()
const route = useRoute()

const examId = route.params.examId
const activeMenu = computed(() => `/admin/exams`)

const examInfo = ref(null)
const questions = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const showImageUploader = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const uploadedImageUrl = ref('')

const form = reactive({
  question_type: 'single',
  content: '',
  options: [
    { id: 'A', content: '' },
    { id: 'B', content: '' },
    { id: 'C', content: '' },
    { id: 'D', content: '' }
  ],
  answer: '',
  explanation: '',
  score: 10
})

const rules = {
  content: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入正确答案', trigger: 'blur' }]
}

onMounted(() => {
  fetchData()
})

const fetchData = async () => {
  loading.value = true
  try {
    const [examRes, questionsRes] = await Promise.all([
      examsAPI.get(examId),
      questionsAPI.get(examId)
    ])
    examInfo.value = examRes
    questions.value = questionsRes
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const truncate = (str, len) => {
  if (!str) return ''
  return str.replace(/<[^>]+>/g, '').slice(0, len) + (str.length > len ? '...' : '')
}

const getTypeText = (type) => {
  const texts = { single: '单选', multiple: '多选', judgment: '判断' }
  return texts[type] || type
}

const getAnswerPlaceholder = () => {
  if (form.question_type === 'multiple') return 'A,B,C'
  return 'A'
}

const addOption = () => {
  const ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
  form.options.push({
    id: ids[form.options.length],
    content: ''
  })
}

const removeOption = (index) => {
  form.options.splice(index, 1)
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    question_type: 'single',
    content: '',
    options: [
      { id: 'A', content: '' },
      { id: 'B', content: '' },
      { id: 'C', content: '' },
      { id: 'D', content: '' }
    ],
    answer: '',
    explanation: '',
    score: 10
  })
  dialogVisible.value = true
}

const showEditDialog = (question) => {
  isEdit.value = true
  form.id = question.id
  form.question_type = question.question_type
  form.content = question.content
  form.options = question.options || []
  form.answer = question.answer
  form.explanation = question.explanation || ''
  form.score = question.score
  dialogVisible.value = true
}

const handleImageChange = async (file) => {
  try {
    const res = await questionsAPI.uploadImage(file.raw)
    uploadedImageUrl.value = res.url
    ElMessage.success('图片上传成功')
  } catch (error) {
    ElMessage.error('图片上传失败')
  }
}

const insertImage = () => {
  form.content += `<img src="${uploadedImageUrl.value}" alt="image" />`
  showImageUploader.value = false
  uploadedImageUrl.value = ''
}

const handleSubmit = async () => {
  if (!form.content) {
    ElMessage.warning('请输入题干')
    return
  }
  
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('question_type', form.question_type)
    formData.append('content', form.content)
    formData.append('options', JSON.stringify(form.options.filter(o => o.content)))
    formData.append('answer', form.answer)
    formData.append('explanation', form.explanation || '')
    formData.append('score', form.score.toString())
    
    if (isEdit.value) {
      await questionsAPI.update(form.id, formData)
      ElMessage.success('更新成功')
    } else {
      await questionsAPI.create(examId, formData)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (question) => {
  try {
    await ElMessageBox.confirm('确定要删除这道题目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await questionsAPI.delete(question.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
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

.option-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.uploaded-image {
  margin-top: 15px;
  text-align: center;
}

.uploaded-image img {
  max-width: 100%;
  max-height: 200px;
  margin-bottom: 10px;
}
</style>

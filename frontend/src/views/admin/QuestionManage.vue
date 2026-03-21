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
            <el-button type="warning" @click="showSharedOptionDialog">管理共用选项</el-button>
            <el-button type="success" @click="openImportDialog">批量导入</el-button>
            <el-button type="info" @click="handleExport">批量导出</el-button>
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
            <el-radio label="shared_option">共用选项题</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 共用选项组选择 -->
        <el-form-item label="选项组" v-if="form.question_type === 'shared_option'">
          <el-select v-model="form.shared_option_group_id" placeholder="请选择共用选项组" style="width: 100%">
            <el-option
              v-for="group in sharedOptionGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            >
              <div>
                <span>{{ group.name }}</span>
                <el-tag size="small" style="margin-left: 10px">
                  {{ group.options.map(o => o.id).join(', ') }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <p v-if="sharedOptionGroups.length === 0" class="form-tip" style="color: #f56c6c">
            暂无共用选项组，请先点击"管理共用选项"创建选项组
          </p>
        </el-form-item>

        <!-- 共用选项组预览 -->
        <el-form-item label="选项预览" v-if="form.question_type === 'shared_option' && selectedSharedGroup">
          <el-table :data="selectedSharedGroup.options" size="small" border>
            <el-table-column prop="id" label="选项ID" width="100" />
            <el-table-column prop="content" label="选项内容" />
          </el-table>
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
        
        <el-form-item label="选项" v-if="form.question_type !== 'judgment' && form.question_type !== 'shared_option'">
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

    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" :title="`批量导入${importType === 'shared_options' ? '共用选项组' : '题目'}`" width="600px">
      <div class="import-tip">
        <p>请上传 Excel、Word 或 TXT 文件进行批量导入</p>
        <el-button type="primary" link @click="downloadTemplate">
          下载导入模板
        </el-button>
      </div>
      
      <el-upload
        v-if="!importResult"
        ref="importRef"
        :auto-upload="false"
        :on-change="handleImportFileChange"
        :limit="1"
        accept=".xlsx,.xls,.docx,.txt,.csv"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls, .docx, .txt, .csv 格式
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

    <!-- Shared Option Group Management Dialog -->
    <el-dialog v-model="sharedOptionDialogVisible" title="管理共用选项组" width="800px">
      <div class="shared-option-header">
        <el-button type="primary" @click="showAddSharedOptionGroup">新建选项组</el-button>
        <el-button type="success" @click="handleImportSharedOptions">导入选项组</el-button>
        <el-button type="info" @click="handleExportSharedOptions">导出选项组</el-button>
      </div>

      <el-table :data="sharedOptionGroups" v-loading="sharedOptionLoading" border>
        <el-table-column prop="name" label="选项组名称" />
        <el-table-column label="选项内容">
          <template #default="{ row }">
            <el-tag v-for="opt in row.options" :key="opt.id" size="small" style="margin: 2px">
              {{ opt.id }}: {{ opt.content }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editSharedOptionGroup(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSharedOptionGroup(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="sharedOptionDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Shared Option Group Add/Edit Dialog -->
    <el-dialog v-model="sharedOptionGroupFormVisible" :title="isEditSharedGroup ? '编辑选项组' : '新建选项组'" width="600px">
      <el-form :model="sharedOptionGroupForm" label-width="100px">
        <el-form-item label="选项组名称" required>
          <el-input v-model="sharedOptionGroupForm.name" placeholder="例如：严重度等级"
            maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="选项列表">
          <div v-for="(opt, idx) in sharedOptionGroupForm.options" :key="idx" class="option-row">
            <el-input v-model="opt.id" placeholder="ID" style="width: 80px" />
            <el-input v-model="opt.content" placeholder="选项内容" style="flex: 1" />
            <el-button type="danger" @click="removeSharedOption(idx)">删除</el-button>
          </div>
          <el-button type="primary" plain @click="addSharedOption">添加选项</el-button>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="sharedOptionGroupFormVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSharedOptionGroup" :loading="savingSharedGroup">
          保存
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { examsAPI, questionsAPI, sharedOptionGroupsAPI } from '@/api'

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

const showImportDialog = ref(false)
const importType = ref('questions') // 'questions' or 'shared_options'
const importRef = ref(null)
const selectedFile = ref(null)
const importing = ref(false)
const importResult = ref(null)

// Shared Option Groups
const sharedOptionGroups = ref([])
const sharedOptionLoading = ref(false)
const sharedOptionDialogVisible = ref(false)
const sharedOptionGroupFormVisible = ref(false)
const isEditSharedGroup = ref(false)
const savingSharedGroup = ref(false)
const sharedOptionGroupForm = reactive({
  id: null,
  name: '',
  options: [
    { id: 'A', content: '' },
    { id: 'B', content: '' },
    { id: 'C', content: '' }
  ]
})

const selectedSharedGroup = computed(() => {
  if (form.shared_option_group_id) {
    return sharedOptionGroups.value.find(g => g.id === form.shared_option_group_id)
  }
  return null
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
    const [examRes, questionsRes, groupsRes] = await Promise.all([
      examsAPI.get(examId),
      questionsAPI.get(examId),
      sharedOptionGroupsAPI.list(examId)
    ])
    examInfo.value = examRes
    questions.value = questionsRes
    sharedOptionGroups.value = groupsRes
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
  const texts = { single: '单选', multiple: '多选', judgment: '判断', shared_option: '共用选项' }
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
    score: 10,
    shared_option_group_id: null
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
  form.shared_option_group_id = question.shared_option_group_id || null
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
    formData.append('answer', form.answer)
    formData.append('explanation', form.explanation || '')
    formData.append('score', form.score.toString())

    if (form.question_type === 'shared_option') {
      if (!form.shared_option_group_id) {
        ElMessage.warning('请选择共用选项组')
        return
      }
      formData.append('shared_option_group_id', form.shared_option_group_id.toString())
    } else {
      formData.append('options', JSON.stringify(form.options.filter(o => o.content)))
    }

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
    const res = await questionsAPI.import(examId, selectedFile.value)
    importResult.value = res
    if (res.success_count > 0) {
      ElMessage.success(res.message)
      fetchData()
    } else if (res.error_count > 0) {
      ElMessage.warning(res.message)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  const templateContent = `题型,题干,选项,答案,解析,分值
single,示例单选题,A:选项A|B:选项B|C:选项C|D:选项D,A,这是解析,10
multiple,示例多选题,A:选项A|B:选项B|C:选项C|D:选项D,A,B,C,这是解析,10
judgment,示例判断题,,正确,这是解析,5
shared_option,示例共用选项题,,A,这是共用选项题的题干，选项从共用选项组中选择,10`

  const link = document.createElement('a')
  link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent('\uFEFF' + templateContent)
  link.download = '导入模板.csv'
  link.click()
}

const openImportDialog = () => {
  showImportDialog.value = true
  selectedFile.value = null
  importResult.value = null
}

const handleExport = () => {
  if (questions.value.length === 0) {
    ElMessage.warning('当前没有题目可导出')
    return
  }

  // Build CSV content
  const headers = ['题型', '题干', '选项', '答案', '解析', '分值']
  const rows = questions.value.map(q => {
    const typeMap = {
      'single': '单选题',
      'multiple': '多选题',
      'judgment': '判断题',
      'shared_option': '共用选项题'
    }
    const type = typeMap[q.question_type] || q.question_type

    // Format options
    let options = ''
    if (q.options && q.options.length > 0) {
      options = q.options.map(opt => `${opt.id}:${opt.content}`).join('|')
    }

    // Format answer
    let answer = q.answer
    if (q.question_type === 'judgment') {
      answer = q.answer === 'true' ? '正确' : '错误'
    }

    return [
      type,
      q.content || '',
      options,
      answer || '',
      q.explanation || '',
      q.score || 10
    ]
  })

  // Convert to CSV
  const csvContent = '\uFEFF' + [headers, ...rows].map(row =>
    row.map(cell => {
      // Escape cells containing commas, quotes, or newlines
      const cellStr = String(cell).replace(/"/g, '""')
      if (cellStr.includes(',') || cellStr.includes('\n') || cellStr.includes('"')) {
        return `"${cellStr}"`
      }
      return cellStr
    }).join(',')
  ).join('\n')

  // Download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${examInfo.value?.title || '考核'}_题目导出_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(link.href)

  ElMessage.success(`成功导出 ${questions.value.length} 道题目`)
}

const closeImportDialog = () => {
  showImportDialog.value = false
  selectedFile.value = null
  importResult.value = null
}

// Shared Option Group Functions
const showSharedOptionDialog = () => {
  sharedOptionDialogVisible.value = true
}

const showAddSharedOptionGroup = () => {
  isEditSharedGroup.value = false
  sharedOptionGroupForm.id = null
  sharedOptionGroupForm.name = ''
  sharedOptionGroupForm.options = [
    { id: 'A', content: '' },
    { id: 'B', content: '' },
    { id: 'C', content: '' }
  ]
  sharedOptionGroupFormVisible.value = true
}

const editSharedOptionGroup = (group) => {
  isEditSharedGroup.value = true
  sharedOptionGroupForm.id = group.id
  sharedOptionGroupForm.name = group.name
  sharedOptionGroupForm.options = group.options.map(opt => ({ ...opt }))
  sharedOptionGroupFormVisible.value = true
}

const addSharedOption = () => {
  const ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
  sharedOptionGroupForm.options.push({
    id: ids[sharedOptionGroupForm.options.length],
    content: ''
  })
}

const removeSharedOption = (index) => {
  sharedOptionGroupForm.options.splice(index, 1)
}

const saveSharedOptionGroup = async () => {
  if (!sharedOptionGroupForm.name) {
    ElMessage.warning('请输入选项组名称')
    return
  }
  if (sharedOptionGroupForm.options.length < 2) {
    ElMessage.warning('至少需要2个选项')
    return
  }
  if (!sharedOptionGroupForm.options.every(opt => opt.id && opt.content)) {
    ElMessage.warning('请填写所有选项的ID和内容')
    return
  }

  savingSharedGroup.value = true
  try {
    if (isEditSharedGroup.value) {
      await sharedOptionGroupsAPI.update(sharedOptionGroupForm.id, sharedOptionGroupForm)
      ElMessage.success('更新成功')
    } else {
      await sharedOptionGroupsAPI.create(examId, sharedOptionGroupForm)
      ElMessage.success('创建成功')
    }
    sharedOptionGroupFormVisible.value = false
    fetchData() // Refresh to show updated groups
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    savingSharedGroup.value = false
  }
}

const handleImportSharedOptions = () => {
  openImportDialog.value = true
  importType.value = 'shared_options'
}

const handleExportSharedOptions = () => {
  if (sharedOptionGroups.value.length === 0) {
    ElMessage.warning('没有选项组可导出')
    return
  }

  const data = sharedOptionGroups.value.map(group => ({
    '选项组名称': group.name,
    '选项列表': group.options.map(opt => `${opt.id}:${opt.content}`).join('|')
  }))

  const csvContent = '\uFEFF' + [
    Object.keys(data[0]).join(','),
    ...data.map(row => Object.values(row).map(cell => {
      const cellStr = String(cell).replace(/"/g, '\"\"')
      if (cellStr.includes(',') || cellStr.includes('\n') || cellStr.includes('"')) {
        return `"${cellStr}"`
      }
      return cellStr
    }).join(','))
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `共用选项组_${examInfo.value?.title || '考核'}_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(link.href)

  ElMessage.success(`成功导出 ${sharedOptionGroups.value.length} 个选项组`)
}

const deleteSharedOptionGroup = async (group) => {
  try {
    await ElMessageBox.confirm('确定要删除该共用选项组吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await sharedOptionGroupsAPI.delete(group.id)
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

.import-tip {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.import-tip p {
  margin: 0 0 10px 0;
  color: #606266;
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

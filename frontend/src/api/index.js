import axios from 'axios'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || '') + '/api',
  timeout: 30000
})

// Request interceptor
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  getUserInfo: () => api.get('/auth/me'),
  register: (data) => api.post('/auth/register', data)
}

// Users API
export const usersAPI = {
  list: (params) => api.get('/users', { params }),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  resetPassword: (id, password) => api.post(`/users/reset-password/${id}`, null, { params: { new_password: password } })
}

// Exams API
export const examsAPI = {
  list: (params) => api.get('/exams', { params }),
  getActive: () => api.get('/exams/active'),
  get: (id) => api.get(`/exams/${id}`),
  create: (data) => api.post('/exams', data),
  update: (id, data) => api.put(`/exams/${id}`, data),
  delete: (id) => api.delete(`/exams/${id}`),
  publish: (id) => api.post(`/exams/${id}/publish`),
  close: (id) => api.post(`/exams/${id}/close`),
  getQuestions: (id) => api.get(`/exams/${id}/questions`),
  start: (id) => api.post(`/exams/${id}/start`)
}

// Questions API
export const questionsAPI = {
  create: (examId, data) => api.post(`/questions/exam/${examId}`, data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id, data) => api.put(`/questions/${id}`, data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  delete: (id) => api.delete(`/questions/${id}`),
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/questions/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  import: (examId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/questions/import/exam/${examId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  get: (examId) => api.get(`/questions/exam/${examId}`)
}

// Records API
export const recordsAPI = {
  my: () => api.get('/records/my'),
  list: (params) => api.get('/records', { params }),
  get: (id) => api.get(`/records/${id}`),
  getExamStats: (examId) => api.get(`/records/exam/${examId}/stats`),
  getStats: () => api.get('/records/stats'),
  submit: (data) => api.post('/records/submit', data)
}

export default api

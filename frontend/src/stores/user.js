import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authAPI } from '../api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const login = async (username, password) => {
    const res = await authAPI.login({ username, password })
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchUserInfo()
    return res
  }

  const setToken = async (accessToken) => {
    token.value = accessToken
    localStorage.setItem('token', accessToken)
    await fetchUserInfo()
  }

  const fetchUserInfo = async () => {
    try {
      const res = await authAPI.getUserInfo()
      user.value = res
      return res
    } catch (error) {
      logout()
      throw error
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  const isAdmin = () => {
    return user.value?.role === 'admin'
  }

  return {
    token,
    user,
    login,
    logout,
    fetchUserInfo,
    setToken,
    isAdmin
  }
})

import axios from 'axios'

const client = axios.create({
  baseURL: '/',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const register = (email, password) =>
  client.post('/auth/register', { email, password })

export const login = (email, password) => {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)
  return client.post('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

// Papers
export const getPapers = () => client.get('/papers')

export const uploadPaper = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return client.post('/papers/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const analyzePaper = (paperId) =>
  client.post(`/papers/${paperId}/analyze`)

export const getPaperInsights = (paperId) =>
  client.get(`/papers/${paperId}/insights`)

export const getPaper = (paperId) =>
  client.get(`/papers/${paperId}`)

// Chatbot
export const sendChatMessage = (message) =>
  client.post('/papers/chatbot/', { message })

export const getChatHistory = () =>
  client.get('/papers/chatbot/')

export default client

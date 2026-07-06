const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'



const getToken = () => localStorage.getItem('token')

const setToken = (token) => localStorage.setItem('token', token)

const removeToken = () => {

  localStorage.removeItem('token')

  localStorage.removeItem('userInfo')

}

const isLoggedIn = () => !!getToken()

const getUserInfo = () => {

  const raw = localStorage.getItem('userInfo')

  return raw ? JSON.parse(raw) : null

}



const request = async (url, options = {}) => {

  const token = getToken()

  const config = {

    method: 'GET',

    headers: {

      'Content-Type': 'application/json',

      ...options.headers,

    },

    ...options,

  }



  if (token) {

    config.headers.Authorization = `Bearer ${token}`

  }



  const response = await fetch(`${API_BASE_URL}${url}`, config)

  const data = await response.json()



  if (!response.ok) {

    throw new Error(data.detail || 'Request failed')

  }

  return data

}



export const login = (email, password) =>

  request('/auth/login/json', {

    method: 'POST',

    body: JSON.stringify({ email, password }),

  })



export const register = (userData) =>

  request('/auth/register', {

    method: 'POST',

    body: JSON.stringify(userData),

  })



export const getCurrentUser = () => request('/auth/me')



export { getToken, setToken, removeToken, isLoggedIn, getUserInfo, API_BASE_URL }



export const createTask = (agentType = 'image_crawler', initialConfig = null) =>

  request('/tasks', {

    method: 'POST',

    body: JSON.stringify({

      agent_type: agentType,

      initial_config: initialConfig,

    }),

  })



export const chatWithAgent = (taskId, message) =>

  request(`/tasks/${taskId}/chat`, {

    method: 'POST',

    body: JSON.stringify({ task_id: taskId, message }),

  })



export const confirmTask = (taskId) =>

  request(`/tasks/${taskId}/confirm`, { method: 'POST' })



export const getChatHistory = (taskId) =>

  request(`/tasks/${taskId}/chat-history`)



export const listTasks = () => request('/tasks')



export const cancelTask = (taskId) =>

  request(`/tasks/${taskId}/cancel`, { method: 'POST' })



export const resumeTask = (taskId) =>

  request(`/tasks/${taskId}/resume`, { method: 'POST' })



export const deleteTask = (taskId) =>

  request(`/tasks/${taskId}`, { method: 'DELETE' })



export const renameTask = (taskId, name) =>

  request(`/tasks/${taskId}`, {

    method: 'PATCH',

    body: JSON.stringify({ name }),

  })



export const updateTaskConfig = (taskId, taskConfig) =>

  request(`/tasks/${taskId}`, {

    method: 'PATCH',

    body: JSON.stringify({ task_config: taskConfig }),

  })



export const subscribeTaskProgress = (taskId, onProgress, onComplete) => {

  const controller = new AbortController()

  const token = getToken()



  fetch(`${API_BASE_URL}/tasks/${taskId}/stream?token=${token}`, {

    headers: { Accept: 'text/event-stream' },

    signal: controller.signal,

  })

    .then((response) => {

      if (!response.ok) {

        throw new Error(`SSE error: ${response.status}`)

      }

      const reader = response.body.getReader()

      const decoder = new TextDecoder()

      let buffer = ''



      function read() {

        reader.read().then(({ done, value }) => {

          if (done) {

            onComplete?.()

            return

          }

          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')

          buffer = lines.pop() || ''

          for (const line of lines) {

            if (line.startsWith('data: ')) {

              try {

                const data = JSON.parse(line.slice(6))

                onProgress(data)

                if (['completed', 'cancelled', 'failed'].includes(data.status)) {

                  onComplete?.()

                  return

                }

              } catch (e) {}

            }

          }

          read()

        }).catch((err) => {

          if (err && err.name !== 'AbortError') console.warn('SSE read error:', err)

        })

      }

      read()

    })

    .catch((err) => {

      if (err.name !== 'AbortError') console.error('SSE error:', err)

    })



  return () => controller.abort()

}



export const listDatasets = () => request('/datasets')


export const listPublicDatasets = (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  ).toString()
  return request(`/datasets/public${qs ? `?${qs}` : ''}`)
}


export const getDataset = (datasetId) => request(`/datasets/${datasetId}`)


export const getPublicDataset = (datasetId) => request(`/datasets/public/${datasetId}`)


export const listPublicDatasetImages = (datasetId, params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  ).toString()
  return request(`/datasets/public/${datasetId}/images${qs ? `?${qs}` : ''}`)
}



export const createDataset = (data) =>

  request('/datasets', {

    method: 'POST',

    body: JSON.stringify(data),

  })



export const updateDataset = (datasetId, data) =>

  request(`/datasets/${datasetId}`, {

    method: 'PATCH',

    body: JSON.stringify(data),

  })



export const deleteDataset = (datasetId) =>

  request(`/datasets/${datasetId}`, {

    method: 'DELETE',

  })



export const publishDataset = (datasetId) =>

  request(`/datasets/${datasetId}/publish`, { method: 'POST' })



export const unpublishDataset = (datasetId) =>

  request(`/datasets/${datasetId}/unpublish`, { method: 'POST' })



export const pinDataset = (datasetId) =>

  request(`/datasets/${datasetId}/pin`, { method: 'POST' })



export const unpinDataset = (datasetId) =>

  request(`/datasets/${datasetId}/unpin`, { method: 'POST' })



export const saveDatasetFromTask = (taskId) =>

  request('/datasets/from-task', {

    method: 'POST',

    body: JSON.stringify({ task_id: taskId }),

  })



export const listDatasetImages = (datasetId, params = {}) => {

  const qs = new URLSearchParams(

    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')

  ).toString()

  return request(`/datasets/${datasetId}/images${qs ? `?${qs}` : ''}`)

}



export const deleteDatasetImage = (datasetId, imageId) =>

  request(`/datasets/${datasetId}/images/${imageId}`, {

    method: 'DELETE',

  })





export const patchDatasetImage = (datasetId, imageId, body) =>

  request(`/datasets/${datasetId}/images/${imageId}`, {

    method: 'PATCH',

    body: JSON.stringify(body),

  })





export const datasetImageUrl = (datasetId, relativePath, bustCache = false) => {
  // <img> tags cannot attach Authorization headers, so embed JWT in the query string
  // (the backend file endpoint accepts either header or ?token).
  const t = getToken()
  // Authenticated: use /datasets/{id}/files/ with ?token=
  // Guest/public: use /datasets/public/{id}/files/ (no token needed)
  const isPublic = !t
  const path = isPublic
    ? `${API_BASE_URL}/datasets/public/${datasetId}/files/${String(relativePath).replace(/^\/+/, '')}`
    : `${API_BASE_URL}/datasets/${datasetId}/files/${String(relativePath).replace(/^\/+/, '')}`
  let url = t ? `${path}?token=${encodeURIComponent(t)}` : path
  if (bustCache) {
    const sep = url.includes('?') ? '&' : '?'
    url += sep + '_t=' + Date.now()
  }
  return url
}
export const bulkUpdateDatasets = (body) =>

  request('/datasets/bulk-update', {

    method: 'POST',

    body: JSON.stringify(body),

  })



export const bulkUpdateDatasetImages = (datasetId, body) =>

  request(`/datasets/${datasetId}/images/bulk-update`, {

    method: 'POST',

    body: JSON.stringify(body),

  })


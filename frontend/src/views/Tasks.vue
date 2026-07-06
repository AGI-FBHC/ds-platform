<template>

  <div class="tasks-page">

    <div class="tasks-header">

      <h2>任务管理</h2>

      <button class="create-btn" @click="startNewTask" :disabled="creatingTask">

        <svg v-if="!creatingTask" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">

          <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>

          <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>

        </svg>

        <span v-if="creatingTask" class="spinner"></span>

        {{ creatingTask ? '创建中..' : '创建新任务' }}

      </button>

    </div>



    <!-- Tasks list -->

    <div class="tasks-list" v-if="tasks.length > 0">

      <div v-for="task in tasks" :key="task.id" class="task-card" :class="task.status">

        <div

          class="task-card-fill"

          :class="task.status"

          :style="{ width: task.progress + '%' }"

          v-if="task.status !== 'configuring'"

          aria-hidden="true"

        ></div>



        <div class="task-info">

          <div class="task-name">

            <span class="status-badge" :class="task.status">{{ statusText[task.status] }}</span>

            <span v-if="editingTaskId === task.id" class="rename-inline">

              <input

                v-model="editingName"

                class="rename-input"

                @keydown.enter="saveRename(task.id)"

                @keydown.escape="cancelRename"

                ref="renameInputRef"

                autofocus

              />

              <button class="app-btn icon-sm primary" @click="saveRename(task.id)">保存</button>

              <button class="app-btn icon-sm ghost" @click="cancelRename">取消</button>

            </span>

            <span v-else class="task-name-text" @dblclick="startRename(task)">{{ task.name }}</span>

            <span class="task-time">{{ formatTime(task.created_at) }}</span>

            <div class="task-name-actions">

              <button

                v-if="task.status === 'completed' || task.status === 'failed'"

                class="app-btn icon"

                @click="handleSaveToDb(task)"

                :disabled="savingToDb === task.id"

                title="保存到数据库"

                aria-label="保存到数据库"

              >

                <svg v-if="savingToDb !== task.id" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">

                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>

                  <polyline points="17 21 17 13 7 13 7 21"/>

                  <polyline points="7 3 7 8 15 8"/>

                </svg>

                <span v-else class="spinner" style="width:14px;height:14px;border-width:1.5px"></span>

              </button>

              <button

                v-if="['completed', 'cancelled', 'failed', 'configuring'].includes(task.status)"

                class="task-card-delete"

                :class="task.status"

                @click="handleDelete(task.id)"

                title="删除任务"

                aria-label="删除任务"

              >

                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">

                  <polyline points="3 6 5 6 21 6"/>

                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>

                  <path d="M10 11v6M14 11v6"/>

                  <path d="M9 6V4h6v2"/>

                </svg>

              </button>

            </div>

          </div>

        </div>




        <div class="task-summary-line" v-if="task.task_config && Object.keys(task.task_config).length > 0" @click="openDetail(task)">

          <span v-if="task.task_config.subject" class="summary-chip">{{ task.task_config.subject }}</span>

          <span v-if="task.task_config.classification_axes?.length" class="summary-chip">{{ task.task_config.classification_axes.length }} 个分类轴</span>

          <span v-if="task.task_config.max_count" class="summary-chip">{{ task.task_config.max_count }} 张</span>

          <span v-if="task.task_config.need_mask" class="summary-chip">含 Mask</span>

          <span v-if="task.task_config.format" class="summary-chip">{{ task.task_config.format }}</span>

          <span class="summary-detail-link"><span class="detail-link-text">查看详情</span><span class="detail-link-arrow">›</span></span>

        </div>



        <div class="task-message" v-if="task.message">{{ task.message }}</div>

        <div class="task-actions">

          <button

            v-if="task.status === 'configuring'"

            class="config-btn"

            @click="openChat(task)"

          >

            配置任务

          </button>

        <button

            v-if="task.status === 'running' || task.status === 'pending'"

            class="app-btn danger small"

            @click="handleCancel(task.id)"

          >

            取消

          </button>

          </div>

        <div class="task-progress-strip" v-if="task.status !== 'configuring'">

          <div class="task-progress-fill" :class="task.status" :style="{ width: task.progress + '%' }"></div>

          <span class="task-progress-pct">{{ task.progress }}%</span>

        </div>

      </div>

    </div>


    <el-dialog

      v-model="showDetail"

      width="640"

      :show-close="true"

      :close-on-click-modal="false"

      class="task-detail-dialog"

      align-center

      destroy-on-close

    >

      <template #header>

        <div class="detail-header">

          <span class="status-badge" :class="detailTask.status">{{ statusText[detailTask.status] }}</span>

          <span class="detail-title">{{ detailTask.name }}</span>

          <span class="detail-time">{{ formatTime(detailTask.created_at) }}</span>

        </div>

      </template>



      <div class="detail-body">

        <div class="detail-message" v-if="detailTask.message">{{ detailTask.message }}</div>



        <div class="detail-progress" v-if="detailTask.status !== 'configuring'">

          <div class="detail-progress-track">

            <div class="detail-progress-fill" :class="detailTask.status" :style="{ width: detailTask.progress + '%' }"></div>

          </div>

          <span class="detail-progress-pct">{{ detailTask.progress }}%</span>

        </div>



        <div v-if="detailTask.task_config && Object.keys(detailTask.task_config).length > 0" class="detail-config-summary">
          <span class="detail-config-count">已配置 {{ configFieldCount(detailTask.task_config) }} 项</span>
          <button class="app-btn outline small" @click="openConfigPreview(detailTask.task_config, detailTask.name)">完整配置</button>
        </div>

        <div v-else class="detail-empty">暂无配置信息</div>

      </div>



      <template #footer>

        <div class="detail-actions">

          <button

            v-if="detailTask.status === 'configuring'"

            class="app-btn primary"

            @click="openChatFromDetail"

          >配置任务</button>



          <button

            v-if="(detailTask.status === 'configuring' || detailTask.status === 'pending') && detailTask.task_config && !detailTask.task_config.search_items?.length"

            class="app-btn primary"

            @click="handleConfirmFromDetail"

            :disabled="confirming"

          >{{ confirming ? '启动中...' : '启动抓取' }}</button>



          <button

            v-if="detailTask.status === 'configuring' && detailTask.task_config && detailTask.task_config.search_items?.length"

            class="app-btn primary"

            @click="handleConfirmFromDetail"

            :disabled="confirming"

          >{{ confirming ? '启动中...' : '确认并启动' }}</button>



          <button

            v-if="detailTask.status === 'running' || detailTask.status === 'pending'"

            class="app-btn warn"

            @click="handleCancelFromDetail"

          >取消任务</button>



          <button

            v-if="detailTask.status === 'completed' || detailTask.status === 'failed'"

            class="app-btn primary"

            @click="handleSaveFromDetail"

            :disabled="savingToDb === detailTask.id"

          >

            <span v-if="savingToDb !== detailTask.id">保存到数据集</span>

            <span v-else class="spinner" style="width:14px;height:14px;border-width:1.5px"></span>

          </button>



          <button

            v-if="['cancelled', 'failed'].includes(detailTask.status)"

            class="app-btn primary"

            @click="handleResumeFromDetail"

            :disabled="resuming"

          >{{ resuming ? '打开中...' : '重新编辑并执行' }}</button>



          <button

            v-if="['completed', 'cancelled', 'failed', 'configuring'].includes(detailTask.status)"

            class="app-btn danger solid"

            @click="handleDeleteFromDetail"

          >删除任务</button>



          <button class="app-btn ghost" @click="showDetail = false">关闭</button>

        </div>

      </template>

    </el-dialog>


    <!-- Config preview / edit modal (opened from detail / chat dialogs) -->

    <el-dialog
      v-model="configPreviewVisible"
      title="配置预览 / 编辑"
      width="620"
      align-center
      destroy-on-close
      class="config-preview-dialog"
    >
      <div v-if="configPreviewTitle" class="config-preview-subtitle">{{ configPreviewTitle }}</div>
      <div class="config-preview-grid">
        <div v-for="(label, key) in fieldLabels" :key="key" v-show="previewConfig[key] !== undefined && previewConfig[key] !== null" class="config-preview-row">
          <label class="config-preview-label" :for="`preview-${key}`">{{ label }}</label>
          <div class="config-preview-input-wrap">
            <!-- Boolean: need_mask -->
            <label v-if="key === 'need_mask'" class="config-preview-toggle">
              <input
                :id="`preview-${key}`"
                type="checkbox"
                :checked="!!previewConfig[key]"
                @change="updatePreviewField(key, $event.target.checked)"
              />
              <span>{{ previewConfig[key] ? '需要' : '不需要' }}</span>
            </label>
            <!-- Number -->
            <input
              v-else-if="['max_count', 'min_width', 'min_height'].includes(key)"
              :id="`preview-${key}`"
              type="number"
              class="config-preview-input"
              :value="previewConfig[key]"
              @input="updatePreviewField(key, $event.target.value === '' ? null : Number($event.target.value))"
            />
            <!-- JSON arrays (keywords/tags/classification_axes/search_items) -->
            <textarea
              v-else-if="['keywords', 'tags', 'classification_axes', 'search_items'].includes(key)"
              :id="`preview-${key}`"
              class="config-preview-textarea"
              rows="4"
              :value="previewJsonDraft[key]"
              :class="{ invalid: previewJsonErrors[key] }"
              @input="updatePreviewJson(key, $event.target.value)"
              :placeholder="jsonPlaceholder(key)"
            />
            <span v-if="previewJsonErrors[key]" class="config-preview-error">{{ previewJsonErrors[key] }}</span>
            <!-- Plain string -->
            <input
              v-else
              :id="`preview-${key}`"
              type="text"
              class="config-preview-input"
              :value="previewConfig[key] || ''"
              @input="updatePreviewField(key, $event.target.value)"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="config-preview-footer">
          <button class="app-btn ghost" @click="copyPreviewJson">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            复制 JSON
          </button>
          <button class="app-btn ghost" @click="configPreviewVisible = false" :disabled="applyingPreview">取消</button>
          <button class="app-btn primary" @click="applyPreviewConfig" :disabled="!previewIsValid || applyingPreview">
            {{ applyingPreview ? '应用中...' : '保存到对话' }}
          </button>
        </div>
      </template>
    </el-dialog>


    <div v-if="tasks.length === 0" class="empty-state">

      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="64" height="64">

        <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="1.5"/>

        <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="1.5"/>

        <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="1.5"/>

      </svg>

      <h3>创建你的第一个数据集抓取任务</h3>

      <p>使用 任务管理 智能配置和批量获取图片数据集，点击上方「创建新任务」开始了</p>

    </div>



    <!-- Agent Chat Dialog -->

    <div v-if="showChat" class="chat-overlay" >

      <div class="chat-container">

        <div class="chat-header">

          <div class="chat-title">

            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="24" height="24">

              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>

              <path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>

              <line x1="9" y1="9" x2="9.01" y2="9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>

              <line x1="15" y1="9" x2="15.01" y2="9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>

            </svg>

            <span v-if="editingChatName" class="rename-inline">

              <input v-model="editingName" class="rename-input" @keydown.enter="saveRename(currentTaskId)" @keydown.escape="cancelRename" autofocus />

              <button class="app-btn icon-sm primary" @click="saveRename(currentTaskId)">保存</button>

            </span>

            <span v-else @dblclick="startRename(currentTaskObj)" style="cursor:pointer">{{ currentTaskName }}</span>

          </div>

          <button class="close-chat" @click="closeChat">&times;</button>

        </div>



        <div class="chat-messages" ref="chatMessagesRef">

          <div

            v-for="(msg, idx) in chatMessages"

            :key="idx"

            class="chat-message"

            :class="msg.role"

            v-show="msg.role !== 'assistant' || msg.content || agentLoading"

          >

            <div class="message-avatar" v-if="msg.role === 'assistant'">

              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20">

                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>

                <path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>

              </svg>

            </div>

            <div class="message-content" v-html="formatMessage(msg.content)"></div>

            <div v-if="msg.role === 'assistant' && !msg.content && agentLoading" class="message-content typing">

              <span></span><span></span><span></span>

            </div>

          </div>



        </div>



        <!-- Config summary when complete -->

        <div v-if="isConfigComplete" class="config-confirm-section">

          <div class="config-preview-summary">
            <span class="detail-config-count">已配置 {{ configFieldCount(currentConfig) }} 项</span>
            <button class="app-btn outline small" @click="openConfigPreview(currentConfig, currentTaskObj.name)">完整配置</button>
          </div>

          <div class="confirm-actions">

            <button class="app-btn primary large" @click="confirmAndStart" :disabled="confirming">

              {{ confirming ? '启动中..' : '确认并开始执行' }}

            </button>

            <button
              v-if="currentTaskObj.status === 'completed' || currentTaskObj.status === 'failed'"
              class="app-btn icon"
              @click="handleSaveToDb(currentTaskObj)"
              :disabled="savingToDb === currentTaskObj.id"
              title="保存到数据库"
              aria-label="保存到数据库"
            >
              <svg v-if="savingToDb !== currentTaskObj.id" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/>
                <polyline points="7 3 7 8 15 8"/>
              </svg>
              <span v-else class="spinner" style="width:14px;height:14px;border-width:1.5px"></span>
            </button>


            <button class="app-btn outline large" @click="continueEditing">

              我还没确定好

            </button>

          </div>


          </div>



        <!-- Input area -->

        <div class="chat-input-area" v-if="!isConfigComplete">

          <input

            v-model="userInput"

            type="text"

            placeholder="输入您的回复..."

            @keydown.enter="sendMessage"

            :disabled="agentLoading"

          />

          <button class="send-btn" @click="sendMessage" :disabled="!userInput.trim() || agentLoading">

            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20">

              <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>

              <polygon points="22 2 15 22 11 13 2 9 22 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>

            </svg>

          </button>

        </div>

      </div>

  </div>

</div>

</template>



<script setup>

import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'

import {

  createTask, listTasks, cancelTask, deleteTask, resumeTask,

  chatWithAgent, confirmTask, getChatHistory,

  subscribeTaskProgress, getToken, renameTask, saveDatasetFromTask, updateTaskConfig

} from '@/utils/api'
import { refreshDatasetList } from '@/utils/datasetBus'

import { ElMessage } from 'element-plus'



const tasks = ref([])

const showChat = ref(false)

const creatingTask = ref(false)

const currentTaskId = ref(null)

const chatMessages = ref([])

const userInput = ref('')

const agentLoading = ref(false)

const isConfigComplete = ref(false)

const currentConfig = ref({})

const confirming = ref(false)

const configPreviewVisible = ref(false)
const previewConfig = ref({})
const previewJsonDraft = ref({})
const previewJsonErrors = ref({})
const applyingPreview = ref(false)
const configPreviewTitle = ref('')
const configFieldCount = (config) => Object.keys(config || {}).filter(k => config[k] !== undefined && config[k] !== null).length

const JSON_FIELDS = ['keywords', 'tags', 'classification_axes', 'search_items']
const jsonPlaceholder = (key) => {
  if (key === 'classification_axes') return '[{"axis_key":"color","axis_name":"颜色","values":[...]}, ...]'
  if (key === 'search_items') return '[{"axis_key":"color","target_count":50,"query_keywords":["..."]}, ...]'
  return '["item1", "item2", ...]'
}

const openConfigPreview = (config, label = '') => {
  const base = config || {}
  previewConfig.value = { ...base }
  previewJsonDraft.value = {}
  previewJsonErrors.value = {}
  for (const k of JSON_FIELDS) {
    if (base[k] !== undefined && base[k] !== null) {
      previewJsonDraft.value[k] = JSON.stringify(base[k], null, 2)
    }
  }
  configPreviewTitle.value = label ? `任务：${label}` : ''
  configPreviewVisible.value = true
}

const updatePreviewField = (key, value) => {
  previewConfig.value = { ...previewConfig.value, [key]: value }
}

const updatePreviewJson = (key, raw) => {
  previewJsonDraft.value = { ...previewJsonDraft.value, [key]: raw }
  const trimmed = (raw || '').trim()
  if (!trimmed) {
    previewJsonErrors.value = { ...previewJsonErrors.value, [key]: undefined }
    // Empty -> clear the field from config
    const next = { ...previewConfig.value }
    delete next[key]
    previewConfig.value = next
    return
  }
  try {
    const parsed = JSON.parse(trimmed)
    if (!Array.isArray(parsed)) {
      previewJsonErrors.value = { ...previewJsonErrors.value, [key]: '必须是 JSON 数组' }
      return
    }
    previewJsonErrors.value = { ...previewJsonErrors.value, [key]: undefined }
    previewConfig.value = { ...previewConfig.value, [key]: parsed }
  } catch (err) {
    previewJsonErrors.value = { ...previewJsonErrors.value, [key]: `JSON 错误: ${err.message}` }
  }
}

const previewIsValid = computed(() =>
  Object.values(previewJsonErrors.value).every(e => !e)
)

const copyPreviewJson = async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(previewConfig.value, null, 2))
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败：' + (err.message || err))
  }
}

const applyPreviewConfig = async () => {
  if (!currentTaskId.value || !previewIsValid.value || applyingPreview.value) return
  applyingPreview.value = true
  const newConfig = { ...previewConfig.value }
  // Drop null/undefined for cleanliness (matches the backend's _normalize_config behaviour)
  for (const k of Object.keys(newConfig)) {
    if (newConfig[k] === null || newConfig[k] === undefined) delete newConfig[k]
  }
  try {
    // 1) Persist to backend so DB state matches what the agent will see next turn.
    await updateTaskConfig(currentTaskId.value, newConfig)
    // 2) Sync local chat-side config so the bottom confirm button uses the new values.
    currentConfig.value = { ...newConfig }
    // 3) Push a user message describing the manual update so the agent can react.
    const jsonText = JSON.stringify(newConfig, null, 2)
    const userMsg = `我手动更新了配置，请以此为准：\n\`\`\`json\n${jsonText}\n\`\`\``
    chatMessages.value.push({ role: 'user', content: userMsg })
    scrollToBottom()
    configPreviewVisible.value = false
    // 4) Send through the chat stream so the agent re-validates / acknowledges.
    await sendMessageInternal(userMsg)
    // Refresh the task list so the card reflects the new config + chat length.
    await loadTasks()
  } catch (err) {
    ElMessage.error('保存失败：' + (err.message || err))
  } finally {
    applyingPreview.value = false
  }
}

const savingToDb = ref(null)  // task id being saved, or null

const chatMessagesRef = ref(null)

const activeStreams = ref({})



// Rename state

const editingTaskId = ref(null)

const editingChatName = ref(false)

const editingName = ref('')

const renameInputRef = ref(null)


// Task detail dialog

const showDetail = ref(false)

const detailTask = ref({})



const openDetail = (task) => {

  detailTask.value = task

  showDetail.value = true

}



const openChatFromDetail = () => {

  const t = detailTask.value

  showDetail.value = false

  if (t && t.id) openChat(t)

}



const handleConfirmFromDetail = async () => {

  const t = detailTask.value

  if (!t || !t.id) return

  confirming.value = true

  try {

    await confirmTask(t.id)

    ElMessage.success('任务已启动')

    await loadTasks()

    const refreshed = tasks.value.find(x => x.id === t.id)

    if (refreshed) detailTask.value = refreshed

  } catch (err) {

    ElMessage.error('无法启动：' + (err.message || err))

  } finally {

    confirming.value = false

  }

}



const handleCancelFromDetail = async () => {

  const t = detailTask.value

  if (!t || !t.id) return

  try {

    await cancelTask(t.id)

    ElMessage.success('已取消')

    await loadTasks()

    const refreshed = tasks.value.find(x => x.id === t.id)

    if (refreshed) detailTask.value = refreshed

  } catch (err) {

    ElMessage.error('取消失败：' + (err.message || err))

  }

}



const resuming = ref(false)

const handleResumeFromDetail = async () => {

  const t = detailTask.value

  if (!t || !t.id) return

  resuming.value = true

  try {

    await resumeTask(t.id)

    await loadTasks()

    showDetail.value = false

    const refreshed = tasks.value.find(x => x.id === t.id)

    ElMessage.success('任务已重新打开，可以修改配置')

    // Open the existing chat so the user can revise the config and re-confirm.

    await openChat(refreshed || t)

  } catch (err) {

    ElMessage.error('打开失败：' + (err.message || err))

  } finally {

    resuming.value = false

  }

}



const handleSaveFromDetail = async () => {

  const t = detailTask.value

  if (!t || !t.id) return

  savingToDb.value = t.id

  try {

    await saveDatasetFromTask(t.id)
    refreshDatasetList()

    ElMessage.success('已保存到数据库')

    await loadTasks()

    showDetail.value = false

  } catch (err) {

    ElMessage.error('保存失败：' + (err.message || err))

  } finally {

    savingToDb.value = null

  }

}



const handleDeleteFromDetail = async () => {

  const t = detailTask.value

  if (!t || !t.id) return

  showDetail.value = false

  await handleDelete(t.id)

}



const currentTaskObj = computed(() => tasks.value.find(t => t.id === currentTaskId.value) || {})

const currentTaskName = computed(() => currentTaskObj.value.name || '')



const statusText = {

  configuring: '配置中',

  pending: '等待中',

  running: '运行中',

  completed: '已完成',

  cancelled: '已取消',

  failed: '失败',

}



const fieldLabels = {

  subject: '数据主题',

  keywords: '抓取搜索词',

  classification_axes: '分类轴设计',

  search_items: '检索计划',

  max_count: '最大数量',

  name: '数据集名称',

  format: '图片格式',

  min_width: '最小宽度',

  min_height: '最小高度',

  description: '数据集描述',

  tags: '标签',

  need_mask: '是否生成 Mask',

  mask_provider: 'Mask 服务',

  search_policy: '检索策略',

}



const formatTime = (dateStr) => {

  if (!dateStr) return ''

  const d = new Date(dateStr)

  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

}



const formatMessage = (msg) => {

  if (!msg) return ''

  return msg

    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')

    .replace(/\n/g, '<br>')

    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

}



const formatConfigValue = (key, value) => {
  if (value === null || value === undefined || value === '' || value === '待用户确认' || value === 'TBD') {
    if (key === 'min_width' || key === 'min_height') return '不限'
    if (key === 'need_mask') return '不需要'
    if (key === 'mask_provider') return '不需要'
    if (key === 'description') return '待补充'
    if (key === 'tags' || key === 'classification_axes' || key === 'search_items') return '待设置'
    return '待用户确认'
  }

  if (Array.isArray(value)) {
    if (key === 'classification_axes') {
      const names = value.map(a => a.axis_name || a.axis_key || '').filter(Boolean).join('、')
      return names ? `${value.length} 个：${names}` : `${value.length} 个分类轴`
    }
    if (key === 'search_items') {
      const total = value.reduce((sum, item) => sum + (Number(item.target_count) || 0), 0)
      return total ? `${value.length} 条检索计划，共 ${total} 张` : `${value.length} 条检索计划`
    }
    if (key === 'tags') return value.join('、')
    if (value.length > 0 && typeof value[0] === 'object') return `${value.length} 项`
    return value.join('、')
  }

  if (typeof value === 'boolean') return value ? '需要' : '不需要'

  if (value && typeof value === 'object') return JSON.stringify(value)

  if ((value === 0 || value === '0') && (key === 'min_width' || key === 'min_height')) return '不限'

  return String(value)
}

const scrollToBottom = () => {

  nextTick(() => {

    if (chatMessagesRef.value) {

      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight

    }

  })

}



const loadTasks = async () => {

  try {

    tasks.value = await listTasks()

    tasks.value.forEach(task => {

      if (task.status === 'running' || task.status === 'pending') {

        subscribeToTask(task.id)

      }

    })

  } catch (error) {

    console.error('Failed to load tasks:', error)

  }

}



const subscribeToTask = (taskId) => {

  if (activeStreams.value[taskId]) return



  const unsubscribe = subscribeTaskProgress(

    taskId,

    (data) => {

      const idx = tasks.value.findIndex(t => t.id === taskId)

      if (idx !== -1) {

        tasks.value[idx] = { ...tasks.value[idx], ...data }

      }

    },

    () => {

      delete activeStreams.value[taskId]

      loadTasks()

    }

  )

  activeStreams.value[taskId] = unsubscribe

}



const startNewTask = async () => {

  if (creatingTask.value) return

  creatingTask.value = true

  try {

    const task = await createTask('xcrawler')

    tasks.value.unshift(task)

    // Open chat with empty history - user types first

    openChat(task)

    ElMessage.success('任务已创建，请开始配置参数')

  } catch (error) {

    ElMessage.error(`创建失败: ${error.message}`)

  } finally {

    setTimeout(() => { creatingTask.value = false }, 500)

  }

}



const openChat = async (task) => {

  currentTaskId.value = task.id

  showChat.value = true

  chatMessages.value = []

  isConfigComplete.value = false

  currentConfig.value = task.task_config || {}



  // Load persisted chat history from DB

  try {

    const history = await getChatHistory(task.id)

    if (history.messages?.length > 0) {

      chatMessages.value = history.messages

    }

    if (history.config && Object.keys(history.config).length > 0) {

      currentConfig.value = history.config

      // Check if config is already complete

      const agent = null // will check via backend

    }

  } catch (error) {

    // No history yet - empty chat, user types first

  }



  scrollToBottom()

}



const closeChat = () => {

  showChat.value = false

  currentTaskId.value = null

  loadTasks()

}



const sendMessage = async () => {

  if (!userInput.value.trim() || agentLoading.value) return

  const msg = userInput.value.trim()

  userInput.value = ''

  await sendMessageInternal(msg)

}



const sendMessageInternal = async (message) => {

  if (!message || agentLoading.value) return

  chatMessages.value.push({ role: 'user', content: message })

  scrollToBottom()



  agentLoading.value = true

  // Add empty assistant message that will be filled by streaming

  const assistantIdx = chatMessages.value.length

  chatMessages.value.push({ role: 'assistant', content: '' })

  scrollToBottom()



  try {

    const token = getToken()

    const response = await fetch(

      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/tasks/${currentTaskId.value}/chat/stream`,

      {

        method: 'POST',

        headers: {

          'Content-Type': 'application/json',

          Authorization: `Bearer ${token}`,

        },

        body: JSON.stringify({ task_id: currentTaskId.value, message }),

      }

    )



    if (!response.ok) {

      throw new Error('Stream request failed')

    }



    const reader = response.body.getReader()

    const decoder = new TextDecoder()

    let buffer = ''

    let fullContent = ''

    let isComplete = false

    let configSummary = null



    try {

    while (true) {

      const { done, value } = await reader.read()

      if (done) break



      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')

      buffer = lines.pop() || ''



      for (const line of lines) {

        if (line.startsWith('data: ')) {

          try {

            const data = JSON.parse(line.slice(6))

            if (data.type === 'chunk') {

              fullContent += data.content

              chatMessages.value[assistantIdx].content = fullContent

              scrollToBottom()

            } else if (data.type === 'complete') {

              isComplete = data.is_complete

              configSummary = data.config_summary

            } else if (data.type === 'error') {

              // Surface error as soft warning instead of throwing — keep any partial content already streamed.

              const errText = (data.message || '未知错误')

              if (fullContent) {

                chatMessages.value[assistantIdx].content = (fullContent + '\n\n> ⚠️ ' + errText).trim()

              } else {

                chatMessages.value[assistantIdx].content = '> ⚠️ ' + errText

              }

            } else if (data.type === 'complete' && data.warning) {

              // Server-side partial-recovery notice: append as soft warning, do not abort.

              if (fullContent) {

                chatMessages.value[assistantIdx].content = (fullContent + '\n\n> ⚠️ ' + data.warning).trim()

              }

            }

          } catch (e) {

            // JSON.parse failure on partial chunk — keep buffer, just skip this line.

            if (!e.message?.includes('Stream request failed')) {

              // Only log; do not propagate. Buffer logic above preserves partial content.

            }

          }

        }

      }

    }
    } catch (streamErr) {
      // reader.read() threw (network blip / SSE closed early). Preserve whatever content we already streamed.
      console.warn('Stream interrupted:', streamErr?.message || streamErr)
      if (fullContent && chatMessages.value[assistantIdx]) {
        const suffix = chatMessages.value[assistantIdx].content.includes('> ⚠️') ? '' : '\n\n> ⚠️ 连接中断，请重发消息'
        chatMessages.value[assistantIdx].content = (fullContent + suffix).trim()
      }
    }



    // Remove empty assistant message if nothing was received

    if (!fullContent && chatMessages.value[assistantIdx]?.content === '') {

      chatMessages.value.splice(assistantIdx, 1)

    }



    if (configSummary) {

      currentConfig.value = configSummary

    }



    if (isComplete) {

      isConfigComplete.value = true

      ElMessage.success('配置已完成，请确认')

    }

  } catch (error) {

    ElMessage.error(`Agent 错误: ${error.message}`)

    if (chatMessages.value[assistantIdx]) {

      chatMessages.value[assistantIdx].content = '抱歉，出现了错误，请重试或重新创建任务'

    }

  } finally {

    agentLoading.value = false

  }

}



const confirmAndStart = async () => {

  confirming.value = true

  try {

    await confirmTask(currentTaskId.value)

    ElMessage.success('任务已启动！')

    closeChat()

  } catch (error) {

    ElMessage.error(`启动失败: ${error.message}`)

  } finally {

    confirming.value = false

  }

}



const handleSaveToDb = async (task) => {
  if (savingToDb.value) return
  savingToDb.value = task.id
  try {
    const result = await saveDatasetFromTask(task.id)
    refreshDatasetList()
    ElMessage.success('数据集已保存到数据库')
  } catch (error) {
    if (error.message?.includes('already saved')) {
      ElMessage.info('该任务已保存过')
    } else {
      ElMessage.error('保存失败: ' + (error.message || '未知错误'))
    }
  } finally {
    savingToDb.value = null
  }
}

const handleCancel = async (taskId) => {

  try {

    await cancelTask(taskId)

    ElMessage.success('取消信号已发送')

  } catch (error) {

    ElMessage.error(`取消失败: ${error.message}`)

  }

}



const handleDelete = async (taskId) => {

  try {

    await deleteTask(taskId)

    tasks.value = tasks.value.filter(t => t.id !== taskId)

    ElMessage.success('任务记录已删除')

  } catch (error) {

    ElMessage.error(`删除失败: ${error.message}`)

  }

}



// --- Rename logic ---

const startRename = (task) => {

  if (!task || !task.id) return

  editingName.value = task.name

  if (showChat.value && currentTaskId.value === task.id) {

    editingChatName.value = true

    editingTaskId.value = null

  } else {

    editingTaskId.value = task.id

    editingChatName.value = false

  }

}



const cancelRename = () => {

  editingTaskId.value = null

  editingChatName.value = false

  editingName.value = ''

}



const saveRename = async (taskId) => {

  const name = editingName.value.trim()

  if (!name || !taskId) return cancelRename()



  try {

    await renameTask(taskId, name)

    const idx = tasks.value.findIndex(t => t.id === taskId)

    if (idx !== -1) {

      tasks.value[idx].name = name

    }

    ElMessage.success('任务名称已更新')

  } catch (error) {

    ElMessage.error(`重命名失败${error.message}`)

  }

  cancelRename()

}



const continueEditing = () => {

  isConfigComplete.value = false

  chatMessages.value.push({

    role: 'user',

    content: '我想再补充一些其他字段信息'

  })

  chatMessages.value.push({

    role: 'assistant',

    content: '好的，当前必要字段已经收集完毕✅\n\n你还可以补充以下可选字段：\n- 🏷 标签（tags? 方便后续分类检索\n- 📐 最小宽度，最小高度 过滤低分辨率图片\n\n请告诉我你想补充哪些，或者直接说出你的需求～'

  })

  scrollToBottom()

}



onMounted(() => {

  loadTasks()

})



onUnmounted(() => {

  Object.values(activeStreams.value).forEach(unsub => unsub?.())

})

</script>



<style scoped>

.tasks-page {

  max-width: 1000px;

  margin: 0 auto;

}



.tasks-header {

  display: flex;

  align-items: center;

  justify-content: space-between;

  margin-bottom: 24px;

}



.tasks-header h2 {

  font-size: 22px;

  font-weight: 700;

  color: var(--text-primary);

  margin: 0;

}



.create-btn {

  display: flex;

  align-items: center;

  gap: 8px;

  padding: 12px 20px;

  background: var(--accent-primary);

  color: #fff;

  border: none;

  border-radius: 10px;

  font-size: 14px;

  font-weight: 600;

  cursor: pointer;

  transition: all 0.2s;

}



.create-btn:hover {

  opacity: 0.9;

  transform: translateY(-1px);

}



.tasks-list {

  display: flex;

  flex-direction: column;

  gap: 16px;

}



.task-card {

  position: relative;

  background: var(--bg-secondary);

  border: 1px solid var(--border-color);

  border-radius: 14px;

  padding: 16px 18px 0;

  overflow: hidden;

  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;

}

.task-card.running {
  animation: card-breathe 2s ease-in-out infinite;
  border-color: rgba(52, 211, 153, 0.4);
}

@keyframes card-breathe {
  0%, 100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0), 0 4px 12px rgba(0,0,0,0.06); }
  50% { box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.2), 0 8px 24px rgba(52, 211, 153, 0.15); }
}

.task-card:hover {

  transform: translateY(-2px);

  box-shadow: 0 12px 32px rgba(58, 125, 126, 0.12), 0 4px 10px rgba(0, 0, 0, 0.04);

  border-color: rgba(58, 125, 126, 0.25);

}



/* Faint backdrop fill that grows with progress, sits behind card content */

.task-card-fill {

  position: absolute;

  top: 0;

  left: 0;

  bottom: 0;

  background: linear-gradient(90deg, rgba(58, 125, 126, 0.08), rgba(58, 125, 126, 0.03));

  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);

  pointer-events: none;

  z-index: 0;

}

.task-card-fill.completed { background: linear-gradient(90deg, rgba(56, 189, 248, 0.10), rgba(56, 189, 248, 0.04)); }

.task-card-fill.failed    { background: linear-gradient(90deg, rgba(239, 68, 68, 0.08),  rgba(239, 68, 68, 0.03)); }

.task-card-fill.cancelled { background: rgba(148, 163, 184, 0.06); }

.task-card-fill.pending   { background: linear-gradient(90deg, rgba(245, 158, 11, 0.08), rgba(245, 158, 11, 0.03)); }

.task-card-fill.running {
  background-image:
    linear-gradient(to bottom,
      rgba(52, 211, 153, 0.0) 0%,
      rgba(52, 211, 153, 0.08) 40%,
      rgba(52, 211, 153, 0.45) 100%
    ),
    linear-gradient(90deg, transparent 0%, rgba(52, 211, 153, 0.35) 50%, transparent 100%);
  background-size: 100% 100%, 200% 100%;
  animation: charge-bar 2.5s linear infinite;
}

@keyframes charge-bar {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}



/* Lift every direct child (other than the fill) above it */

.task-card > *:not(.task-card-fill) { position: relative; z-index: 1; }



.task-info {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

  margin-bottom: 10px;

}



.task-name {

  font-size: 15px;

  font-weight: 600;

  color: var(--text-primary);

  display: flex;

  align-items: center;

  gap: 8px;

  flex: 1;

  min-width: 0;

}



.task-name-text {

  flex: 1;

  min-width: 0;

  cursor: default;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}

.task-name-text:hover {

  text-decoration: underline;

  text-decoration-style: dotted;

}



/* Frosted-glass tag pills */

.status-badge {

  display: inline-flex;

  align-items: center;

  gap: 6px;

  padding: 4px 12px;

  border-radius: 999px;

  font-size: 12px;

  font-weight: 500;

  letter-spacing: 0.2px;

  background: rgba(255, 255, 255, 0.55);

  backdrop-filter: blur(14px) saturate(160%);

  -webkit-backdrop-filter: blur(14px) saturate(160%);

  border: 1px solid rgba(255, 255, 255, 0.55);

  box-shadow:

    0 2px 6px rgba(58, 125, 126, 0.06),

    inset 0 1px 0 rgba(255, 255, 255, 0.7);

  color: var(--text-primary);

  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;

}

.status-badge:hover {

  transform: translateY(-1px);

  background: rgba(255, 255, 255, 0.72);

  box-shadow:

    0 6px 14px rgba(58, 125, 126, 0.14),

    inset 0 1px 0 rgba(255, 255, 255, 0.85);

}

.status-badge::before {

  content: '';

  width: 6px;

  height: 6px;

  border-radius: 50%;

  background: var(--accent-primary);

  box-shadow: 0 0 0 2px rgba(58, 125, 126, 0.16);

}

.status-badge.configuring::before { background: #0ea5e9; box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.18); }

.status-badge.pending::before     { background: #f59e0b; box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.18); }

.status-badge.running::before {
  background: #34d399;
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.18);
  animation: breathe 1.8s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.3); }
  50% { opacity: 0.6; transform: scale(1.4); box-shadow: 0 0 6px 3px rgba(52, 211, 153, 0.4); }
}

.status-badge.completed::before   { background: #38bdf8; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.22); }

.status-badge.cancelled::before   { background: #94a3b8; box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.16); }

.status-badge.failed::before      { background: #ef4444; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.18); }



.task-time {

  font-size: 11.5px;

  color: var(--text-tertiary);

 flex-shrink: 0; }



.task-name-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
}

/* Local button styles were removed; all buttons now use the global
   .app-btn utilities defined in App.vue. See <style> in App.vue. */

/* Compact delete icon - inline with status badge, no extra row */

.task-card-delete {

  width: 30px;

  height: 30px;

  margin-left: 4px;

  padding: 0;

  border: none;

  border-radius: 8px;

  background: transparent;

  color: var(--text-tertiary);

  cursor: pointer;

  display: inline-flex;

  align-items: center;

  justify-content: center;

  flex-shrink: 0;

  opacity: 0.72;

  transition: opacity 0.2s ease, color 0.2s ease, transform 0.2s ease;

}

.task-card:hover .task-card-delete { opacity: 1; }

.task-card-delete:hover {

  color: #dc2626;

  transform: scale(1.1);

}



.task-config-summary {

  background: rgba(58, 125, 126, 0.04);

  border: 1px solid rgba(58, 125, 126, 0.08);

  border-radius: 10px;

  padding: 8px 14px;

  margin-bottom: 10px;

  display: flex;

  flex-wrap: wrap;

  gap: 6px 14px;

  max-height: 56px;

  overflow: hidden;

  align-content: flex-start;

  position: relative;

}

.config-item {

  font-size: 12.5px;

  display: flex;

  align-items: baseline;

  gap: 4px;

  max-width: 100%;

  min-width: 0;

}

.config-label { color: var(--text-tertiary); flex-shrink: 0; }

.config-value {

  color: var(--text-primary);

  font-weight: 500;

  flex: 1;

  min-width: 0;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}



/* Bottom progress strip, integrated into the card */

.task-progress-strip {

  position: relative;

  margin: 0 -18px;

  padding: 5px 18px;

  min-height: 26px;

  background: rgba(58, 125, 126, 0.05);

  border-top: 1px solid rgba(58, 125, 126, 0.08);

  display: flex;

  align-items: center;

  overflow: hidden;

  isolation: isolate;

}

/* The fill IS the strip's own background - no separate thin line */

.task-progress-fill {

  position: absolute;

  left: 0;

  top: 0;

  bottom: 0;

  width: 0;

  background: linear-gradient(90deg, rgba(58, 125, 126, 0.22), rgba(58, 125, 126, 0.10));

  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);

  z-index: 0;

}

.task-progress-fill.completed { background: linear-gradient(90deg, rgba(16, 185, 129, 0.24), rgba(16, 185, 129, 0.10)); }

.task-progress-fill.failed    { background: linear-gradient(90deg, rgba(239, 68, 68, 0.20),  rgba(239, 68, 68, 0.08)); }

.task-progress-fill.cancelled { background: rgba(148, 163, 184, 0.10); }

.task-progress-fill.pending   { background: linear-gradient(90deg, rgba(245, 158, 11, 0.22), rgba(245, 158, 11, 0.10)); }

.task-progress-pct {

  margin-left: auto;

  font-size: 11.5px;

  font-weight: 600;

  color: var(--text-primary);

  z-index: 1;

  padding-left: 12px;

  letter-spacing: 0.3px;

}







.task-message {

  font-size: 12.5px;

  color: var(--text-secondary);

  margin-bottom: 8px;

  display: -webkit-box;

  -webkit-line-clamp: 2;

  line-clamp: 2;

  -webkit-box-orient: vertical;

  overflow: hidden;

  word-break: break-word;

}



.task-actions {

  display: flex;

  justify-content: flex-end;

  gap: 8px;

}



.config-btn {

  padding: 6px 14px;

  background: var(--accent-primary);

  color: #fff;

  border: none;

  border-radius: 7px;

  font-size: 12.5px;

  font-weight: 500;

  cursor: pointer;

  transition: all 0.2s;

}



.config-btn:hover { opacity: 0.9; }






.empty-state {

  text-align: center;

  padding: 80px 20px;

  color: var(--text-tertiary);

}



.empty-state svg {

  margin-bottom: 20px;

  opacity: 0.4;

}



.empty-state h3 {

  font-size: 18px;

  font-weight: 600;

  color: var(--text-primary);

  margin: 0 0 8px 0;

}



.empty-state p {

  font-size: 14px;

  color: var(--text-secondary);

  max-width: 360px;

  margin: 0 auto;

  line-height: 1.5;

}



/* Rename inline controls */

.rename-inline {

  display: inline-flex;

  align-items: center;

  gap: 6px;

}



.rename-input {

  padding: 4px 8px;

  border: 1px solid var(--accent-primary);

  border-radius: 6px;

  font-size: 14px;

  font-weight: 600;

  background: var(--bg-primary);

  color: var(--text-primary);

  outline: none;

  width: 200px;

}






/* Spinner */

.spinner {

  display: inline-block;

  width: 16px;

  height: 16px;

  border: 2px solid rgba(255, 255, 255, 0.3);

  border-top-color: #fff;

  border-radius: 50%;

  animation: spin 0.6s linear infinite;

}



@keyframes spin {

  to { transform: rotate(360deg); }

}



/* Chat Dialog */

.chat-overlay {

  position: fixed;

  inset: 0;

  background: rgba(0, 0, 0, 0.5);

  backdrop-filter: blur(4px);

  display: flex;

  align-items: center;

  justify-content: center;

  z-index: 1000;

}



.chat-container {

  background: var(--bg-secondary);

  border-radius: 16px;

  width: 100%;

  max-width: 780px;

  max-height: 85vh;

  display: flex;

  flex-direction: column;

  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);

}



.chat-header {

  display: flex;

  align-items: center;

  justify-content: space-between;

  padding: 20px 24px;

  border-bottom: 1px solid var(--border-color);

}



.chat-title {

  display: flex;

  align-items: center;

  gap: 10px;

  font-size: 18px;

  font-weight: 600;

  color: var(--text-primary);

}



.chat-title svg {

  color: var(--accent-primary);

}



.close-chat {

  background: none;

  border: none;

  font-size: 28px;

  color: var(--text-tertiary);

  cursor: pointer;

  padding: 4px;

  line-height: 1;

}



.close-chat:hover {

  color: var(--text-primary);

}



.chat-messages {

  flex: 1;

  overflow-y: auto;

  padding: 20px;

  min-height: 400px;

  max-height: 520px;

}



.chat-message {

  display: flex;

  gap: 12px;

  margin-bottom: 16px;

}



.chat-message.user {

  flex-direction: row-reverse;

}



.message-avatar {

  width: 36px;

  height: 36px;

  border-radius: 50%;

  background: var(--accent-light);

  color: var(--accent-primary);

  display: flex;

  align-items: center;

  justify-content: center;

  flex-shrink: 0;

}



.message-content {

  max-width: 80%;

  padding: 12px 16px;

  border-radius: 14px;

  font-size: 14px;

  line-height: 1.5;

}



.chat-message.assistant .message-content {

  background: var(--bg-tertiary);

  color: var(--text-primary);

  border-bottom-left-radius: 4px;

}



.chat-message.user .message-content {

  background: var(--accent-primary);

  color: #fff;

  border-bottom-right-radius: 4px;

}



.message-content pre {

  background: var(--bg-primary);

  border-radius: 8px;

  padding: 12px;

  margin: 8px 0;

  overflow-x: auto;

}



.message-content code {

  font-family: 'Monaco', 'Consolas', monospace;

  font-size: 13px;

}



.typing {

  display: flex;

  align-items: center;

  gap: 4px;

  padding: 16px;

}



.typing span {

  width: 8px;

  height: 8px;

  background: var(--text-tertiary);

  border-radius: 50%;

  animation: typing 1.4s infinite;

}



.typing span:nth-child(2) { animation-delay: 0.2s; }

.typing span:nth-child(3) { animation-delay: 0.4s; }



@keyframes typing {

  0%, 100% { transform: translateY(0); }

  50% { transform: translateY(-8px); }

}



.config-confirm-section {

  padding: 20px;

  border-top: 1px solid var(--border-color);

}

/* Config preview modal */
.config-preview-dialog .el-dialog__body { padding: 14px 22px 18px; }
.config-preview-subtitle {
  font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px;
  padding-bottom: 10px; border-bottom: 1px dashed var(--border-color);
}
.config-preview-grid {
  display: grid; grid-template-columns: 1fr; gap: 0;
  max-height: 60vh; overflow-y: auto;
}
.config-preview-row {
  display: flex; gap: 14px; padding: 9px 0;
  border-bottom: 1px dashed var(--border-color);
  font-size: 13px; align-items: flex-start;
}
.config-preview-row:last-child { border-bottom: none; }
.config-preview-label {
  color: var(--text-tertiary); min-width: 110px; flex-shrink: 0;
  font-weight: 500;
}
.config-preview-value {
  color: var(--text-primary); flex: 1; word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px;
}
.config-preview-input-wrap { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.config-preview-input {
  width: 100%; padding: 6px 10px; border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary); color: var(--text-primary);
  font-size: 12.5px; font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.config-preview-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(58, 125, 126, 0.18);
}
.config-preview-textarea {
  width: 100%; padding: 8px 10px; border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary); color: var(--text-primary);
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  line-height: 1.5; resize: vertical;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.config-preview-textarea:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(58, 125, 126, 0.18);
}
.config-preview-textarea.invalid {
  border-color: var(--danger);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15);
}
.config-preview-error { font-size: 11.5px; color: var(--danger); }
.config-preview-toggle {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 6px; cursor: pointer;
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  font-size: 12.5px; color: var(--text-primary); width: fit-content;
}
.config-preview-toggle input { cursor: pointer; accent-color: var(--accent-primary); }
.config-preview-footer { display: flex; justify-content: flex-end; gap: 8px; }



.config-preview-summary {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 14px; margin-bottom: 12px;
  background: var(--bg-tertiary); border: 1px solid var(--border-color);
  border-radius: 10px;
}

.detail-config-count { font-size: 13px; color: var(--text-secondary); font-weight: 500; }



.confirm-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.confirm-actions .app-btn.primary { flex: 1; }






.chat-input-area {

  display: flex;

  gap: 12px;

  padding: 16px 20px;

  border-top: 1px solid var(--border-color);

}



.chat-input-area input {

  flex: 1;

  padding: 12px 16px;

  border: 1px solid var(--border-color);

  border-radius: 10px;

  font-size: 14px;

  background: var(--bg-primary);

  color: var(--text-primary);

  transition: all 0.2s;

}



.chat-input-area input:focus {

  outline: none;

  border-color: var(--accent-primary);

  box-shadow: 0 0 0 3px rgba(58, 125, 126, 0.1);

}



.chat-input-area input::placeholder {

  color: var(--text-tertiary);

}



.send-btn {

  width: 48px;

  height: 48px;

  background: var(--accent-primary);

  color: #fff;

  border: none;

  border-radius: 10px;

  display: flex;

  align-items: center;

  justify-content: center;

  cursor: pointer;

  transition: all 0.2s;

}



.send-btn:hover { opacity: 0.9; }

.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

</style>










/* Task detail dialog */
.task-detail-dialog { border-radius: 12px; }
.task-detail-dialog .el-dialog__header { padding: 16px 20px; border-bottom: 1px solid rgba(0, 0, 0, 0.06); margin-right: 0; }
.task-detail-dialog .el-dialog__body { padding: 18px 20px; }
.task-detail-dialog .el-dialog__footer { padding: 14px 20px; border-top: 1px solid var(--border-color); }
.detail-header { display: flex; align-items: center; gap: 10px; }
.detail-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.detail-time { font-size: 12px; color: var(--text-tertiary); margin-left: auto; }
.detail-message { font-size: 13px; color: var(--text-secondary); padding: 10px 12px; background: rgba(58, 125, 126, 0.06); border-radius: 8px; margin-bottom: 12px; }
.detail-progress { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.detail-progress-track { flex: 1; height: 6px; background: var(--bg-tertiary); border-radius: 999px; overflow: hidden; }
.detail-progress-fill { height: 100%; background: linear-gradient(90deg, #3a7d7e, #4ea0a1); transition: width 0.3s ease; border-radius: 999px; }
.detail-progress-fill.completed { background: linear-gradient(90deg, #10b981, #34d399); }
.detail-progress-fill.failed { background: linear-gradient(90deg, #ef4444, #f87171); }
.detail-progress-fill.cancelled { background: var(--border-hover); }
.detail-progress-fill.pending { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.detail-progress-pct { font-size: 12px; color: var(--text-secondary); min-width: 36px; text-align: right; }
.detail-config-summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 14px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 10px; margin-bottom: 8px; }
.detail-empty { font-size: 13px; color: var(--text-tertiary); padding: 24px 0; text-align: center; }
.detail-actions { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }

/* Compact summary chips on the task card */
.task-summary-line { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; cursor: pointer; padding: 4px 0; user-select: none; }
.task-summary-line:hover .summary-detail-link { color: #3d8fa3 !important; }
.summary-chip { font-size: 11.5px; color: var(--text-secondary); background: rgba(58, 125, 126, 0.08); padding: 2px 9px; border-radius: 999px; }
.summary-detail-link { margin-left: auto; display: flex; align-items: center; gap: 8px; font-size: 12px; color: #4a9db0 !important; padding-right: 4px; }
.summary-detail-link .detail-link-text { letter-spacing: 1px; }
.summary-detail-link .detail-link-arrow { font-size: 14px; line-height: 1; color: #4a9db0; }

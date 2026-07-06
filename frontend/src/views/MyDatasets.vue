<template>
  <div class="my-datasets-page">
    <div class="page-header">
      <div>
        <h2>我的数据集</h2>
        <p class="page-desc">管理您从 XCrawler 抓取并保存的数据集</p>
      </div>
      <button class="app-btn" style="opacity:0.5; cursor:not-allowed;" disabled title="多格式数据集上传功能正在开发中，敬请期待">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <polyline points="17 8 12 3 7 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        上传数据集
        <span style="font-size:11px; opacity:0.7; margin-left:4px">开发中</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Dataset cards grid -->
    <div v-else-if="myDatasets.length > 0" class="datasets-grid">
      <div
        v-for="ds in myDatasets"
        :key="ds.id"
        class="dataset-card"
        :class="{ published: ds.is_published }"
      >
        <div class="card-banner">
          <div class="banner-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="28" height="28">
              <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="banner-right">
            <span v-if="ds.is_published" class="badge published-badge">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="9 12 11 14 15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              已发布
            </span>
            <span class="badge count-badge">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                <polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ formatNumber(ds.image_count) }} 张
            </span>
            <button
              v-if="ds.is_published"
              class="pin-btn"
              :class="{ pinned: ds.is_pinned }"
              @click.stop="togglePin(ds)"
              :title="ds.is_pinned ? '取消置顶' : '置顶'"
            >
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="14" height="14">
                <path d="M16 12V4H17V2H7V4H8V12L6 14V16H11.2V22H12.8V16H18V14L16 12Z" :fill="ds.is_pinned ? 'currentColor' : 'none'" :stroke="ds.is_pinned ? 'currentColor' : 'currentColor'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="card-body">
          <h3 class="card-title" :title="ds.name">{{ ds.name }}</h3>
          <p class="card-desc">{{ ds.description || '暂无描述' }}</p>

          <div class="card-stats">
            <div class="stat-item">
              <span class="stat-label">大小</span>
              <span class="stat-value">{{ formatSize(ds.total_size) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">来源</span>
              <span class="stat-value">{{ ds.source || '未知' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">格式</span>
              <span class="stat-value">{{ ds.format || 'jpg' }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">创建</span>
              <span class="stat-value">{{ formatDate(ds.created_at) }}</span>
            </div>
          </div>

          <div v-if="getTags(ds).length > 0" class="card-tags">
            <span v-for="tag in getTags(ds)" :key="tag" class="card-tag">{{ tag }}</span>
          </div>

          <div v-if="ds.is_published && ds.published_at" class="published-info">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            发布于 {{ formatDate(ds.published_at) }}
          </div>
        </div>

        <div class="card-actions">
          <button
            v-if="ds.is_published"
            class="app-btn ghost small"
            @click="handleUnpublish(ds)"
            :disabled="actionLoading === ds.id"
          >
            取消发布
          </button>
          <button
            v-else
            class="app-btn outline small"
            @click="handlePublish(ds)"
            :disabled="actionLoading === ds.id"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="13" height="13">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="16 6 12 2 8 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="2" x2="12" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            发布
          </button>
          <button
            class="app-btn ghost small"
            @click="openEditDialog(ds)"
          >
            编辑信息
          </button>
          <button
            class="app-btn ghost small"
            @click="$router.push(`/app/dataset/${ds.id}`)"
          >
            详情
          </button>
          <button
            class="app-btn danger small"
            @click="openDeleteDialog(ds)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="56" height="56">
          <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="1.2"/>
          <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="1.2"/>
          <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="1.2"/>
        </svg>
      </div>
      <h3>暂无数据集</h3>
      <p>您还没有从 XCrawler 任务保存的数据集。<br>完成抓取任务后，点击「保存数据集」来创建。</p>
      <button class="app-btn primary" @click="$router.push('/tasks')">
        去抓取数据
      </button>
    </div>

    <!-- Edit info dialog -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑数据集信息"
      width="520"
      align-center
      destroy-on-close
    >
      <div v-if="currentDataset" class="edit-form">
        <div class="form-group">
          <label>数据集名称</label>
          <input
            v-model="editForm.name"
            type="text"
            class="edit-input"
            placeholder="输入数据集名称"
            @keydown.enter="confirmEdit"
          />
          <span v-if="nameError" class="field-error">{{ nameError }}</span>
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea
            v-model="editForm.description"
            class="edit-input"
            placeholder="描述数据集的内容、用途和格式..."
            rows="4"
          ></textarea>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="app-btn ghost" @click="editDialogVisible = false" :disabled="saving">取消</button>
          <button class="app-btn primary" @click="confirmEdit" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- Delete confirmation dialog -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除数据集"
      width="520"
      align-center
      destroy-on-close
    >
      <div v-if="currentDataset" class="delete-body">
        <div class="delete-warning">
          <div class="delete-warning-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="22" height="22">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="delete-warning-text">
            <p class="delete-warning-title">此操作不可恢复</p>
            <p class="delete-warning-detail">
              将删除数据库中的数据集记录及其所有样本元数据，并清除服务器上的图片与 Mask 文件夹。
            </p>
          </div>
        </div>
        <div class="delete-summary">
          <div class="delete-summary-row">
            <span class="delete-summary-label">数据集名称</span>
            <span class="delete-summary-value name">{{ currentDataset.name }}</span>
          </div>
          <div class="delete-summary-row">
            <span class="delete-summary-label">样本数</span>
            <span class="delete-summary-value">{{ currentDataset.image_count }} 张</span>
          </div>
          <div class="delete-summary-row">
            <span class="delete-summary-label">占用空间</span>
            <span class="delete-summary-value">{{ formatSize(currentDataset.total_size) }}</span>
          </div>
        </div>
        <div class="delete-confirm-input">
          <label>
            请输入数据集名称 <code>{{ currentDataset.name }}</code> 以确认删除
          </label>
          <input
            v-model="deleteConfirmName"
            class="delete-input"
            :placeholder="currentDataset.name"
            autocomplete="off"
            @keydown.enter="confirmDelete"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="app-btn ghost" @click="deleteDialogVisible = false" :disabled="deleting">取消</button>
          <button class="app-btn danger solid" @click="confirmDelete" :disabled="!canConfirmDelete || deleting">
            {{ deleting ? '删除中...' : '永久删除' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- Upload modal -->
    <div v-if="showUpload" class="modal-overlay" @click.self="showUpload = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>上传新数据集</h3>
          <button class="modal-close" @click="showUpload = false">&times;</button>
        </div>
        <form @submit.prevent="handleUpload" class="upload-form">
          <div class="form-group">
            <label>数据集名称</label>
            <input v-model="uploadForm.name" type="text" placeholder="例如：my-dataset-v1" required />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="uploadForm.description" placeholder="描述数据集的内容、用途和格式..." rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>标签</label>
            <div class="tag-selector">
              <div class="selected-tags" v-if="uploadForm.tags.length > 0">
                <span v-for="tag in uploadForm.tags" :key="tag" class="selected-tag">
                  {{ tag }}
                  <button type="button" class="tag-remove" @click="removeTag(tag)">&times;</button>
                </span>
              </div>
              <div class="tag-dropdown" ref="tagDropdownRef">
                <div class="dropdown-trigger" @click="showTagDropdown = !showTagDropdown">
                  <span class="placeholder">选择标签...</span>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="chevron" :class="{ open: showTagDropdown }">
                    <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div v-if="showTagDropdown" class="dropdown-menu">
                  <div
                    v-for="tag in predefinedTags"
                    :key="tag"
                    class="dropdown-item"
                    :class="{ selected: uploadForm.tags.includes(tag) }"
                    @click="toggleTag(tag)"
                  >
                    <span class="checkbox" :class="{ checked: uploadForm.tags.includes(tag) }">
                      <svg v-if="uploadForm.tags.includes(tag)" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                        <polyline points="20 6 9 17 4 12" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </span>
                    {{ tag }}
                  </div>
                  <div class="dropdown-divider"></div>
                  <div class="custom-tag-row">
                    <input
                      v-model="customTag"
                      type="text"
                      placeholder="自定义标签..."
                      @keydown.enter.prevent="addCustomTag"
                      class="custom-tag-input"
                    />
                    <button type="button" class="add-custom-btn" @click="addCustomTag" :disabled="!customTag.trim()">添加</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>数据文件</label>
            <div class="file-drop-zone">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="32" height="32">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="17 8 12 3 7 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <p>拖拽文件到此处，或 <span class="browse-link">浏览文件</span></p>
              <p class="hint">支持 .csv, .json, .parquet, .zip 等格式</p>
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="app-btn ghost" @click="showUpload = false">取消</button>
            <button type="submit" class="app-btn primary" :disabled="uploading">
              {{ uploading ? '上传中...' : '确认上传' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listDatasets, deleteDataset, publishDataset, unpublishDataset, updateDataset, pinDataset, unpinDataset } from '@/utils/api'

const showUpload = ref(false)
const uploading = ref(false)
const loading = ref(false)
const actionLoading = ref(null)
const showTagDropdown = ref(false)
const customTag = ref('')
const tagDropdownRef = ref(null)
const predefinedTags = ['NLP', 'CV', 'Audio', 'Tabular', 'Multimodal', 'Medical', 'Biology', 'Chemistry']
const uploadForm = reactive({ name: '', description: '', tags: [] })

const myDatasets = ref([])

// Edit dialog
const editDialogVisible = ref(false)
const currentDataset = ref(null)
const editForm = reactive({ name: '', description: '' })
const saving = ref(false)
const nameError = ref('')

// Delete dialog
const deleteDialogVisible = ref(false)
const deleteConfirmName = ref('')
const deleting = ref(false)

const canConfirmDelete = computed(() => {
  return currentDataset.value && deleteConfirmName.value.trim() === currentDataset.value.name.trim()
})

const getTags = (ds) => {
  const fields = ds.fields || {}
  return fields.tags || []
}

const formatNumber = (n) => {
  if (!n && n !== 0) return '0'
  if (n >= 10000) return (n / 1000).toFixed(1) + 'k'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toString()
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + ' GB'
  if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + ' MB'
  if (bytes >= 1e3) return (bytes / 1e3).toFixed(1) + ' KB'
  return bytes + ' B'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

const fetchDatasets = async () => {
  loading.value = true
  try {
    myDatasets.value = await listDatasets()
  } catch (err) {
    ElMessage.error('加载数据集失败：' + (err.message || err))
  } finally {
    loading.value = false
  }
}

const togglePin = async (ds) => {
  try {
    if (ds.is_pinned) {
      await unpinDataset(ds.id)
      ElMessage.success(`「${ds.name}」已取消置顶`)
    } else {
      await pinDataset(ds.id)
      ElMessage.success(`「${ds.name}」已置顶`)
    }
    // 局部更新，不重新请求列表
    const idx = myDatasets.value.findIndex(d => d.id === ds.id)
    if (idx !== -1) {
      myDatasets.value[idx] = { ...myDatasets.value[idx], is_pinned: !ds.is_pinned }
    }
  } catch (err) {
    ElMessage.error('操作失败：' + (err.message || err))
  }
}

const toggleTag = (tag) => {
  const idx = uploadForm.tags.indexOf(tag)
  if (idx >= 0) uploadForm.tags.splice(idx, 1)
  else uploadForm.tags.push(tag)
}
const removeTag = (tag) => { uploadForm.tags = uploadForm.tags.filter(t => t !== tag) }
const addCustomTag = () => {
  const tag = customTag.value.trim()
  if (tag && !uploadForm.tags.includes(tag)) uploadForm.tags.push(tag)
  customTag.value = ''
}

const handleClickOutside = (e) => {
  if (tagDropdownRef.value && !tagDropdownRef.value.contains(e.target)) showTagDropdown.value = false
}

onMounted(() => { fetchDatasets(); document.addEventListener('click', handleClickOutside) })
onUnmounted(() => { document.removeEventListener('click', handleClickOutside) })

const handleUpload = () => {
  uploading.value = true
  setTimeout(() => {
    showUpload.value = false
    uploadForm.name = ''; uploadForm.description = ''; uploadForm.tags = []
    uploading.value = false
    ElMessage.success('数据集上传功能开发中')
  }, 1000)
}

const openEditDialog = (ds) => {
  currentDataset.value = ds
  editForm.name = ds.name
  editForm.description = ds.description || ''
  nameError.value = ''
  editDialogVisible.value = true
}

const confirmEdit = async () => {
  if (!currentDataset.value) return
  nameError.value = ''
  const newName = editForm.name.trim()
  if (!newName) { nameError.value = '数据集名称不能为空'; return }
  saving.value = true
  try {
    const updated = await updateDataset(currentDataset.value.id, {
      name: newName,
      description: editForm.description.trim(),
    })
    const idx = myDatasets.value.findIndex(d => d.id === currentDataset.value.id)
    if (idx !== -1) myDatasets.value[idx] = { ...myDatasets.value[idx], ...updated }
    editDialogVisible.value = false
    ElMessage.success('数据集信息已保存')
  } catch (err) {
    if (err.message && err.message.includes('已被占用')) {
      nameError.value = err.message
    } else {
      ElMessage.error('保存失败：' + (err.message || err))
    }
  } finally {
    saving.value = false
  }
}

const handlePublish = async (ds) => {
  actionLoading.value = ds.id
  try {
    const updated = await publishDataset(ds.id)
    const idx = myDatasets.value.findIndex(d => d.id === ds.id)
    if (idx !== -1) myDatasets.value[idx] = { ...myDatasets.value[idx], ...updated }
    ElMessage.success(`「${ds.name}」已发布到公共数据集`)
  } catch (err) {
    ElMessage.error('发布失败：' + (err.message || err))
  } finally {
    actionLoading.value = null
  }
}

const handleUnpublish = async (ds) => {
  actionLoading.value = ds.id
  try {
    const updated = await unpublishDataset(ds.id)
    const idx = myDatasets.value.findIndex(d => d.id === ds.id)
    if (idx !== -1) myDatasets.value[idx] = { ...myDatasets.value[idx], ...updated }
    ElMessage.success(`「${ds.name}」已取消发布`)
  } catch (err) {
    ElMessage.error('取消发布失败：' + (err.message || err))
  } finally {
    actionLoading.value = null
  }
}

const openDeleteDialog = (ds) => {
  currentDataset.value = ds
  deleteConfirmName.value = ''
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  if (!canConfirmDelete.value) return
  deleting.value = true
  try {
    await deleteDataset(currentDataset.value.id)
    myDatasets.value = myDatasets.value.filter(d => d.id !== currentDataset.value.id)
    deleteDialogVisible.value = false
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error('删除失败：' + (err.message || err))
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.my-datasets-page { max-width: 1200px; margin: 0 auto; }

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 28px;
}
.page-header h2 { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Loading */
.loading-state { text-align: center; padding: 60px; color: var(--text-tertiary); }
.spinner {
  width: 36px; height: 36px; border: 3px solid var(--border-color);
  border-top-color: var(--accent-primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Grid */
.datasets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* Card */
.dataset-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}
.dataset-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.dataset-card.published { border-color: rgba(58, 125, 126, 0.35); }

.card-banner {
  background: linear-gradient(135deg, var(--accent-light) 0%, rgba(58,125,126,0.06) 100%);
  padding: 16px 20px;
  display: flex; align-items: center; gap: 12px;
  border-bottom: 1px solid var(--border-color);
}
.dark .card-banner { background: linear-gradient(135deg, rgba(58,125,126,0.12) 0%, rgba(58,125,126,0.05) 100%); }
.banner-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  color: var(--accent-primary); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.banner-right { display: flex; flex-direction: row; align-items: center; gap: 6px; margin-left: auto; }
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 600;
  white-space: nowrap;
}
.published-badge {
  background: rgba(5, 150, 105, 0.12); color: var(--success);
  border: 1px solid rgba(5, 150, 105, 0.25);
}
.count-badge { background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid var(--border-color); }
.pin-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 8px;
  border: 1.5px solid var(--border-color); background: var(--bg-secondary);
  color: var(--text-tertiary); cursor: pointer; transition: all 0.15s;
  padding: 0; flex-shrink: 0;
}
.pin-btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); background: rgba(58,125,126,0.08); }
.pin-btn.pinned { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }

.card-body { padding: 16px 20px; flex: 1; display: flex; flex-direction: column; gap: 10px; }
.card-title { font-size: 15px; font-weight: 700; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.55;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; min-height: 2.6em;
}
.card-stats {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 8px; padding: 10px 0;
  border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color);
}
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 11px; color: var(--text-tertiary); font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; }
.stat-value { font-size: 13px; color: var(--text-primary); font-weight: 600; }
.card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.card-tag { padding: 2px 8px; border-radius: 4px; background: var(--accent-light); color: var(--accent-primary); font-size: 11px; font-weight: 500; }
.published-info { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-tertiary); margin-top: auto; padding-top: 4px; }

.card-actions { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid var(--border-color); background: var(--bg-primary); }
.card-actions .app-btn { flex: 1; justify-content: center; }

/* Edit form dialog */
.edit-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.edit-input {
  padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 10px;
  font-size: 14px; background: var(--bg-primary); color: var(--text-primary);
  font-family: inherit; resize: vertical; transition: all 0.2s;
}
.edit-input:focus { outline: none; border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(58,125,126,0.1); }
.edit-input::placeholder { color: var(--text-tertiary); }
textarea.edit-input { min-height: 80px; }
.field-error { font-size: 12px; color: var(--danger); margin-top: 2px; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }

/* Delete dialog */
.delete-body { display: flex; flex-direction: column; gap: 16px; }
.delete-warning { display: flex; gap: 14px; align-items: flex-start; padding: 14px; background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.15); border-radius: 10px; }
.delete-warning-icon { color: var(--danger); flex-shrink: 0; margin-top: 2px; }
.delete-warning-title { font-size: 14px; font-weight: 600; color: var(--danger); margin-bottom: 4px; }
.delete-warning-detail { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.delete-summary { display: flex; flex-direction: column; gap: 6px; padding: 12px 14px; background: var(--bg-primary); border-radius: 8px; }
.delete-summary-row { display: flex; justify-content: space-between; align-items: center; }
.delete-summary-label { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.delete-summary-value { font-size: 13px; color: var(--text-primary); font-weight: 600; }
.delete-summary-value.name { color: var(--accent-primary); }
.delete-confirm-input { display: flex; flex-direction: column; gap: 6px; }
.delete-confirm-input label { font-size: 13px; color: var(--text-secondary); }
.delete-confirm-input label code { font-family: monospace; background: var(--bg-tertiary); padding: 1px 6px; border-radius: 4px; color: var(--text-primary); }
.delete-input {
  padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 10px;
  font-size: 14px; background: var(--bg-primary); color: var(--text-primary);
  font-family: inherit; transition: all 0.2s;
}
.delete-input:focus { outline: none; border-color: var(--danger); box-shadow: 0 0 0 3px rgba(220,38,38,0.1); }
.delete-input::placeholder { color: var(--text-tertiary); }

/* Empty state */
.empty-state { text-align: center; padding: 80px 20px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 16px; }
.empty-icon { margin-bottom: 20px; color: var(--text-tertiary); }
.empty-state h3 { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 10px; }
.empty-state p { font-size: 14px; color: var(--text-secondary); line-height: 1.7; margin-bottom: 20px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: var(--bg-secondary); border-radius: 16px; padding: 28px; width: 100%; max-width: 520px; box-shadow: var(--shadow-lg); max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h3 { font-size: 18px; font-weight: 600; color: var(--text-primary); }
.modal-close { background: none; border: none; font-size: 24px; color: var(--text-tertiary); cursor: pointer; padding: 4px; line-height: 1; }
.modal-close:hover { color: var(--text-primary); }
.upload-form { display: flex; flex-direction: column; gap: 16px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }

/* Tag selector */
.tag-selector { display: flex; flex-direction: column; gap: 8px; }
.selected-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.selected-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: var(--accent-light); color: var(--accent-primary); border-radius: 6px; font-size: 13px; font-weight: 500; }
.tag-remove { background: none; border: none; color: var(--accent-primary); cursor: pointer; font-size: 16px; line-height: 1; padding: 0 2px; opacity: 0.7; }
.tag-remove:hover { opacity: 1; }
.tag-dropdown { position: relative; }
.dropdown-trigger { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 10px; background: var(--bg-primary); cursor: pointer; transition: all 0.2s; }
.dropdown-trigger:hover { border-color: var(--accent-primary); }
.dropdown-trigger .placeholder { color: var(--text-tertiary); font-size: 14px; }
.dropdown-trigger .chevron { transition: transform 0.2s; color: var(--text-tertiary); }
.dropdown-trigger .chevron.open { transform: rotate(180deg); }
.dropdown-menu { position: absolute; top: 100%; left: 0; right: 0; margin-top: 4px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; box-shadow: var(--shadow-lg); z-index: 100; max-height: 280px; overflow-y: auto; }
.dropdown-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; font-size: 14px; color: var(--text-primary); cursor: pointer; transition: background 0.15s; }
.dropdown-item:hover { background: var(--bg-hover); }
.dropdown-item.selected { background: var(--accent-light); color: var(--accent-primary); }
.checkbox { width: 18px; height: 18px; border: 2px solid var(--border-color); border-radius: 4px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.15s; }
.checkbox.checked { background: var(--accent-primary); border-color: var(--accent-primary); color: white; }
.dropdown-divider { height: 1px; background: var(--border-color); margin: 4px 0; }
.custom-tag-row { display: flex; gap: 8px; padding: 10px 14px; }
.custom-tag-input { flex: 1; padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 13px; background: var(--bg-primary); color: var(--text-primary); }
.custom-tag-input:focus { outline: none; border-color: var(--accent-primary); }
.add-custom-btn { padding: 6px 12px; background: var(--accent-primary); color: white; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: opacity 0.2s; }
.add-custom-btn:hover { opacity: 0.9; }
.add-custom-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.file-drop-zone { border: 2px dashed var(--border-color); border-radius: 12px; padding: 32px; text-align: center; color: var(--text-tertiary); transition: all 0.2s; }
.file-drop-zone:hover { border-color: var(--accent-primary); }
.file-drop-zone p { font-size: 13px; margin-top: 8px; }
.browse-link { color: var(--accent-primary); cursor: pointer; font-weight: 500; }
.hint { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }
.form-group input, .form-group textarea { padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 10px; font-size: 14px; background: var(--bg-primary); color: var(--text-primary); font-family: inherit; resize: vertical; }
.form-group input:focus, .form-group textarea:focus { outline: none; border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(58,125,126,0.1); }
.form-group input::placeholder, .form-group textarea::placeholder { color: var(--text-tertiary); }
</style>

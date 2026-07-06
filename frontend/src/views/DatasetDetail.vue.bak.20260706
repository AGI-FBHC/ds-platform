<template>
  <div class="dataset-detail-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载数据集...</p>
    </div>

    <!-- Not found -->
    <div v-else-if="!dataset" class="not-found">
      <h3>数据集不存在或无权访问</h3>
      <button class="app-btn primary" @click="$router.back()">返回</button>
    </div>

    <template v-else>
      <!-- Back -->
      <div class="back-bar">
        <button class="app-btn ghost small" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="14" height="14">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          返回
        </button>
      </div>

      <!-- Dataset header -->
      <div class="dataset-header">
        <div class="header-banner">
          <div class="banner-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="32" height="32">
              <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="header-badges">
            <button v-if="dataset.is_published" class="badge download-btn" @click="handleDownload" title="下载数据集">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="13" height="13">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              下载
            </button>
          </div>
        </div>

        <div class="header-body">
          <div class="header-left">
            <h1 class="dataset-title">{{ dataset.name }}</h1>
            <p class="dataset-desc">{{ dataset.description || '暂无描述' }}</p>

            <div class="header-meta">
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="13" height="13">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ dataset.owner_nickname || '未知用户' }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="13" height="13">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ isPublished ? ('发布于 ' + formatDate(dataset.published_at)) : ('创建于 ' + formatDate(dataset.created_at)) }}
              </span>
            </div>

            <div v-if="tags.length > 0" class="header-tags">
              <span v-for="tag in tags" :key="tag" class="header-tag">{{ tag }}</span>
            </div>
          </div>

          <div class="header-stats">
            <div class="stat-card">
              <span class="stat-num">{{ formatNumber(dataset.image_count) }}</span>
              <span class="stat-lbl">样本数</span>
            </div>
            <div class="stat-card">
              <span class="stat-num">{{ formatSize(dataset.total_size) }}</span>
              <span class="stat-lbl">总大小</span>
            </div>
            <div class="stat-card">
              <span class="stat-num">{{ dataset.format?.toUpperCase() || 'JPG' }}</span>
              <span class="stat-lbl">格式</span>
            </div>
            <div class="stat-card">
              <span class="stat-num">{{ dataset.source || 'BAIDU' }}</span>
              <span class="stat-lbl">来源</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Image grid -->
      <div class="images-section" :class="{ 'fullscreen-active': listFullscreen }">
        <div class="section-header">
          <h2>样本预览</h2>
          <div class="header-right">
            <span class="image-count">{{ formatNumber(totalImages) }} 张图片</span>
            <div class="view-toggle">
              <button
                class="toggle-btn"
                :class="{ active: viewMode === 'grid' }"
                @click="viewMode = 'grid'"
                title="网格视图"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                  <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
              <button
                class="toggle-btn"
                :class="{ active: viewMode === 'list' }"
                @click="viewMode = 'list'"
                title="列表视图"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                  <line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
            <button v-if="viewMode === 'list'" class="fullscreen-btn" @click="listFullscreen = !listFullscreen" :title="listFullscreen ? '退出全屏' : '全屏'">
              <img v-show="!listFullscreen" class="icon-light" src="/logos/全屏.png" width="18" height="18" alt="全屏" />
              <img v-show="!listFullscreen" class="icon-dark" src="/logos/全屏 (1).png" width="18" height="18" alt="全屏" />
              <img v-show="listFullscreen" class="icon-light" src="/logos/退出全屏.png" width="18" height="18" alt="退出全屏" />
              <img v-show="listFullscreen" class="icon-dark" src="/logos/退出全屏 (1).png" width="18" height="18" alt="退出全屏" />
            </button>
          </div>
        </div>

        <!-- Grid view -->
        <div v-if="filteredImages.length > 0 && viewMode === 'grid'" class="image-grid">
          <div
            v-for="(img, idx) in paginatedImages"
            :key="img.id"
            class="image-thumb"
            @click="openDetail(idx)"
          >
            <div class="thumb-wrap">
              <img
                :src="datasetImageUrl(dataset.id, img.relative_path, true)"
                :alt="img.filename"
                loading="lazy"
                @error="onImgError($event)"
              />
              <div v-if="img.mask_relative_path" class="thumb-mask">
                <img
                  :src="datasetImageUrl(dataset.id, img.mask_relative_path, true)"
                  alt="mask"
                  @error="onImgError($event)"
                />
              </div>
            </div>
            <div class="thumb-info">
              <span class="thumb-name" :title="img.keyword || img.filename">{{ img.keyword || '—' }}</span>
              <span v-if="img.width && img.height" class="thumb-size">{{ img.width }}×{{ img.height }}</span>
            </div>
          </div>
        </div>

        <!-- List view -->
        <div v-if="filteredImages.length > 0 && viewMode === 'list'" class="image-list">
          <!-- List header -->
          <div class="list-header" :style="listGridStyle">
            <div class="col col-thumb">原图</div>
            <div class="col col-mask">Mask</div>
            <div class="col col-keyword">
              关键词
              <button class="col-filter-btn" @click="openColFilter('keyword')" :class="{ active: colFilters.keyword }" title="筛选">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              </button>
            </div>
            <div v-for="ax in axes" :key="ax.axis_key" class="col col-axis">
              {{ ax.axis_name }}
              <button class="col-filter-btn" @click="openColFilter(ax.axis_key)" :class="{ active: colFilters[ax.axis_key] }" title="筛选">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              </button>
            </div>
            <div class="col col-source">
              来源页
              <button class="col-filter-btn" @click="openColFilter('source_page_title')" :class="{ active: colFilters.source_page_title }" title="筛选">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              </button>
            </div>
            <div class="col col-size">尺寸</div>
          </div>
          <!-- List rows -->
          <div
            v-for="(img, idx) in paginatedImages"
            :key="img.id"
            class="list-row"
            :style="listGridStyle"
            @click="openDetail(idx)"
          >
            <div class="col col-thumb">
              <div class="list-thumb-wrap">
                <img
                  :src="datasetImageUrl(dataset.id, img.relative_path, true)"
                  :alt="img.filename"
                  loading="lazy"
                  @error="onImgError($event)"
                />
              </div>
            </div>
            <div class="col col-mask">
              <div v-if="img.mask_relative_path" class="list-mask-thumb">
                <img
                  :src="datasetImageUrl(dataset.id, img.mask_relative_path, true)"
                  alt="mask"
                  @error="onImgError($event)"
                />
              </div>
              <span v-else class="mask-none">—</span>
            </div>
            <div class="col col-keyword">{{ img.keyword || '—' }}</div>
            <div v-for="ax in axes" :key="ax.axis_key" class="col col-axis">
              {{ (img.labels || {})[ax.axis_key] || '—' }}
            </div>
            <div class="col col-source" :title="img.source_page_title">{{ img.source_page_title || '—' }}</div>
            <div class="col col-size">{{ img.width || '?' }} × {{ img.height || '?' }}</div>
          </div>
        </div>

        <div v-else-if="!loadingImages" class="empty-grid">
          <p>没有找到匹配的样本</p>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button class="app-btn ghost small" :disabled="currentPage === 1" @click="currentPage--">
            上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button class="app-btn ghost small" :disabled="currentPage === totalPages" @click="currentPage++">
            下一页
          </button>
        </div>
      </div>
    </template>

    <!-- Column filter dialog -->
    <el-dialog v-model="colFilterVisible" :title="'筛选 ' + colFilterLabel" width="380" align-center destroy-on-close>
      <div class="col-filter-body">
        <p class="col-filter-hint">输入值筛选 <b>{{ colFilterLabel }}</b> 列（支持模糊匹配）</p>
        <input v-model="colFilterValue" class="col-filter-input" :placeholder="'输入 ' + colFilterLabel + '...'" @keydown.enter="applyColFilter" />
      </div>
      <template #footer>
        <button class="app-btn ghost" @click="colFilterVisible = false">取消</button>
        <button v-if="colFilters[colFilterKey]" class="app-btn ghost" @click="clearColFilter(colFilterKey); colFilterVisible = false">清除</button>
        <button class="app-btn primary" @click="applyColFilter">确定</button>
      </template>
    </el-dialog>

    <!-- Detail dialog -->
    <el-dialog
      v-model="detailVisible"
      width="840"
      align-center
      destroy-on-close
      class="image-detail-dialog"
      :title="detailImage ? `${detailImage.filename}  (${detailIndex + 1} / ${filteredImages.length})` : '样本详情'"
    >
      <div v-if="detailImage" class="detail-content">
        <div class="detail-preview">
          <button class="preview-nav prev" :disabled="!hasPrev" @click="gotoPrev">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="24" height="24"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="preview-main">
            <img
              :src="datasetImageUrl(dataset.id, detailImage.relative_path)"
              :alt="detailImage.filename"
              @error="onImgError($event)"
            />
          </div>
          <button class="preview-nav next" :disabled="!hasNext" @click="gotoNext">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="24" height="24"><path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div
            class="mask-preview"
            :class="{ empty: !detailImage.mask_relative_path }"
          >
            <img
              v-if="detailImage.mask_relative_path"
              :src="datasetImageUrl(dataset.id, detailImage.mask_relative_path)"
              :alt="detailImage.filename + '.mask'"
              @error="onImgError($event)"
            />
            <div v-else class="mask-empty-detail">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="28" height="28">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              <span>暂无 Mask</span>
            </div>
          </div>
        </div>
        <div class="detail-fields">
          <div class="field readonly">
            <label>文件名</label>
            <span>{{ detailImage.filename }}</span>
          </div>
          <div v-if="detailImage.keyword" class="field readonly">
            <label>关键词</label>
            <span>{{ detailImage.keyword }}</span>
          </div>
          <div class="field readonly">
            <label>尺寸</label>
            <span>{{ detailImage.width || '?' }} × {{ detailImage.height || '?' }} px</span>
          </div>
          <div v-if="detailImage.source_page_title" class="field readonly">
            <label>来源页标题</label>
            <span class="readonly-text">{{ detailImage.source_page_title }}</span>
          </div>
          <div v-if="detailImage.url" class="field readonly">
            <label>来源 URL</label>
            <a class="readonly-text url-link" :href="detailImage.url" target="_blank" rel="noopener">{{ truncateUrl(detailImage.url) }}</a>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDataset, getPublicDataset, listDatasetImages, listPublicDatasetImages, datasetImageUrl } from '@/utils/api'

const route = useRoute()
const datasetId = computed(() => route.params.id)

const dataset = ref(null)
const loading = ref(true)
const loadingImages = ref(false)
const listFullscreen = ref(false)

const handleKeydown = (e) => {
  if (e.key === 'Escape' && listFullscreen.value) {
    listFullscreen.value = false
  }
}

onMounted(() => { window.addEventListener('keydown', handleKeydown) })
onUnmounted(() => { window.removeEventListener('keydown', handleKeydown) })
const allImages = ref([])
const colFilters = ref({})
const colFilterVisible = ref(false)
const colFilterKey = ref('')
const colFilterValue = ref('')
const viewMode = ref('grid')
const currentPage = ref(1)
const pageSize = 48

const detailVisible = ref(false)
const detailIndex = ref(0)
const detailImage = ref(null)

const colFilterLabel = computed(() => {
  const labels = { keyword: '关键词', source_page_title: '来源页' }
  if (labels[colFilterKey.value]) return labels[colFilterKey.value]
  const ax = axes.value.find(a => a.axis_key === colFilterKey.value)
  return ax ? ax.axis_name : colFilterKey.value
})

const openColFilter = (key) => {
  colFilterKey.value = key
  colFilterValue.value = colFilters.value[key] || ''
  colFilterVisible.value = true
}

const applyColFilter = () => {
  if (colFilterValue.value) {
    colFilters.value = { ...colFilters.value, [colFilterKey.value]: colFilterValue.value }
  } else {
    const f = { ...colFilters.value }
    delete f[colFilterKey.value]
    colFilters.value = f
  }
  colFilterVisible.value = false
}

const clearColFilter = (key) => {
  const f = { ...colFilters.value }
  delete f[key]
  colFilters.value = f
}

const isPublished = computed(() => dataset.value?.is_published)
const tags = computed(() => {
  const fields = dataset.value?.fields || {}
  return fields.tags || []
})
const axes = computed(() => {
  const fields = dataset.value?.fields || {}
  return fields.classification_axes || []
})

const listGridStyle = computed(() => {
  const cols = ['60px', '60px', '120px', ...axes.value.map(() => '1fr'), '1fr', '100px']
  return { 'grid-template-columns': cols.join(' ') }
})

const totalImages = computed(() => filteredImages.value.length)

const filteredImages = computed(() => {
  const filters = colFilters.value
  if (!Object.keys(filters).length) return allImages.value
  return allImages.value.filter(img => {
    for (const [key, val] of Object.entries(filters)) {
      let cellVal
      if (key === 'keyword') cellVal = (img.keyword || '') + (img.filename || '')
      else if (key === 'source_page_title') cellVal = img.source_page_title || ''
      else cellVal = (img.labels || {})[key] || ''
      if (!cellVal.toLowerCase().includes(val.toLowerCase())) return false
    }
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredImages.value.length / pageSize)))

const paginatedImages = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredImages.value.slice(start, start + pageSize)
})

const hasPrev = computed(() => detailIndex.value > 0)
const hasNext = computed(() => detailIndex.value < filteredImages.value.length - 1)


const openDetail = (idx) => {
  detailIndex.value = idx
  detailImage.value = filteredImages.value[idx]
  detailVisible.value = true
}

const gotoPrev = () => {
  if (!hasPrev.value) return
  detailIndex.value--
  detailImage.value = filteredImages.value[detailIndex.value]
}

const gotoNext = () => {
  if (!hasNext.value) return
  detailIndex.value++
  detailImage.value = filteredImages.value[detailIndex.value]
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

const truncateUrl = (url) => {
  if (!url) return ''
  return url.length > 50 ? url.slice(0, 47) + '...' : url
}

const onImgError = (e) => {
  e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="150"><rect fill="%23f1f5f9" width="200" height="150"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2394a3b8" font-size="13">加载失败</text></svg>'
}

const fetchDataset = async () => {
  loading.value = true
  try {
    // Use public endpoint for guest routes, authenticated endpoint for app routes
    const usePublic = route.path.startsWith('/dataset/')
    dataset.value = usePublic
      ? await getPublicDataset(datasetId.value)
      : await getDataset(datasetId.value)
  } catch (err) {
    dataset.value = null
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

const fetchImages = async () => {
  loadingImages.value = true
  try {
    const usePublic = route.path.startsWith('/dataset/')
    const page1 = usePublic
      ? await listPublicDatasetImages(datasetId.value, { limit: 500, offset: 0 })
      : await listDatasetImages(datasetId.value, { limit: 500, offset: 0 })
    allImages.value = page1.items || []
  } catch (err) {
    allImages.value = []
  } finally {
    loadingImages.value = false
  }
}

onMounted(async () => {
  await fetchDataset()
  if (dataset.value) await fetchImages()
})

const handleDownload = () => {
  ElMessage.warning('服务器升级中，需要下载请联系管理员：gejie@stu.jiangnan.edu.cn')
}
</script>

<style scoped>
.dataset-detail-page { max-width: 1200px; margin: 0 auto; }

.loading-state, .not-found { text-align: center; padding: 80px 20px; color: var(--text-tertiary); }
.loading-state p, .not-found p { font-size: 15px; margin-top: 12px; }
.not-found h3 { font-size: 18px; color: var(--text-primary); margin-bottom: 20px; }
.spinner { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.back-bar { margin-bottom: 20px; }

.dataset-header {
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  border-radius: 16px; overflow: hidden; margin-bottom: 28px;
}
.header-banner {
  background: linear-gradient(135deg, var(--accent-light) 0%, rgba(58,125,126,0.06) 100%);
  padding: 20px 24px; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}
.dark .header-banner { background: linear-gradient(135deg, rgba(58,125,126,0.12) 0%, rgba(58,125,126,0.05) 100%); }
.banner-icon {
  width: 56px; height: 56px; border-radius: 14px;
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  color: var(--accent-primary); display: flex; align-items: center; justify-content: center;
}
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.download-btn { display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1px solid rgba(58,125,126,0.35); background: rgba(58,125,126,0.08); color: var(--accent-primary); transition: all 0.15s; }
.download-btn:hover { background: rgba(58,125,126,0.15); border-color: var(--accent-primary); }

.header-body { padding: 20px 24px; display: flex; gap: 32px; align-items: flex-start; }
.header-left { flex: 1; min-width: 0; }
.dataset-title { font-size: 22px; font-weight: 800; color: var(--text-primary); margin-bottom: 8px; word-break: break-all; }
.dataset-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; }
.header-meta { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 12px; }
.meta-item { display: flex; align-items: center; gap: 5px; font-size: 13px; color: var(--text-secondary); }
.header-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.header-tag { padding: 3px 10px; border-radius: 20px; background: var(--accent-light); color: var(--accent-primary); font-size: 12px; font-weight: 500; }

.header-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; flex-shrink: 0; }
.stat-card { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px; text-align: center; }
.stat-num { font-size: 18px; font-weight: 800; color: var(--accent-primary); }
.stat-lbl { font-size: 11px; color: var(--text-tertiary); font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; }

/* Images section */
.images-section { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 16px; padding: 20px 24px; }
.images-section.fullscreen-active { position: fixed; inset: 0; z-index: 999; background: var(--bg-primary); display: flex; flex-direction: column; padding: 20px 24px; overflow: hidden; border-radius: 0; border: none; }
.fullscreen-btn { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; border: none; background: rgba(58,125,126,0.08); backdrop-filter: blur(8px); cursor: pointer; transition: all 0.15s; flex-shrink: 0; }
.fullscreen-btn .icon-dark { display: none; }
.dark .fullscreen-btn .icon-light { display: none; }
.dark .fullscreen-btn .icon-dark { display: block; }
.fullscreen-btn:hover { background: rgba(58,125,126,0.15); }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.section-header h2 { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.image-count { font-size: 13px; color: var(--text-tertiary); }

.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.search-input-wrap { position: relative; flex: 1; min-width: 180px; }
.search-ico { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-tertiary); pointer-events: none; }
.search-input { width: 100%; padding: 8px 12px 8px 32px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 13px; background: var(--bg-primary); color: var(--text-primary); transition: all 0.2s; }
.search-input:focus { outline: none; border-color: var(--accent-primary); }
.search-input::placeholder { color: var(--text-tertiary); }

.image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; }
.image-thumb { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; cursor: pointer; transition: all 0.15s; }
.image-thumb:hover { border-color: var(--accent-primary); box-shadow: var(--shadow-sm); transform: translateY(-1px); }
.thumb-wrap { position: relative; padding-top: 75%; background: var(--bg-tertiary); }
.thumb-wrap img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.thumb-mask {
  position: absolute;
  bottom: 0; right: 0;
  width: 33.33%;
  padding-top: 33.33%;
  border-left: 1px solid rgba(255,255,255,0.4);
  border-top: 1px solid rgba(255,255,255,0.4);
  overflow: hidden;
  box-sizing: border-box;
}
.thumb-mask img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.9;
}
.thumb-info { padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; }
.thumb-name { font-size: 11px; color: var(--text-primary); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.thumb-size { font-size: 10px; color: var(--text-tertiary); }

.empty-grid { text-align: center; padding: 40px; color: var(--text-tertiary); font-size: 14px; }

.view-toggle { display: flex; gap: 4px; }
.toggle-btn {
  padding: 6px 8px; border-radius: 8px; border: 1px solid var(--border-color);
  background: var(--bg-primary); color: var(--text-tertiary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.toggle-btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
.toggle-btn.active { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }

/* List view */
.image-list { display: flex; flex-direction: column; border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
.list-header {
  display: grid; gap: 0; padding: 10px 16px;
  background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color);
}
.list-header .col { font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.4px; }
.list-row {
  display: grid; gap: 0; padding: 8px 16px;
  align-items: center; cursor: pointer;
  border-bottom: 1px solid var(--border-color); transition: background 0.15s;
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: var(--bg-hover); }
.list-thumb-wrap { width: 48px; height: 48px; border-radius: 8px; overflow: hidden; background: var(--bg-tertiary); flex-shrink: 0; }
.list-thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
.list-mask-thumb { width: 48px; height: 48px; border-radius: 8px; overflow: hidden; background: var(--bg-tertiary); }
.list-mask-thumb img { width: 100%; height: 100%; object-fit: cover; }
.mask-none { color: var(--text-tertiary); font-size: 14px; }
.col { font-size: 13px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col.col-keyword { color: var(--text-secondary); }
.col.col-source { color: var(--text-tertiary); font-size: 12px; }
.col.col-size { color: var(--text-tertiary); font-size: 12px; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 20px; }
.page-info { font-size: 13px; color: var(--text-secondary); }

/* Detail dialog */
:deep(.image-detail-dialog .el-dialog__body) { padding: 0; }
.detail-content { display: flex; gap: 0; min-height: 480px; }
.detail-preview { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-primary); padding: 16px; gap: 8px; position: relative; min-width: 0; }
.preview-nav { position: absolute; top: 50%; transform: translateY(-50%); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-secondary); transition: all 0.15s; z-index: 2; }
.preview-nav:hover:not(:disabled) { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }
.preview-nav:disabled { opacity: 0.3; cursor: not-allowed; }
.preview-nav.prev { left: 8px; }
.preview-nav.next { right: 8px; }
.preview-main { flex: 1; display: flex; align-items: center; justify-content: center; max-height: 380px; width: 100%; }
.preview-main img { max-width: 100%; max-height: 380px; object-fit: contain; border-radius: 6px; }
.mask-preview { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.mask-preview:not(.empty) { border-top: 1px solid var(--border-color); padding-top: 8px; }
.mask-preview img { max-width: 100%; max-height: 100px; object-fit: contain; border-radius: 4px; opacity: 0.85; }
.mask-preview.empty { border-top: 1px dashed var(--border-color); padding: 10px; }
.mask-empty-detail { display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--text-tertiary); }
.mask-empty-detail span { font-size: 11px; }
.col-filter-btn { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border: none; background: transparent; cursor: pointer; color: var(--text-tertiary); padding: 0; border-radius: 3px; vertical-align: middle; margin-left: 3px; transition: all 0.15s; }
.col-filter-btn:hover { color: var(--accent-primary); }
.col-filter-btn.active { color: #fff; background: var(--accent-primary); }
.col-filter-body { padding: 4px 0 12px; }
.col-filter-hint { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
.col-filter-hint b { color: var(--text-primary); }
.col-filter-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 13px; background: var(--bg-secondary); color: var(--text-primary); box-sizing: border-box; }
.col-filter-input:focus { outline: none; border-color: var(--accent-primary); }
.detail-fields { width: 240px; flex-shrink: 0; padding: 20px 16px; border-left: 1px solid var(--border-color); overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 11px; color: var(--text-tertiary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }
.field span, .field a { font-size: 13px; color: var(--text-primary); }
.readonly-text { word-break: break-all; font-size: 12px; }
.url-link { color: var(--accent-primary); text-decoration: none; }
.url-link:hover { text-decoration: underline; }
</style>

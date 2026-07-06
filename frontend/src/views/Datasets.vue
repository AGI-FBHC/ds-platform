<template>
  <div class="datasets-page">
    <!-- Hero section (guest mode) -->
    <div v-if="isGuest" class="guest-hero">
      <div class="hero-inner">
        <div class="hero-brand">
          <img src="/logos/gpt1trans.png" alt="AGI&FBHC DataSphere" width="40" height="40" />
          <h1>AGI&FBHC DataSphere</h1>
        </div>
        <p class="hero-desc">开放数据集浏览与共享平台</p>
        <div class="hero-actions">
          <button class="hero-btn primary" @click="$router.push('/')">登录 / 注册</button>
          <button class="hero-btn ghost" @click="scrollToContent">浏览数据集</button>
        </div>
      </div>
    </div>

    <!-- Search and filters -->
    <div class="datasets-content" ref="contentRef">
      <div class="search-bar">
        <div class="search-input-wrapper">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18" class="search-icon">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索数据集名称、标签或描述..." @input="handleSearch" />
        </div>
        <div class="filter-tags">
          <button
            v-if="!isGuest"
            class="filter-tag my-tag"
            :class="{ active: showMyOnly }"
            @click="showMyOnly = !showMyOnly"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="14" height="14">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            我的
          </button>
          <button
            v-for="tag in availableTags"
            :key="tag"
            class="filter-tag"
            :class="{ active: selectedTags.includes(tag) }"
            @click="toggleTag(tag)"
          >{{ tag }}</button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载数据集...</p>
      </div>

      <!-- Dataset grid -->
      <div v-else class="datasets-grid">
        <div
          v-for="ds in filteredDatasets"
          :key="ds.id"
          class="dataset-card"
        >
          <div class="card-banner">
            <div class="banner-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="26" height="26">
                <ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="1.5"/>
                <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="1.5"/>
                <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="banner-meta">
              <span class="card-owner">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ ds.owner_nickname || '未知用户' }}
              </span>
              <span class="card-count">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                  <polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ formatNumber(ds.image_count) }}
              </span>
              <button
                v-if="!isGuest && ds.user_id === currentUserId"
                class="pin-btn"
                :class="{ pinned: ds.is_pinned }"
                @click="togglePin(ds, $event)"
                :title="ds.is_pinned ? '取消置顶' : '置顶'"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="11" height="11">
                  <path d="M12 2L12 22M12 2L8 6M12 2L16 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="card-body" @click="openDataset(ds)">
            <h3 class="card-title">{{ ds.name }}</h3>
            <p class="card-desc">{{ ds.description || '暂无描述' }}</p>

            <div class="card-info-row">
              <span class="info-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                {{ formatSize(ds.total_size) }}
              </span>
              <span class="info-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ ds.published_at ? formatDate(ds.published_at) : formatDate(ds.created_at) }}
              </span>
            </div>

            <div v-if="getTags(ds).length > 0" class="card-tags">
              <span v-for="tag in getTags(ds)" :key="tag" class="card-tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && filteredDatasets.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="48" height="48">
          <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="1.5"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <p>{{ searchQuery || selectedTags.length ? '未找到匹配的数据集' : '暂无公开数据集' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, listPublicDatasets, listDatasets, pinDataset, unpinDataset, getUserInfo } from '@/utils/api'

const router = useRouter()

const isGuest = computed(() => !isLoggedIn())
const currentUserId = computed(() => getUserInfo()?.id)
const searchQuery = ref('')
const selectedTags = ref([])
const showMyOnly = ref(false)
const contentRef = ref(null)
const loading = ref(false)
const pinnedIds = ref(new Set())

const togglePin = async (ds, event) => {
  event.stopPropagation()
  if (!isLoggedIn()) return
  try {
    if (ds.is_pinned) {
      await unpinDataset(ds.id)
    } else {
      await pinDataset(ds.id)
    }
    await fetchPublicDatasets()
    await fetchMyPublished()
  } catch (err) {
    console.warn('Pin toggle failed:', err)
  }
}

const publicDatasets = ref([])
const myPublishedDatasets = ref([])

const predefinedTags = ['NLP', 'CV', 'Audio', 'Tabular', 'Multimodal', 'Medical', 'Biology', 'Chemistry']

const availableTags = computed(() => {
  const allTags = new Set(predefinedTags)
  for (const ds of publicDatasets.value) {
    const tags = getTags(ds)
    tags.forEach(t => allTags.add(t))
  }
  return [...allTags]
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

const fetchPublicDatasets = async () => {
  loading.value = true
  try {
    publicDatasets.value = await listPublicDatasets()
  } catch (err) {
    console.warn('Failed to fetch public datasets:', err)
  } finally {
    loading.value = false
  }
}

const fetchMyPublished = async () => {
  if (isGuest.value) return
  try {
    const all = await listDatasets()
    myPublishedDatasets.value = all.filter(ds => ds.is_published)
    pinnedIds.value = new Set(all.filter(ds => ds.is_published && ds.is_pinned).map(ds => ds.id))
  } catch (err) {
    console.warn('Failed to fetch my published datasets:', err)
  }
}

const handleSearch = () => {
  // Search is reactive via computed, no debounce needed at this stage
}

const toggleTag = (tag) => {
  const idx = selectedTags.value.indexOf(tag)
  if (idx >= 0) selectedTags.value.splice(idx, 1)
  else selectedTags.value.push(tag)
}

const filteredDatasets = computed(() => {
  const source = (showMyOnly.value && !isGuest.value) ? myPublishedDatasets.value : publicDatasets.value

  return source.filter(ds => {
    const matchSearch = !searchQuery.value ||
      ds.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (ds.description || '').toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      getTags(ds).some(t => t.toLowerCase().includes(searchQuery.value.toLowerCase()))
    const matchTags = selectedTags.value.length === 0 ||
      selectedTags.value.some(t => getTags(ds).includes(t))
    return matchSearch && matchTags
  })
})

const openDataset = (ds) => {
  router.push(isGuest.value ? `/dataset/${ds.id}` : `/app/dataset/${ds.id}`)
}

const scrollToContent = () => {
  contentRef.value?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  fetchPublicDatasets()
  fetchMyPublished()
})
</script>

<style scoped>
.datasets-page { min-height: 100%; }

/* Guest hero */
.guest-hero {
  background: linear-gradient(180deg, #f1f5f9 0%, var(--bg-primary) 100%);
  padding: 60px 24px 40px; text-align: center; margin: -24px -24px 0;
}
.dark .guest-hero { background: linear-gradient(180deg, #1e293b 0%, var(--bg-primary) 100%); }
.hero-inner { max-width: 600px; margin: 0 auto; }
.hero-brand { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.hero-brand h1 { font-size: 32px; font-weight: 800; color: var(--text-primary); letter-spacing: -0.5px; }
.hero-desc { color: var(--text-secondary); font-size: 15px; margin-bottom: 24px; }
.hero-actions { display: flex; gap: 12px; justify-content: center; }
.hero-btn {
  padding: 10px 24px; border-radius: 10px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.2s; border: none;
}
.hero-btn.primary { background: #1e293b; color: #fff; }
.hero-btn.primary:hover { background: #334155; }
.dark .hero-btn.primary { background: #5a9e9f; color: #0f172a; }
.hero-btn.ghost { background: transparent; color: var(--text-secondary); border: 1px solid var(--border-color); }
.hero-btn.ghost:hover { border-color: var(--accent-primary); color: var(--accent-primary); }

/* Content */
.datasets-content { max-width: 1200px; margin: 0 auto; }
.search-bar { margin-bottom: 24px; }
.search-input-wrapper { position: relative; margin-bottom: 16px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-tertiary); }
.search-input-wrapper input {
  width: 100%; padding: 12px 16px 12px 42px;
  border: 1px solid var(--border-color); border-radius: 12px;
  font-size: 14px; background: var(--bg-secondary); color: var(--text-primary);
  transition: all 0.2s;
}
.search-input-wrapper input:focus { outline: none; border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(58,125,126,0.1); }
.search-input-wrapper input::placeholder { color: var(--text-tertiary); }
.filter-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.filter-tag {
  padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border-color);
  background: var(--bg-secondary); color: var(--text-secondary);
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.filter-tag:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
.filter-tag.active { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }
.filter-tag.my-tag { display: flex; align-items: center; gap: 4px; border-color: var(--accent-primary); color: var(--accent-primary); font-weight: 600; }
.filter-tag.my-tag.active { background: var(--accent-primary); color: #fff; }

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
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;
}

/* Card */
.dataset-card {
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  border-radius: 14px; overflow: hidden; cursor: pointer; transition: all 0.2s;
  display: flex; flex-direction: column;
}
.dataset-card:hover { border-color: var(--accent-primary); box-shadow: var(--shadow-md); transform: translateY(-2px); }

.card-banner {
  background: linear-gradient(135deg, var(--accent-light) 0%, rgba(58,125,126,0.05) 100%);
  padding: 14px 18px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}
.dark .card-banner { background: linear-gradient(135deg, rgba(58,125,126,0.1) 0%, rgba(58,125,126,0.04) 100%); }
.banner-icon {
  width: 42px; height: 42px; border-radius: 10px;
  background: var(--bg-secondary); border: 1px solid var(--border-color);
  color: var(--accent-primary); display: flex; align-items: center; justify-content: center;
}
.banner-meta { display: flex; flex-direction: column; gap: 5px; align-items: flex-end; }
.card-owner, .card-count {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--text-secondary); font-weight: 500;
}
.banner-meta { display: flex; flex-direction: column; gap: 5px; align-items: flex-end; }
.pin-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid var(--border-color); background: var(--bg-secondary);
  color: var(--text-tertiary); cursor: pointer; transition: all 0.15s;
  padding: 0; margin-top: 2px;
}
.pin-btn:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
.pin-btn.pinned { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }

.card-body { padding: 16px 18px; flex: 1; display: flex; flex-direction: column; gap: 8px; }
.card-title {
  font-size: 15px; font-weight: 700; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; flex: 1; min-height: 2.6em;
}
.card-info-row { display: flex; gap: 16px; padding-top: 6px; border-top: 1px solid var(--border-color); }
.info-item {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--text-tertiary);
}
.card-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.card-tag {
  padding: 2px 8px; border-radius: 4px;
  background: var(--bg-tertiary); color: var(--text-secondary);
  font-size: 11px; font-weight: 500;
}

/* Empty state */
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-tertiary); }
.empty-state svg { margin-bottom: 16px; }
.empty-state p { font-size: 15px; }
</style>

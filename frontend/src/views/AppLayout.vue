<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="sidebar-brand" v-if="!sidebarCollapsed">
          <img src="/logos/gpt1trans.png" alt="AGI&FBHC DataSphere" width="32" height="32" />
          <div class="brand-name"><span class="brand-line1">AGI&FBHC</span><span class="brand-line2">DataSphere</span></div>
        </div>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
            <path v-if="!sidebarCollapsed" d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path v-else d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-item" :class="{ active: currentRoute === 'datasets' }" @click="$router.push('/app/datasets')">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="2"/><path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="2"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="2"/></svg>
          <span v-if="!sidebarCollapsed">数据集广场</span>
        </div>
        <div class="nav-item" :class="{ active: currentRoute === 'my-datasets' }" @click="$router.push('/app/my-datasets')">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span v-if="!sidebarCollapsed">我的数据集</span>
        </div>
        <div class="nav-item" :class="{ active: currentRoute === 'tasks' }" @click="$router.push('/app/tasks')">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="22" height="22"><ellipse cx="12" cy="14" rx="3.5" ry="4.5" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="8" r="2.5" stroke="currentColor" stroke-width="2"/><path d="M8.5 12L4 9M8.5 14L3 14M8.5 16L4 19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M15.5 12L20 9M15.5 14L21 14M15.5 16L20 19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span v-if="!sidebarCollapsed">XCrawler Agent</span>
        </div>
        <div class="nav-item" :class="{ active: currentRoute === 'edit-dataset' }" @click="$router.push('/app/edit-dataset')">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span v-if="!sidebarCollapsed">编辑数据集</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="nav-item" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="16 17 21 12 16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span v-if="!sidebarCollapsed">退出登录</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <div class="page-title"><h2>{{ pageTitle }}</h2></div>
        <div class="top-bar-right">
          <button class="theme-toggle-btn" @click="toggleTheme">
            <svg v-if="!isDark" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18"><circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="2"/><path d="M12 1V3M12 21V23M4.22 4.22L5.64 5.64M18.36 18.36L19.78 19.78M1 12H3M21 12H23M4.22 19.78L5.64 18.36M18.36 5.64L19.78 4.22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
          <div class="user-info">
            <div class="avatar">{{ avatarLetter }}</div>
            <span class="user-name">{{ userInfo?.nickname || userInfo?.email || '用户' }}</span>
          </div>
        </div>
      </header>
      <section class="content-area">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { removeToken } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const { isDark, toggleTheme } = useTheme()
const sidebarCollapsed = ref(false)
const userInfo = ref(null)

const avatarLetter = computed(() => {
  const name = userInfo.value?.nickname || userInfo.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})

const currentRoute = computed(() => {
  const path = route.path
  if (path.includes('my-datasets')) return 'my-datasets'
  if (path.includes('tasks')) return 'tasks'
  if (path.includes('edit-dataset')) return 'edit-dataset'
  return 'datasets'
})

const pageTitle = computed(() => {
  const titles = { 'datasets': '数据集广场', 'my-datasets': '我的数据集', 'tasks': 'XCrawler Agent', 'edit-dataset': '编辑数据集' }
  return titles[currentRoute.value] || '数据集'
})

onMounted(() => {
  const stored = localStorage.getItem('userInfo')
  if (stored) userInfo.value = JSON.parse(stored)
})

const handleLogout = () => {
  removeToken()
  router.push('/')
}
</script>

<style scoped>
.app-layout { display: flex; height: 100vh; overflow: hidden; }
.sidebar {
  width: 240px;
  background: var(--glass-bg);
  border-right: 1px solid var(--glass-border);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  box-shadow: var(--glass-shadow);
  display: flex; flex-direction: column; transition: width 0.3s ease; flex-shrink: 0;
}
.sidebar.collapsed { width: 64px; }
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between; padding: 16px;
  border-bottom: 1px solid var(--border-color); min-height: 64px;
}
.sidebar-brand { display: flex; align-items: center; gap: 10px; }
.brand-name {
  display: flex; flex-direction: column; gap: 0; line-height: 1.2;
}
.brand-line1 {
  font-size: 12px; font-weight: 500; color: var(--text-secondary); letter-spacing: 0.5px;
}
.brand-line2 {
  font-size: 17px; font-weight: 700; color: var(--text-primary); white-space: nowrap;
}
.collapse-btn {
  background: transparent; border: none; cursor: pointer; padding: 6px; border-radius: 6px;
  color: var(--text-secondary); transition: all 0.2s; display: flex; align-items: center; justify-content: center;
}
.collapse-btn:hover { background: var(--bg-hover); }
.sidebar-nav { flex: 1; padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px;
  cursor: pointer; color: var(--text-secondary); font-size: 14px; font-weight: 500;
  transition: all 0.15s; white-space: nowrap;
}
.nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-item.active { background: var(--accent-light); color: var(--accent-primary); }
.nav-item svg { flex-shrink: 0; }
.sidebar-footer { padding: 12px 8px; border-top: 1px solid var(--border-color); }
.sidebar-footer .nav-item { color: var(--text-tertiary); }
.sidebar-footer .nav-item:hover { color: var(--danger); background: rgba(220, 38, 38, 0.06); }
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.top-bar {
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
  background: var(--glass-bg);
  border-bottom: 1px solid var(--glass-border);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  box-shadow: var(--glass-shadow);
  height: 56px;
  flex-shrink: 0;
}
.page-title h2 { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.top-bar-right { display: flex; align-items: center; gap: 12px; }
.theme-toggle-btn {
  background: var(--bg-hover); border: none; cursor: pointer; padding: 8px; border-radius: 8px;
  transition: all 0.2s; display: flex; align-items: center; justify-content: center; color: var(--text-secondary);
}
.theme-toggle-btn:hover { background: var(--bg-tertiary); color: var(--accent-primary); }
.user-info { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 30px; height: 30px; border-radius: 50%; background: var(--accent-primary); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600;
}
.user-name { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.content-area { flex: 1; padding: 24px; overflow-y: auto; }
</style>

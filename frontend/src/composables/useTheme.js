import { ref, computed, watch, onMounted } from 'vue'

const THEME_KEY = 'ds-theme'
const LIGHT_THEME = 'light'
const DARK_THEME = 'dark'

const currentTheme = ref(localStorage.getItem(THEME_KEY) || LIGHT_THEME)

export function useTheme() {
  const isDark = computed(() => currentTheme.value === DARK_THEME)

  function setTheme(theme) {
    currentTheme.value = theme
    localStorage.setItem(THEME_KEY, theme)
    applyTheme(theme)
  }

  function toggleTheme() {
    const newTheme = isDark.value ? LIGHT_THEME : DARK_THEME
    setTheme(newTheme)
  }

  function applyTheme(theme) {
    const root = document.documentElement
    if (theme === DARK_THEME) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  onMounted(() => {
    applyTheme(currentTheme.value)
  })

  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme)
  })

  return {
    currentTheme,
    isDark,
    setTheme,
    toggleTheme
  }
}

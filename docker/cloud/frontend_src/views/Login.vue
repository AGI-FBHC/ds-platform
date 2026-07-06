<template>
  <div class="login-container">
    <!-- Theme toggle -->
    <div class="theme-toggle-container">
      <button class="theme-toggle-btn" @click="toggleTheme" :title="isDark ? '切换到亮色主题' : '切换到深色主题'">
        <svg v-if="!isDark" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="2"/>
          <path d="M12 1V3M12 21V23M4.22 4.22L5.64 5.64M18.36 18.36L19.78 19.78M1 12H3M21 12H23M4.22 19.78L5.64 18.36M18.36 5.64L19.78 4.22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Top-left brand -->
    <div class="header-logo-section">
      <div class="brand-icon">
        <img src="/logos/gpt1trans.png" alt="AGI&FBHC DataSphere" width="44" height="44" />
      </div>
      <div class="header-text">
        <h3 class="main-title">AGI&FBHC DataSphere</h3>
        <p class="sub-title">数据集管理平台</p>
      </div>
    </div>

    <!-- Login card -->
    <div class="login-card">
      <div class="flip-toggle-container">
        <button class="flip-toggle-btn" @click="isLogin = !isLogin">
          {{ isLogin ? '注册账号' : '返回登录' }}
        </button>
      </div>

      <!-- Logo area -->
      <div class="card-logo">
        <img src="/logos/gpt1trans.png" alt="AGI&FBHC DataSphere" width="48" height="48" />
        <h2 class="card-title">AGI&FBHC DataSphere</h2>
      </div>

      <!-- Login form -->
      <form v-if="isLogin" @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="loginForm.email" type="email" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <div class="password-input-container">
            <input v-model="loginForm.password" :type="showPassword ? 'text' : 'password'" placeholder="请输入密码" required />
            <button type="button" class="password-toggle-btn" @click="showPassword = !showPassword">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
                <path v-if="!showPassword" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle v-if="!showPassword" cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                <path v-if="showPassword" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line v-if="showPassword" x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '处理中...' : '登录' }}
        </button>
      </form>

      <!-- Register form -->
      <form v-else @submit.prevent="handleRegister" class="login-form">
        <div class="form-group">
          <label>昵称</label>
          <input v-model="registerForm.nickname" type="text" placeholder="请输入昵称" required />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="registerForm.email" type="email" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <div class="password-input-container">
            <input v-model="registerForm.password" :type="showRegPassword ? 'text' : 'password'" placeholder="请输入密码（至少6位）" required />
            <button type="button" class="password-toggle-btn" @click="showRegPassword = !showRegPassword">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
                <path v-if="!showRegPassword" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle v-if="!showRegPassword" cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                <path v-if="showRegPassword" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line v-if="showRegPassword" x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <div class="password-input-container">
            <input v-model="registerForm.confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" placeholder="请再次输入密码" required />
            <button type="button" class="password-toggle-btn" @click="showConfirmPassword = !showConfirmPassword">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
                <path v-if="!showConfirmPassword" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle v-if="!showConfirmPassword" cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                <path v-if="showConfirmPassword" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line v-if="showConfirmPassword" x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>邀请码</label>
          <input v-model="registerForm.inviteCode" type="text" placeholder="请输入邀请码" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '处理中...' : '注册' }}
        </button>
      </form>

      <!-- Guest entry -->
      <div class="guest-section">
        <div class="divider">
          <span>或</span>
        </div>
        <button class="guest-btn" @click="enterAsGuest">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
          </svg>
          游客进入，浏览数据集
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { ElMessage } from 'element-plus'
import { login, register, setToken, getCurrentUser } from '@/utils/api'

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

const isLogin = ref(true)
const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ nickname: '', email: '', password: '', confirmPassword: '', inviteCode: '' })
const showPassword = ref(false)
const showRegPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)

const enterAsGuest = () => {
  router.push('/datasets')
}

const handleLogin = async () => {
  try {
    loading.value = true
    const response = await login(loginForm.email, loginForm.password)
    setToken(response.access_token)
    const userInfo = await getCurrentUser()
    localStorage.setItem('userInfo', JSON.stringify(userInfo))
    ElMessage.success('登录成功')
    router.push('/app/datasets')
  } catch (error) {
    ElMessage.error(`登录失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  try {
    loading.value = true
    await register({
      email: registerForm.email,
      password: registerForm.password,
      nickname: registerForm.nickname,
      invite_code: registerForm.inviteCode,
    })
    ElMessage.success('注册成功，请登录')
    isLogin.value = true
  } catch (error) {
    ElMessage.error(`注册失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-image: url('/background/jnu.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
}

/* Top-left brand */
.header-logo-section {
  position: absolute;
  top: 24px;
  left: 28px;
  display: flex;
  align-items: center;
  gap: 14px;
  z-index: 100;
}

.brand-icon {
  display: flex;
  align-items: center;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.main-title {
  margin: 0;
  font-size: 22px;
  color: #1e293b;
  font-weight: 700;
  line-height: 1.2;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
}

.sub-title {
  margin: 0;
  font-size: 12px;
  color: #475569;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

/* Theme toggle */
.theme-toggle-container {
  position: absolute;
  top: 24px;
  right: 28px;
  z-index: 100;
}

.theme-toggle-btn {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.theme-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.45);
}

.dark .theme-toggle-btn {
  background: rgba(30, 41, 59, 0.4);
  border-color: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.theme-toggle-btn svg {
  width: 20px;
  height: 20px;
}

/* Login card - glassmorphism like XBots */
.login-card {
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 100%;
  max-width: 400px;
  position: relative;
}

.dark .login-card {
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.flip-toggle-container {
  position: absolute;
  top: 16px;
  right: 16px;
}

.flip-toggle-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.flip-toggle-btn:hover {
  background: rgba(58, 125, 126, 0.08);
  color: #3a7d7e;
}

/* Card logo */
.card-logo {
  text-align: center;
  margin-bottom: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.dark .card-title {
  color: #e2e8f0;
}

/* Forms */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  color: #475569;
  font-weight: 500;
  font-size: 13px;
}

.dark .form-group label {
  color: #94a3b8;
}

.form-group input {
  padding: 11px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.7);
  color: #1e293b;
}

.dark .form-group input {
  background: rgba(15, 23, 42, 0.5);
  border-color: #334155;
  color: #e2e8f0;
}

.form-group input:focus {
  outline: none;
  border-color: #3a7d7e;
  box-shadow: 0 0 0 3px rgba(58, 125, 126, 0.12);
}

.form-group input::placeholder {
  color: #94a3b8;
}

/* Password input */
.password-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-container input {
  flex: 1;
  padding-right: 40px;
}

.password-toggle-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.password-toggle-btn:hover {
  color: #3a7d7e;
}

/* Submit button */
.submit-btn {
  padding: 12px;
  background: var(--accent-primary);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 4px;
}

.submit-btn:hover {
  background: #334155;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(30, 41, 59, 0.25);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.dark .submit-btn {
  background: #5a9e9f;
  color: #0f172a;
}

.dark .submit-btn:hover {
  background: #3a7d7e;
  color: #ffffff;
}

/* Guest section */
.guest-section {
  margin-top: 20px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

.dark .divider::before,
.dark .divider::after {
  background: #334155;
}

.divider span {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

.guest-btn {
  width: 100%;
  padding: 11px;
  background: transparent;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.guest-btn:hover {
  background: rgba(58, 125, 126, 0.06);
  border-color: #3a7d7e;
  color: #3a7d7e;
}

.dark .guest-btn {
  color: #94a3b8;
  border-color: #334155;
}

.dark .guest-btn:hover {
  background: rgba(90, 158, 159, 0.1);
  border-color: #5a9e9f;
  color: #5a9e9f;
}
</style>

<script setup>
import { useTheme } from '@/composables/useTheme'

useTheme()
</script>

<template>
  <router-view />
</template>

<style>
:root {
  --bg-primary: #f8f9fb;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f1f3f5;
  --bg-hover: #f1f3f5;

  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-tertiary: #94a3b8;

  --border-color: #e2e8f0;
  --border-hover: #94a3b8;

  --accent-primary: #3a7d7e;
  --accent-secondary: #5a9e9f;
  --accent-light: #e8f4f4;
  --accent-gradient: none;

  --status-online-bg: #ecfdf5;
  --status-online-text: #059669;

  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);

  --success: #059669;
  --warning: #d97706;
  --danger: #dc2626;
}

.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #273449;
  --bg-hover: #273449;

  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;

  --border-color: #334155;
  --border-hover: #5a9e9f;

  --accent-primary: #5a9e9f;
  --accent-secondary: #3a7d7e;
  --accent-light: #1a3a3a;
  --accent-gradient: none;

  --status-online-bg: #064e3b;
  --status-online-text: #34d399;

  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.35);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4);

  --success: #34d399;
  --warning: #fbbf24;
  --danger: #f87171;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  height: 100vh;
}

/* Decorative gradient background - adapts to theme */
body::before {
  content: '';
  position: fixed;
  inset: -10%;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(ellipse 80% 65% at 90% 100%, rgba(58, 125, 126, 0.30) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 10% 80%,  rgba(90, 158, 159, 0.20) 0%, transparent 55%),
    radial-gradient(ellipse 40% 40% at 55% 110%, rgba(58, 125, 126, 0.14) 0%, transparent 50%),
    radial-gradient(ellipse 30% 25% at 70% 90%,  rgba(80, 140, 140, 0.10) 0%, transparent 45%);
  animation: blob-float 20s ease-in-out infinite;
  transition: opacity 0.4s ease;
}

@keyframes blob-float {
  0%   { transform: translate(0, 0) scale(1); }
  25%  { transform: translate(-30px, -20px) scale(1.05); }
  50%  { transform: translate(20px, -40px) scale(0.97); }
  75%  { transform: translate(40px, -15px) scale(1.03); }
  100% { transform: translate(0, 0) scale(1); }
}

:root {
  --glass-bg: rgba(255, 255, 255, 0.80);
  --glass-border: rgba(255, 255, 255, 0.55);
  --glass-shadow: 0 8px 32px rgba(58, 125, 126, 0.10), 0 2px 8px rgba(58, 125, 126, 0.06);
}

.dark body::before {
  background:
    radial-gradient(ellipse 70% 55% at 85% 105%, rgba(58, 125, 126, 0.28) 0%, transparent 65%),
    radial-gradient(ellipse 50% 40% at 15% 85%,  rgba(58, 125, 126, 0.16) 0%, transparent 60%),
    radial-gradient(ellipse 45% 35% at 50% 115%, rgba(90, 158, 159, 0.12) 0%, transparent 55%);
  animation: blob-float 20s ease-in-out infinite;
}

.dark {
  --glass-bg: rgba(15, 23, 42, 0.78);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* Element Plus theme overrides */
:root {
  --el-color-primary: #3a7d7e;
  --el-color-primary-light-3: #5a9e9f;
  --el-color-primary-light-5: #8abfbf;
  --el-color-primary-light-7: #b5dada;
  --el-color-primary-light-8: #d1ecec;
  --el-color-primary-light-9: #e8f4f4;
  --el-color-primary-dark-2: #2d6363;
}

.dark {
  --el-color-primary: #5a9e9f;
  --el-color-primary-light-3: #7ababa;
  --el-color-primary-light-5: #9acdcd;
  --el-color-primary-dark-2: #3a7d7e;
  --el-bg-color: #1e293b;
  --el-bg-color-page: #0f172a;
  --el-bg-color-overlay: #1e293b;
  --el-text-color-primary: #e2e8f0;
  --el-text-color-regular: #94a3b8;
  --el-border-color: #334155;
  --el-fill-color-blank: #1e293b;
}

/* Element Plus dark-mode hard overrides — CSS vars alone don't always reach
   the teleported popper; force explicit colors so dropdowns / dialogs / etc.
   don't render as white panels. */
.dark .el-select__popper,
.dark .el-select-dropdown,
.dark .el-popper.is-light,
.dark .el-popper {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45) !important;
}
.dark .el-select__popper .el-popper__arrow::before,
.dark .el-select-dropdown__popper .el-popper__arrow::before {
  background: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
}

.dark .el-select-dropdown__item {
  color: var(--text-primary) !important;
}
.dark .el-select-dropdown__item:hover,
.dark .el-select-dropdown__item.is-hovering {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}
.dark .el-select-dropdown__item.is-selected {
  color: var(--accent-primary) !important;
  font-weight: 600;
}
.dark .el-select-dropdown__item.is-selected.is-hovering {
  color: #fff !important;
  background: var(--accent-primary) !important;
}

.dark .el-select__wrapper {
  background: var(--bg-secondary) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
  color: var(--text-primary) !important;
}
.dark .el-select__wrapper.is-hovering:not(.is-focused) {
  box-shadow: 0 0 0 1px var(--accent-primary) inset !important;
}
.dark .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px var(--accent-primary) inset, 0 0 0 3px rgba(90, 158, 159, 0.20) !important;
}
.dark .el-select__placeholder {
  color: var(--text-tertiary) !important;
}
.dark .el-select__caret {
  color: var(--text-tertiary) !important;
}

.dark .el-input__wrapper {
  background: var(--bg-secondary) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}
.dark .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--accent-primary) inset, 0 0 0 3px rgba(90, 158, 159, 0.20) !important;
}
.dark .el-input__inner {
  color: var(--text-primary) !important;
}
.dark .el-input__inner::placeholder {
  color: var(--text-tertiary) !important;
}

.dark .el-dialog {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}
.dark .el-dialog__title {
  color: var(--text-primary) !important;
}
.dark .el-dialog__body {
  color: var(--text-primary) !important;
}
.dark .el-dialog__header {
  border-bottom: 1px solid var(--border-color);
}
.dark .el-dialog__footer {
  border-top: 1px solid var(--border-color);
}

.dark .el-message-box {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}
.dark .el-message-box__title,
.dark .el-message-box__content,
.dark .el-message-box__message,
.dark .el-message-box__message p {
  color: var(--text-primary) !important;
}

.dark .el-button {
  --el-button-bg-color: var(--bg-secondary);
  --el-button-text-color: var(--text-primary);
  --el-button-border-color: var(--border-color);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-text-color: var(--accent-primary);
  --el-button-hover-border-color: var(--accent-primary);
}
.dark .el-button--primary {
  --el-button-bg-color: var(--accent-primary);
  --el-button-text-color: #fff;
  --el-button-border-color: var(--accent-primary);
  --el-button-hover-bg-color: var(--accent-secondary);
  --el-button-hover-border-color: var(--accent-secondary);
  --el-button-hover-text-color: #fff;
}
.dark .el-button.is-disabled {
  opacity: 0.55;
}

.dark .el-message,
.dark .el-notification {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
}
.dark .el-message__content {
  color: var(--text-primary) !important;
}

.dark .el-tag {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.dark .el-empty__description p {
  color: var(--text-tertiary) !important;
}

.dark .el-tooltip__popper,
.dark .el-popper.is-dark {
  background: #1e293b !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color) !important;
}

.dark .el-overlay {
  background-color: rgba(0, 0, 0, 0.6) !important;
}

/* Custom scrollbars — thin teal-tinted, consistent across light and dark themes */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(58, 125, 126, 0.35);
  border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(58, 125, 126, 0.60); }
::-webkit-scrollbar-corner { background: transparent; }

/* Firefox */
* { scrollbar-width: thin; scrollbar-color: rgba(58, 125, 126, 0.35) transparent; }

/* Global button utilities — works across all components (Tasks.vue had
   unscoped .ghost-btn / .primary-btn references that broke). */
.app-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px;
  font-size: 13px; font-weight: 500;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-primary);
  font-family: inherit; line-height: 1.2;
  cursor: pointer; user-select: none; white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.app-btn:disabled,
.app-btn.is-disabled {
  opacity: 0.5; cursor: not-allowed; pointer-events: none;
}

.app-btn.primary {
  background: var(--accent-primary); color: #fff;
  border-color: var(--accent-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.app-btn.primary:hover:not(:disabled) {
  background: var(--accent-secondary); border-color: var(--accent-secondary);
  box-shadow: 0 4px 12px rgba(58, 125, 126, 0.22);
}

.app-btn.ghost {
  background: var(--bg-secondary); color: var(--text-secondary);
  border-color: var(--border-color);
}
.app-btn.ghost:hover:not(:disabled) {
  color: var(--accent-primary); border-color: var(--accent-primary);
  background: var(--bg-secondary);
}

.app-btn.outline {
  background: transparent; color: var(--accent-primary);
  border-color: var(--accent-primary);
}
.app-btn.outline:hover:not(:disabled) {
  background: var(--accent-light);
}

.app-btn.danger {
  background: var(--bg-secondary); color: var(--danger);
  border-color: rgba(239, 68, 68, 0.4);
}
.app-btn.danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.08); border-color: var(--danger);
}
.app-btn.danger.solid {
  background: var(--danger); color: #fff; border-color: var(--danger);
}
.app-btn.danger.solid:hover:not(:disabled) {
  background: #b91c1c; border-color: #b91c1c;
}

.app-btn.warn {
  background: rgba(245, 158, 11, 0.10); color: #b45309;
  border-color: rgba(245, 158, 11, 0.35);
}
.app-btn.warn:hover:not(:disabled) {
  background: #f59e0b; color: #fff; border-color: #f59e0b;
}

.app-btn.small  { padding: 5px 10px; font-size: 12px;   border-radius: 6px; }
.app-btn.large  { padding: 12px 22px; font-size: 14px;  border-radius: 10px; }
.app-btn.icon   { padding: 6px; width: 30px; height: 30px; border-radius: 8px; }
.app-btn.icon-sm { padding: 4px; width: 26px; height: 26px; border-radius: 6px; }
</style>

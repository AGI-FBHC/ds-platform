<template>
  <div v-if="visible" class="mask-editor-overlay">
    <div class="mask-editor-dialog" @click.stop>
      <div class="mask-editor-header">
        <h3>Mask 编辑器</h3>
        <button class="close-btn" @click="close">×</button>
      </div>
      <div class="mask-editor-toolbar">
        <div class="tool-group">
          <span class="tool-label">画笔颜色</span>
          <button
            class="color-btn black-btn"
            :class="{ active: brushColor === 'black' }"
            @click="setBrushColor('black')"
            title="黑色（绘制 Mask）"
          ></button>
          <button
            class="color-btn white-btn"
            :class="{ active: brushColor === 'white' }"
            @click="setBrushColor('white')"
            title="白色（擦除 Mask）"
          ></button>
        </div>
        <div class="tool-group">
          <span class="tool-label">画笔大小</span>
          <div class="brush-slider-wrap">
            <input type="range" min="10" max="200" v-model.number="brushSize" class="brush-slider" />
            <span class="brush-size-value">{{ brushSize }}px</span>
          </div>
        </div>
        <button class="tool-btn" @click="clearCanvas">清空</button>
      </div>
      <div class="mask-editor-workspace">
        <div class="canvas-panel">
          <div class="panel-label">预览（原图 + Mask）</div>
          <div class="canvas-container">
            <canvas
              ref="previewCanvasRef"
              class="editor-canvas preview-canvas"
              :style="{ cursor: currentCursor }"
              @mousedown="startDrawingOnPreview"
              @mousemove="drawOnPreview"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
            ></canvas>
          </div>
        </div>
        <div class="canvas-panel">
          <div class="panel-label">编辑（绘制 Mask）</div>
          <div class="canvas-container">
            <canvas
              ref="canvasRef"
              class="editor-canvas edit-canvas"
              :style="{ cursor: currentCursor }"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
            ></canvas>
          </div>
        </div>
      </div>
      <div class="mask-editor-footer">
        <button class="ghost-btn" @click="close">取消</button>
        <button class="primary-btn" @click="saveMask" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { API_BASE_URL, getToken } from '@/utils/api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  imageUrl: { type: String, default: '' },
  maskUrl: { type: String, default: '' },
  datasetId: { type: String, default: '' },
  imageId: { type: String, default: '' }
})

const emit = defineEmits(['close', 'saved'])

const canvasRef = ref(null)
const previewCanvasRef = ref(null)
const ctx = ref(null)
const previewCtx = ref(null)
const brushColor = ref('black')
const brushSize = ref(30)
const isDrawing = ref(false)
const saving = ref(false)
const lastX = ref(0)
const lastY = ref(0)

let originalImage = null

const loadImage = (url) => new Promise((resolve, reject) => {
  const img = new Image()
  img.crossOrigin = "anonymous"
  img.onload = () => resolve(img)
  img.onerror = reject
  img.src = url
})


const setBrushColor = (color) => { brushColor.value = color }
// 生成圆形光标 (原文: 光标圆 size/3.35, 128 为界限)
const generateCircleCursor = (size, color) => {
  const maxCursorSize = 128
  const cursorSize = Math.min(Math.max(size + 4, 16), maxCursorSize)
  const offscreen = document.createElement("canvas")
  offscreen.width = cursorSize
  offscreen.height = cursorSize
  const context = offscreen.getContext("2d")
  if (!context) return "crosshair"
  const centerX = cursorSize / 2
  const centerY = cursorSize / 2
  // 光标圆 size/3.35 (略小于实际笔触, 作为视觉指示)
  const radius = Math.min(size / 5, (cursorSize - 4) / 2)
  context.beginPath()
  context.arc(centerX, centerY, radius, 0, Math.PI * 2)
  context.strokeStyle = color === "black" ? "#ffffff" : "#000000"
  context.lineWidth = 2
  context.stroke()
  context.beginPath()
  context.arc(centerX, centerY, radius, 0, Math.PI * 2)
  context.fillStyle = color === "black" ? "rgba(0, 0, 0, 0.3)" : "rgba(255, 255, 255, 0.3)"
  context.fill()
  return `url(${offscreen.toDataURL()}) ${centerX} ${centerY}, crosshair`
}

// 参考实现: brushSize 直接传, cursor 圆 size/3.35 略小 (作为视觉指示)
const currentCursor = computed(() => {
  return generateCircleCursor(brushSize.value, brushColor.value)
})


// 初始化 mask 编辑画布：白底 + 已有 mask
const initCanvas = async (img) => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = img.width
  canvas.height = img.height
  const context = canvas.getContext('2d')
  if (!context) return
  ctx.value = context
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  if (props.maskUrl) {
    try {
      const maskImg = await loadImage(props.maskUrl)
      context.drawImage(maskImg, 0, 0, canvas.width, canvas.height)
    } catch (e) {
      console.warn('Failed to load existing mask:', e)
    }
  }
}

// 初始化预览画布：原图 + 80% 透明度的 mask 编辑画布
const initPreviewCanvas = (img) => {
  const canvas = previewCanvasRef.value
  if (!canvas) return
  canvas.width = img.width
  canvas.height = img.height
  const context = canvas.getContext('2d')
  if (!context) return
  previewCtx.value = context
  originalImage = img
  updatePreviewCanvas()
}

const updatePreviewCanvas = () => {
  if (!previewCtx.value || !canvasRef.value || !originalImage) return
  const previewContext = previewCtx.value
  const editCanvas = canvasRef.value
  previewContext.drawImage(originalImage, 0, 0, editCanvas.width, editCanvas.height)
  previewContext.globalAlpha = 0.8
  previewContext.drawImage(editCanvas, 0, 0)
  previewContext.globalAlpha = 1.0
}

watch(() => props.visible, async (val) => {
  if (val && props.imageUrl) {
    await nextTick()
    setTimeout(async () => {
      try {
        const img = await loadImage(props.imageUrl)
        await initCanvas(img)
        initPreviewCanvas(img)
      } catch (err) {
        console.error('Failed to load image:', err)
        ElMessage.error('加载原图失败')
      }
    }, 50)
  }
})

const getCanvasCoordinates = (event) => {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) * (canvas.width / rect.width),
    y: (event.clientY - rect.top) * (canvas.height / rect.height)
  }
}

const getPreviewCanvasCoordinates = (event) => {
  const canvas = previewCanvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) * (canvas.width / rect.width),
    y: (event.clientY - rect.top) * (canvas.height / rect.height)
  }
}

const startDrawing = (event) => {
  isDrawing.value = true
  const coords = getCanvasCoordinates(event)
  lastX.value = coords.x
  lastY.value = coords.y
  if (ctx.value) {
    const radius = brushSize.value / 2
    ctx.value.beginPath()
    ctx.value.arc(coords.x, coords.y, radius, 0, Math.PI * 2)
    ctx.value.fillStyle = brushColor.value === 'black' ? '#000000' : '#ffffff'
    ctx.value.fill()
    updatePreviewCanvas()
  }
}

const draw = (event) => {
  if (!isDrawing.value || !ctx.value) return
  const coords = getCanvasCoordinates(event)
  const context = ctx.value
  const radius = brushSize.value / 2
  const distance = Math.sqrt(Math.pow(coords.x - lastX.value, 2) + Math.pow(coords.y - lastY.value, 2))
  if (distance < 1) return
  const steps = Math.ceil(distance / (radius * 0.5))
  const stepX = (coords.x - lastX.value) / steps
  const stepY = (coords.y - lastY.value) / steps
  const fill = brushColor.value === 'black' ? '#000000' : '#ffffff'
  for (let i = 0; i <= steps; i++) {
    const x = lastX.value + stepX * i
    const y = lastY.value + stepY * i
    context.beginPath()
    context.arc(x, y, radius, 0, Math.PI * 2)
    context.fillStyle = fill
    context.fill()
  }
  updatePreviewCanvas()
  lastX.value = coords.x
  lastY.value = coords.y
}

const startDrawingOnPreview = (event) => {
  isDrawing.value = true
  const coords = getPreviewCanvasCoordinates(event)
  lastX.value = coords.x
  lastY.value = coords.y
  if (ctx.value) {
    const radius = brushSize.value / 2
    ctx.value.beginPath()
    ctx.value.arc(coords.x, coords.y, radius, 0, Math.PI * 2)
    ctx.value.fillStyle = brushColor.value === 'black' ? '#000000' : '#ffffff'
    ctx.value.fill()
    updatePreviewCanvas()
  }
}

const drawOnPreview = (event) => {
  if (!isDrawing.value || !ctx.value) return
  const coords = getPreviewCanvasCoordinates(event)
  const context = ctx.value
  const radius = brushSize.value / 2
  const distance = Math.sqrt(Math.pow(coords.x - lastX.value, 2) + Math.pow(coords.y - lastY.value, 2))
  if (distance < 1) return
  const steps = Math.ceil(distance / (radius * 0.5))
  const stepX = (coords.x - lastX.value) / steps
  const stepY = (coords.y - lastY.value) / steps
  const fill = brushColor.value === 'black' ? '#000000' : '#ffffff'
  for (let i = 0; i <= steps; i++) {
    const x = lastX.value + stepX * i
    const y = lastY.value + stepY * i
    context.beginPath()
    context.arc(x, y, radius, 0, Math.PI * 2)
    context.fillStyle = fill
    context.fill()
  }
  updatePreviewCanvas()
  lastX.value = coords.x
  lastY.value = coords.y
}

const stopDrawing = () => { isDrawing.value = false }

const clearCanvas = () => {
  if (!ctx.value || !canvasRef.value) return
  const canvas = canvasRef.value
  ctx.value.fillStyle = '#ffffff'
  ctx.value.fillRect(0, 0, canvas.width, canvas.height)
  updatePreviewCanvas()
}

// Overlay click is intentionally a no-op — only the × button closes the editor.

const close = () => {
  ctx.value = null
  previewCtx.value = null
  originalImage = null
  isDrawing.value = false
  emit('close')
}

const saveMask = async () => {
  if (!canvasRef.value || !props.datasetId || !props.imageId) return
  saving.value = true
  try {
    const canvas = canvasRef.value
    const blob = await new Promise((resolve) => { canvas.toBlob((b) => resolve(b), 'image/png') })
    if (!blob) throw new Error('Canvas to blob failed')
    const formData = new FormData()
    formData.append('file', new File([blob], 'mask.png', { type: 'image/png' }))
    const token = getToken()
    const response = await fetch(
      API_BASE_URL + '/datasets/' + props.datasetId + '/images/' + props.imageId + '/mask',
      {
        method: 'POST',
        body: formData,
        headers: token ? { 'Authorization': 'Bearer ' + token } : {}
      }
    )
    if (!response.ok) throw new Error('Upload failed: ' + response.statusText)
    const result = await response.json()
    ElMessage.success('Mask 保存成功')
    emit('saved', result)
    close()
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.message || err))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.mask-editor-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 2100; animation: fadeIn 0.2s ease; }
.mask-editor-dialog { background: var(--bg-secondary); border-radius: 12px; box-shadow: var(--shadow-lg); width: 90vw; max-width: 1200px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; animation: slideUp 0.3s ease; }
.mask-editor-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.mask-editor-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: var(--text-primary); }
.close-btn { width: 32px; height: 32px; border: none; border-radius: 8px; background: var(--bg-tertiary); color: var(--text-secondary); font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s ease; }
.close-btn:hover { background: rgba(239,68,68,0.1); color: #ef4444; }
.mask-editor-toolbar { display: flex; align-items: center; gap: 20px; padding: 12px 20px; border-bottom: 1px solid var(--border-color); background: rgba(58,125,126,0.05); }
.tool-group { display: flex; align-items: center; gap: 8px; }
.tool-label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.color-btn { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--border-color); cursor: pointer; transition: all 0.15s ease; }
.color-btn:hover { transform: scale(1.1); }
.color-btn.active { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(58,125,126,0.25); }
.black-btn { background: #000000; }
.white-btn { background: #ffffff; }
.brush-slider-wrap { display: flex; align-items: center; gap: 10px; }
.brush-slider { flex: 1; height: 4px; -webkit-appearance: none; appearance: none; background: var(--bg-tertiary); border-radius: 2px; outline: none; cursor: pointer; }
.brush-slider::-webkit-slider-runnable-track { height: 4px; border-radius: 2px; background: linear-gradient(to right, var(--accent-primary) 0%, var(--accent-primary) var(--pct, 50%), var(--bg-tertiary) var(--pct, 50%)); }
.brush-slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 18px; height: 18px; margin-top: -7px;
  background: var(--accent-primary); border-radius: 50%; cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.brush-slider::-webkit-slider-thumb:hover { transform: scale(1.15); box-shadow: 0 2px 8px rgba(58,125,126,0.35); }
.brush-slider::-moz-range-thumb { width: 18px; height: 18px; background: var(--accent-primary); border-radius: 50%; cursor: pointer; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.25); }
.brush-size-value { font-size: 12px; color: var(--text-secondary); min-width: 40px; }
.tool-btn { padding: 6px 14px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-secondary); font-size: 12px; cursor: pointer; transition: all 0.15s ease; }
.tool-btn:hover { background: rgba(239,68,68,0.08); color: #ef4444; border-color: rgba(239,68,68,0.25); }
.mask-editor-workspace { display: flex; flex: 1; gap: 16px; padding: 16px 20px; overflow: hidden; min-height: 400px; }
.canvas-panel { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.panel-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-align: center; }
.canvas-container { flex: 1; display: flex; justify-content: center; align-items: center; background: var(--bg-primary); border-radius: 8px; border: 2px dashed var(--border-color); overflow: hidden; padding: 12px; min-height: 0; }
.editor-canvas { max-width: 100%; max-height: 100%; object-fit: contain; box-shadow: var(--shadow-sm); border-radius: 4px; }
.edit-canvas { background: var(--bg-secondary); }
.mask-editor-footer { display: flex; justify-content: center; gap: 12px; padding: 16px 20px; border-top: 1px solid var(--border-color); }
.ghost-btn { padding: 8px 20px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-secondary); cursor: pointer; font-size: 13px; transition: all 0.15s ease; }
.ghost-btn:hover { border-color: #3a7d7e; color: #3a7d7e; }
.primary-btn { padding: 8px 20px; border: none; border-radius: 6px; background: #3a7d7e; color: white; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s ease; }
.primary-btn:hover { background: #2f6465; }
.primary-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>

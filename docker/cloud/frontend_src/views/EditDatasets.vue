<template>
  <div class="edit-ds-page">
    <div class="page-header">
      <div>
        <h2>编辑数据集</h2>
        <p class="page-desc">选择由 Crawler Agent 保存的数据集，筛选、修改、批量编辑样本信息</p>
      </div>
      <div class="header-actions">
        <button class="app-btn ghost" @click="loadDatasets" :disabled="loadingDatasets">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          刷新
        </button>
      </div>
    </div>

    <!-- Hint when datasets exist but none is selected -->
    <div v-if="datasets.length > 0 && !currentDataset && !loadingDatasets" class="ds-hint-card">
      <div class="ds-hint-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="40" height="40">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>
        </svg>
      </div>
      <div class="ds-hint-body">
        <h4>请选择一个数据集开始编辑</h4>
        <p>
          本页面展示的所有数据集均由 <strong>XCrawler Agent</strong> 在图片抓取任务完成时自动保存生成。
          请先到 XCrawler Agent 创建一个图片搜集任务，任务结束后数据集会自动出现在上方下拉框中。
        </p>
        <router-link to="/app/tasks" class="ds-hint-cta">→ 前往 XCrawler Agent 创建任务</router-link>
      </div>
    </div>

    <!-- Dataset picker -->
    <div class="ds-picker">
      <div class="ds-picker-label">选择数据集</div>
      <el-select
        v-if="datasets.length > 0"
        v-model="selectedDatasetId"
        placeholder="选择一个数据集"
        filterable
        class="ds-picker-select"
        @change="onDatasetChange"
      >
        <el-option
          v-for="ds in datasets"
          :key="ds.id"
          :label="ds.name"
          :value="ds.id"
        >
          <div class="ds-option">
            <span class="ds-option-name">{{ ds.name }}</span>
            <span class="ds-option-meta">{{ ds.image_count }} 张</span>
          </div>
        </el-option>
      </el-select>
      <div v-else class="ds-empty">
        <template v-if="loadingDatasets">加载中...</template>
        <template v-else>
          还没有可编辑的数据集，请先去
          <router-link to="/app/tasks">任务页</router-link>
          跑个任务并保存到数据库。
        </template>
      </div>
    </div>

    <template v-if="currentDataset">
      <!-- Dataset info bar -->
      <div class="ds-info-bar">
        <div class="ds-info-top">
          <div class="ds-info-main">
            <h3 class="ds-info-name">
              <span>{{ currentDataset.name }}</span>
              <button class="rename-btn" @click="openRenameDialog" :disabled="renaming" title="重命名">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
              </button>
            </h3>
          </div>
          <div class="ds-info-stats">
            <div class="stat">
              <span class="stat-value">{{ currentDataset.image_count }}</span>
              <span class="stat-label">样本</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ formatBytes(currentDataset.total_size) }}</span>
              <span class="stat-label">大小</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ currentDataset.format }}</span>
              <span class="stat-label">格式</span>
            </div>
          </div>
          <div class="ds-info-actions">
            <button class="app-btn danger solid" @click="openDeleteDialog" :disabled="deleting">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/>
                <path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>
              </svg>
              删除数据集
            </button>
          </div>
        </div>
        <p class="ds-info-desc">{{ currentDataset.description || '无描述' }}</p>
        <div class="ds-info-chips" v-if="axes.length > 0">
          <span class="axis-chip" v-for="ax in axes" :key="ax.axis_key">
            {{ ax.axis_name }}
            <em>{{ ax.values.length }}</em>
          </span>
          <span v-if="needMask" class="axis-chip mask">Mask 开启</span>
        </div>
      </div>


      <!-- List fullscreen wrapper -->
      <div class="list-fullscreen-wrap" :class="{ 'fullscreen-active': listFullscreen }">
        <!-- Filter bar -->
        <div class="filter-bar">
          <div class="filter-left">
            <div class="view-toggle">
              <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'" title="列表视图">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                  <line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
              <button :class="{ active: viewMode === 'grid' }" @click="viewMode = 'grid'" title="网格视图">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                  <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                  <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="filter-right">
            <button v-if="viewMode === 'list'" class="fullscreen-btn" @click="listFullscreen = !listFullscreen" :title="listFullscreen ? '退出全屏' : '全屏'">
              <img v-show="!listFullscreen" class="icon-light" src="/logos/全屏.png" width="22" height="22" alt="全屏" />
              <img v-show="!listFullscreen" class="icon-dark" src="/logos/全屏 (1).png" width="22" height="22" alt="全屏" />
              <img v-show="listFullscreen" class="icon-light" src="/logos/退出全屏.png" width="22" height="22" alt="退出全屏" />
              <img v-show="listFullscreen" class="icon-dark" src="/logos/退出全屏 (1).png" width="22" height="22" alt="退出全屏" />
            </button>
            <span class="result-count">{{ filteredCount }} 条结果</span>
          </div>
        </div>

        <!-- Selection bar -->
        <div class="select-bar">
          <label class="select-all">
            <input type="checkbox" :checked="allOnPageSelected" @change="toggleSelectAllOnPage" />
            当前页全选
          </label>
          <span v-if="selectedIds.size > 0" class="selected-pill">已选 {{ selectedIds.size }} 项</span>
          <button v-if="selectedIds.size > 0" class="app-btn ghost small" @click="clearSelection">清除选择</button>
        </div>

        <!-- Image content -->
        <div v-if="loadingImages" class="grid-loading">加载样本中...</div>
        <div v-else-if="images.length === 0" class="grid-empty">没有符合条件的样本</div>
        <div v-else-if="viewMode === 'grid'" class="image-grid">
          <div v-for="img in images" :key="img.id" class="image-card" :class="{ selected: selectedIds.has(img.id) }">
            <label class="image-check" @click.stop>
              <input type="checkbox" :checked="selectedIds.has(img.id)" @change="toggleImage(img.id)" />
            </label>
            <div class="image-thumb" @click="openDetail(img)">
              <img :src="datasetImageUrl(currentDataset.id, img.relative_path)" :alt="img.filename" loading="lazy" @error="onImgError($event)" />
              <span v-if="img.mask_status === 'completed'" class="mask-badge" title="已生成 mask">M</span>
              <span v-else-if="img.mask_status === 'failed'" class="mask-badge failed" title="mask 生成失败">!</span>
            </div>
            <div class="image-meta">
              <div class="image-name" :title="img.filename">{{ img.filename }}</div>
              <div class="image-keyword" v-if="img.keyword">#{{ img.keyword }}</div>
              <div class="image-labels">
                <span v-for="(v, k) in (img.labels || {})" :key="k" class="label-chip">{{ k }}={{ v }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="image-list-wrap">
          <div class="image-list">
            <div class="list-header" :style="gridStyle">
              <div class="col col-check"></div>
              <div class="col col-thumb">缩略图</div>
              <div class="col col-name">
                文件名
                <button class="col-filter-btn" @click="openColFilter('filename')" :class="{ active: colFilters.filename }" title="筛选">
                  <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                </button>
              </div>
              <div v-if="needMask" class="col col-mask">Mask</div>
              <div class="col col-axis" v-for="ax in axes" :key="ax.axis_key">
                {{ ax.axis_name }}
                <button class="col-filter-btn" @click="openColFilter(ax.axis_key)" :class="{ active: colFilters[ax.axis_key] }" title="筛选">
                  <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                </button>
              </div>
              <div class="col col-actions">操作</div>
            </div>
            <div v-for="img in filteredImages" :key="img.id" class="list-row" :class="{ selected: selectedIds.has(img.id), saving: savingIds.has(img.id) }" :style="gridStyle">
              <div class="col col-check">
                <input type="checkbox" :checked="selectedIds.has(img.id)" @change="toggleImage(img.id)" />
              </div>
              <div class="col col-thumb">
                <img :src="datasetImageUrl(currentDataset.id, img.relative_path)" :alt="img.filename" loading="lazy" @error="onImgError($event)" @click="openDetail(img)" />
              </div>
              <div class="col col-name" :title="img.filename" @click="openDetail(img)">{{ img.filename }}</div>
              <div v-if="needMask" class="col col-mask">
                <img v-if="img.mask_relative_path" :src="datasetImageUrl(currentDataset.id, img.mask_relative_path, true)" :alt="img.filename + '.mask'" class="mask-thumb" @error="onImgError($event)" @click="openMaskEditor(img)" />
                <span v-else class="mask-empty" @click="openMaskEditor(img)" style="cursor: pointer;">--</span>
              </div>
              <div class="col col-axis" v-for="ax in axes" :key="ax.axis_key">
                <div class="cell-ax-wrap">
                  <input
                    class="cell-ax-input"
                    :value="(img.labels || {})[ax.axis_key] || ''"
                    placeholder="-- 未标注 --"
                    @focus="onAxFocus(img, ax)"
                    @input="onAxInput(img, ax, $event.target.value)"
                    @change="updateLabel(img, ax.axis_key, $event.target.value)"
                  />
                  <button class="ax-arrow" @click.stop="toggleAxPanel(img, ax)" :class="{ open: activeAxImgId === img.id && activeAxKey === ax.axis_key }">
                    <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
                  </button>
                  <div class="cell-ax-dropdown" v-if="activeAxImgId === img.id && activeAxKey === ax.axis_key">
                    <div
                      v-for="v in filteredAxValues"
                      :key="v.value_key"
                      class="ax-option"
                      :class="{ active: v.value_name === (img.labels || {})[ax.axis_key] }"
                      @mousedown.prevent="selectAxOption(img, ax, v.value_name)"
                    >{{ v.value_name }}</div>
                    <div class="ax-option ax-option-empty" v-if="filteredAxValues.length === 0">无匹配</div>
                  </div>
                </div>
              </div>
              <div class="col col-actions">
                <span v-if="recentlySavedIds.has(img.id)" class="saved-pulse">已保存</span>
                <button class="icon-btn" @click="openDetail(img)" title="详情">详情</button>
                <button class="icon-btn danger" @click="quickDelete(img)" title="删除">删除</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination + Bulk bar -->
        <div class="pagination-bulk-row">
          <!-- Bulk bar -->
          <transition name="bulk-fade">
            <div v-if="selectedIds.size > 0" class="bulk-bar">
              <span class="bulk-count">已选 <b>{{ selectedIds.size }}</b> 项</span>
              <button class="bulk-btn" @click="openBulkLabelDialog" :disabled="axes.length === 0">批量改分类</button>
              <button class="bulk-btn danger" @click="bulkDelete">删除</button>
            </div>
          </transition>
          <!-- Pagination -->
          <div v-if="totalPages > 1" class="pagination">
            <button class="page-btn" :disabled="page <= 1" @click="reloadImages(page - 1)">上一页</button>
            <span class="page-info">{{ page }} / {{ totalPages }}</span>
            <button class="page-btn" :disabled="page >= totalPages" @click="reloadImages(page + 1)">下一页</button>
          </div>
        </div>
      </div><!-- end list-fullscreen-wrap -->

      <!-- Column filter dialog -->
      <el-dialog v-model="colFilterVisible" :title="'筛选 ' + colFilterLabel" width="380" align-center destroy-on-close class="col-filter-dialog">
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

    </template>

    <!-- Image detail dialog -->
    <el-dialog
      v-model="detailVisible"
      width="780"
      align-center
      destroy-on-close
      class="image-detail-dialog"
      :title="detailImage ? `${detailImage.filename}  (${detailIndex + 1} / ${images.length})` : '样本详情'"
    >
      <div v-if="detailImage" class="detail-content">
        <div class="detail-preview">
          <button class="preview-nav prev" :disabled="!hasPrev" @click="gotoPrev" title="上一个">‹</button>
          <img
            :src="datasetImageUrl(currentDataset.id, detailImage.relative_path)"
            :alt="detailImage.filename"
          />
          <button class="preview-nav next" :disabled="!hasNext" @click="gotoNext" title="下一个">›</button>
          <div
            class="mask-preview"
            :class="{ empty: !detailImage.mask_relative_path }"
            @click="openMaskEditor(detailImage)"
            :title="detailImage.mask_relative_path ? '点击打开 Mask 编辑器' : '点击生成 Mask'"
          >
            <img
              v-if="detailImage.mask_relative_path"
              :src="datasetImageUrl(currentDataset.id, detailImage.mask_relative_path)"
              :alt="detailImage.filename + '.mask'"
              @error="onImgError($event)"
              @click.stop
            />
            <div v-else class="mask-empty-detail">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="28" height="28">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              <span>点击生成/编辑 Mask</span>
            </div>
            <span v-if="detailImage.mask_relative_path" class="mask-preview-label">Mask · 点击编辑</span>
          </div>
        </div>
        <div class="detail-fields">
          <div class="field">
            <label>关键词</label>
            <input v-model="editForm.keyword" />
          </div>
          <div class="field" v-for="ax in axes" :key="ax.axis_key">
            <label>{{ ax.axis_name }}</label>
            <input v-model="editForm.labels[ax.axis_key]" />
          </div>
          <div class="field">
            <label>Mask 状态</label>
            <select v-model="editForm.mask_status">
              <option value="not_requested">未生成</option>
              <option value="pending">生成中</option>
              <option value="completed">已完成</option>
              <option value="failed">生成失败</option>
            </select>
          </div>
          <div class="field">
            <label>来源页标题</label>
            <input v-model="editForm.source_page_title" />
          </div>
          <div class="field readonly">
            <label>尺寸</label>
            <span>{{ detailImage.width }} × {{ detailImage.height }}</span>
          </div>
          <div class="field readonly">
            <label>URL</label>
            <span class="readonly-text">{{ detailImage.url }}</span>
          </div>
          <div class="field readonly" v-if="detailImage.extra && detailImage.extra.caption">
            <label>描述</label>
            <textarea class="caption-text" readonly :value="detailImage.extra.caption" rows="6"></textarea>
          </div>
          <div class="field readonly">
            <label>标签 JSON</label>
            <a class="readonly-text json-link" :href="sampleJsonUrl(detailImage)" target="_blank" download>▼ 下载 {{ detailImage.filename.replace('.jpg', '.json') }}</a>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="detail-footer">
          <button class="app-btn ghost" @click="detailVisible = false">取消</button>
          <button class="app-btn primary" @click="exportDatasetJson" title="下载整个 dataset.json">▼ 全部 JSON</button>
          <button class="app-btn danger solid" @click="deleteOne(detailImage.id)" :disabled="detailSaving">删除</button>
          <button class="app-btn primary" @click="saveDetail" :disabled="detailSaving">{{ detailSaving ? '保存中...' : '保存' }}</button>
        </div>
      </template>
    </el-dialog>

    <!-- Bulk label edit dialog -->
    <el-dialog v-model="bulkDialogVisible" title="批量修改分类" width="480" align-center destroy-on-close class="bulk-dialog">
      <div class="bulk-form">
        <div class="field" v-for="ax in axes" :key="ax.axis_key">
          <label>{{ ax.axis_name }}</label>
          <select v-model="bulkForm.labels[ax.axis_key]">
            <option value="">-- 不修改 --</option>
            <option v-for="v in ax.values" :key="v.value_key" :value="v.value_key">{{ v.value_name }}</option>
          </select>
        </div>
        <p class="bulk-tip">选择 "不修改" 则跳过该轴。只替换选中样本的分类字段。</p>
      </div>
      <template #footer>
        <button class="app-btn ghost" @click="bulkDialogVisible = false">取消</button>
        <button class="app-btn primary" @click="applyBulkLabel" :disabled="bulkApplying">{{ bulkApplying ? '应用中...' : '应用到选中项' }}</button>
      </template>
    </el-dialog>
  
    <!-- Mask Editor -->
    <MaskEditor
      :visible="maskEditorVisible"
      :image-url="maskEditorImage ? datasetImageUrl(currentDataset.id, maskEditorImage.relative_path) : ''"
      :mask-url="maskEditorImage && maskEditorImage.mask_relative_path ? datasetImageUrl(currentDataset.id, maskEditorImage.mask_relative_path, true) : ''"
      :dataset-id="currentDataset?.id || ''"
      :image-id="maskEditorImage?.id || ''"
      @close="maskEditorVisible = false"
      @saved="onMaskSaved"
    />

    <!-- Rename dataset dialog -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名数据集"
      width="460"
      align-center
      destroy-on-close
      class="rename-dataset-dialog"
    >
      <div v-if="currentDataset" class="rename-dataset-body">
        <div class="rename-field">
          <label>当前名称</label>
          <div class="rename-current-name">{{ currentDataset.name }}</div>
        </div>
        <div class="rename-field">
          <label>新名称</label>
          <input
            v-model="renameNewName"
            class="rename-input"
            placeholder="输入新的数据集名称"
            maxlength="200"
            autofocus
            @keydown.enter="confirmRename"
          />
          <p v-if="renameError" class="rename-error">{{ renameError }}</p>
          <p v-else class="rename-hint">名称在所有用户之间唯一，不能与其他数据集重名</p>
        </div>
      </div>
      <template #footer>
        <div class="rename-footer">
          <button class="app-btn ghost" @click="renameDialogVisible = false" :disabled="renaming">取消</button>
          <button class="app-btn primary" @click="confirmRename" :disabled="!canConfirmRename || renaming">
            {{ renaming ? '保存中...' : '保存' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- Delete dataset confirmation dialog -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除数据集"
      width="520"
      align-center
      destroy-on-close
      class="delete-dataset-dialog"
    >
      <div v-if="currentDataset" class="delete-dataset-body">
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
            <span class="delete-summary-value">{{ formatBytes(currentDataset.total_size) }}</span>
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
            @keydown.enter="confirmDeleteDataset"
          />
        </div>
      </div>
      <template #footer>
        <div class="delete-footer">
          <button class="app-btn ghost" @click="deleteDialogVisible = false" :disabled="deleting">取消</button>
          <button class="app-btn danger solid" @click="confirmDeleteDataset" :disabled="!canConfirmDelete || deleting">
            {{ deleting ? '删除中...' : '永久删除' }}
          </button>
        </div>
      </template>
    </el-dialog>
</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listDatasets,
  listDatasetImages,
  patchDatasetImage,
  deleteDatasetImage,
  bulkUpdateDatasetImages,
  datasetImageUrl,
  deleteDataset,
  updateDataset,
} from '@/utils/api'
import MaskEditor from '@/components/MaskEditor.vue'
import { onDatasetListChanged } from '@/utils/datasetBus'

const PAGE_SIZE = 48

const datasets = ref([])
const loadingDatasets = ref(false)
const selectedDatasetId = ref(null)
const currentDataset = ref(null)
const images = ref([])
const loadingImages = ref(false)
const totalPages = ref(1)
const page = ref(1)
const totalCount = ref(0)
const selectedIds = ref(new Set())
const detailVisible = ref(false)
const detailImage = ref(null)
const detailSaving = ref(false)
const editForm = ref({ keyword: '', labels: {}, mask_status: 'not_requested', source_page_title: '' })

const sampleJsonUrl = (img) => datasetImageUrl(currentDataset.value.id, 'samples_json/' + img.filename.replace('.jpg', '.json'))

const colFilters = ref({})
const colFilterVisible = ref(false)
const colFilterKey = ref('')
const colFilterValue = ref('')
const colFilterLabel = computed(() => {
  if (colFilterKey.value === 'filename') return '文件名'
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

const exportDatasetJson = () => {
  const url = datasetImageUrl(currentDataset.value.id, 'dataset.json')
  window.open(url, '_blank')
}


const bulkDialogVisible = ref(false)
const bulkApplying = ref(false)
const bulkForm = ref({ labels: {} })

const maskEditorVisible = ref(false)
const maskEditorImage = ref(null)

const deleteDialogVisible = ref(false)
const deleteConfirmName = ref('')
const deleting = ref(false)
const canConfirmDelete = computed(() =>
  currentDataset.value
  && deleteConfirmName.value === currentDataset.value.name
  && (currentDataset.value.name || '').length > 0
)

const renameDialogVisible = ref(false)
const renameNewName = ref('')
const renaming = ref(false)
const renameError = ref('')
const canConfirmRename = computed(() => {
  const newName = (renameNewName.value || '').trim()
  if (!newName) return false
  if (newName === currentDataset.value?.name) return false
  return true
})

const filters = ref({ keyword: '', mask_status: '', min_width: null, max_width: null })
const viewMode = ref('list')
const listFullscreen = ref(false)
const savingIds = ref(new Set())
const recentlySavedIds = ref(new Set())
const activeAxImgId = ref(null)
const activeAxKey = ref(null)
const filteredAxValues = ref([])

const onAxFocus = (img, ax) => {
  filteredAxValues.value = ax.values
}

const onAxInput = (img, ax, val) => {
  filteredAxValues.value = val
    ? ax.values.filter(v => v.value_name.toLowerCase().includes(val.toLowerCase()))
    : ax.values
}

const toggleAxPanel = (img, ax) => {
  if (activeAxImgId.value === img.id && activeAxKey.value === ax.axis_key) {
    closeAxPanel()
  } else {
    activeAxImgId.value = img.id
    activeAxKey.value = ax.axis_key
    filteredAxValues.value = ax.values
  }
}

const selectAxOption = (img, ax, val) => {
  updateLabel(img, ax.axis_key, val)
  closeAxPanel()
}

const closeAxPanel = () => {
  activeAxImgId.value = null
  activeAxKey.value = null
}

const axes = computed(() => {
  const fields = currentDataset.value?.fields || {}
  return fields.classification_axes || []
})

const needMask = computed(() => Boolean(currentDataset.value?.fields?.need_mask))

const allOnPageSelected = computed(() => {
  if (images.value.length === 0) return false
  return images.value.every(img => selectedIds.value.has(img.id))
})

const filteredCount = computed(() => filteredImages.value.length)

const filteredImages = computed(() => {
  const filters = colFilters.value
  if (!Object.keys(filters).length) return images.value
  return images.value.filter(img => {
    for (const [key, val] of Object.entries(filters)) {
      let cellVal
      if (key === 'filename') cellVal = img.filename || ''
      else cellVal = (img.labels || {})[key] || ''
      if (!cellVal.toLowerCase().includes(val.toLowerCase())) return false
    }
    return true
  })
})

const gridStyle = computed(() => {
  const axisCount = axes.value.length
  const axisCols = axisCount > 0
    ? Array(axisCount).fill('minmax(110px, 1fr)').join(' ')
    : ''
  const maskCol = needMask.value ? '110px ' : ''
  if (axisCount <= 1) {
    return { gridTemplateColumns: '32px 60px minmax(200px, 2fr) ' + maskCol + axisCols + ' minmax(120px, 1fr) 130px' }
  }
  return { gridTemplateColumns: '32px 60px minmax(180px, 1.8fr) ' + maskCol + axisCols + ' minmax(100px, 0.9fr) 130px' }
})

const openMaskEditor = (img) => {
  maskEditorImage.value = img
  maskEditorVisible.value = true
}

const openDeleteDialog = () => {
  if (!currentDataset.value) return
  deleteConfirmName.value = ''
  deleteDialogVisible.value = true
}

const openRenameDialog = () => {
  if (!currentDataset.value) return
  renameNewName.value = currentDataset.value.name || ''
  renameError.value = ''
  renameDialogVisible.value = true
}

const confirmRename = async () => {
  if (!currentDataset.value || !canConfirmRename.value || renaming.value) return
  const newName = renameNewName.value.trim()
  renaming.value = true
  renameError.value = ''
  try {
    const updated = await updateDataset(currentDataset.value.id, { name: newName })
    // Backend returns the patched row; sync local state.
    currentDataset.value = { ...currentDataset.value, ...updated }
    // Also update the entry in the picker list so the dropdown label refreshes.
    const idx = datasets.value.findIndex(d => d.id === currentDataset.value.id)
    if (idx >= 0) datasets.value[idx] = { ...datasets.value[idx], ...updated }
    ElMessage.success('已重命名')
    renameDialogVisible.value = false
  } catch (err) {
    renameError.value = (err && err.message) || String(err)
  } finally {
    renaming.value = false
  }
}

const confirmDeleteDataset = async () => {
  if (!currentDataset.value || !canConfirmDelete.value || deleting.value) return
  deleting.value = true
  const targetId = currentDataset.value.id
  const targetName = currentDataset.value.name
  try {
    await deleteDataset(targetId)
    ElMessage.success(`数据集「${targetName}」已删除`)
    // Reset selection and refresh list
    selectedDatasetId.value = null
    currentDataset.value = null
    images.value = []
    totalCount.value = 0
    totalPages.value = 1
    selectedIds.value = new Set()
    deleteDialogVisible.value = false
    await loadDatasets()
  } catch (err) {
    ElMessage.error('删除失败：' + (err.message || err))
  } finally {
    deleting.value = false
  }
}

const onMaskSaved = async (result) => {
  if (maskEditorImage.value) {
    maskEditorImage.value.mask_relative_path = result.mask_relative_path
    maskEditorImage.value.mask_status = result.mask_status
  }
  // Force reload images to bust browser cache on mask images
  await reloadImages(page.value)
  // Re-link detailImage to the fresh object so prev/next stays valid after mask save
  if (detailVisible.value && detailImage.value) {
    const fresh = images.value.find(i => i.id === detailImage.value.id)
    if (fresh) detailImage.value = fresh
  }
}

const formatBytes = (n) => {
  if (!n) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let v = Number(n)
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(v < 10 && i > 0 ? 1 : 0)} ${units[i]}`
}

const onImgError = () => {
  // No-op: the browser shows its own broken-image placeholder.
  // Previously we dimmed the image here, which made failures look like
  // "hidden" rather than genuinely broken, confusing users during debugging.
}

const loadDatasets = async () => {
  loadingDatasets.value = true
  try {
    const list = await listDatasets()
    datasets.value = list
    // If the currently selected dataset no longer exists (deleted elsewhere), reset selection.
    const stillExists = selectedDatasetId.value && list.some(d => d.id === selectedDatasetId.value)
    if (!stillExists) {
      selectedDatasetId.value = null
      currentDataset.value = null
      images.value = []
      totalCount.value = 0
      totalPages.value = 1
      selectedIds.value = new Set()
    }
    if (list.length > 0 && !selectedDatasetId.value) {
      // Do NOT auto-select a dataset — user must explicitly pick one.
      // Reset any stale image state from a prior session.
      currentDataset.value = null
      images.value = []
      totalCount.value = 0
      totalPages.value = 1
      selectedIds.value = new Set()
    }
  } catch (err) {
    ElMessage.error('加载数据集列表失败：' + (err.message || err))
  } finally {
    loadingDatasets.value = false
  }
}

const onDatasetChange = async (id) => {
  if (!id) return
  selectedDatasetId.value = id
  try {
    const ds = await (await import('@/utils/api')).getDataset(id)
    currentDataset.value = ds
    selectedIds.value = new Set()
    page.value = 1
    await reloadImages(1)
  } catch (err) {
    ElMessage.error('加载数据集失败：' + (err.message || err))
  }
}

const reloadImages = async (targetPage) => {
  if (!currentDataset.value) return
  const p = Number(targetPage) || 1
  loadingImages.value = true
  page.value = p
  try {
    const params = {
      limit: PAGE_SIZE,
      offset: (p - 1) * PAGE_SIZE,
    }
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.mask_status) params.mask_status = filters.value.mask_status
    if (filters.value.min_width) params.min_width = filters.value.min_width
    if (filters.value.max_width) params.max_width = filters.value.max_width
    const result = await listDatasetImages(currentDataset.value.id, params)
    images.value = result.items || result || []
    totalCount.value = result.total ?? images.value.length
    totalPages.value = Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE))
  } catch (err) {
    ElMessage.error('加载样本失败：' + (err.message || err))
    images.value = []
    totalCount.value = 0
    totalPages.value = 1
  } finally {
    loadingImages.value = false
  }
}

const resetFilters = () => {
  filters.value = { keyword: '', mask_status: '', min_width: null, max_width: null }
  reloadImages(1)
}

const flashSaved = (imageId) => {
  const next = new Set(recentlySavedIds.value)
  next.add(imageId)
  recentlySavedIds.value = next
  setTimeout(() => {
    const after = new Set(recentlySavedIds.value)
    after.delete(imageId)
    recentlySavedIds.value = after
  }, 1500)
}

const updateField = async (image, field, value) => {
  if (!currentDataset.value) return
  if ((image[field] || '') === (value || '')) return
  if (savingIds.value.has(image.id)) return
  const next = new Set(savingIds.value)
  next.add(image.id)
  savingIds.value = next
  const oldValue = image[field]
  image[field] = value
  try {
    const updated = await patchDatasetImage(currentDataset.value.id, image.id, { [field]: value })
    Object.assign(image, updated)
    flashSaved(image.id)
  } catch (err) {
    image[field] = oldValue
    ElMessage.error('更新失败: ' + (err.message || err))
  } finally {
    const after = new Set(savingIds.value)
    after.delete(image.id)
    savingIds.value = after
  }
}

const updateLabel = async (image, axisKey, value) => {
  if (!currentDataset.value) return
  const oldLabels = image.labels || {}
  if ((oldLabels[axisKey] || '') === (value || '')) return
  if (savingIds.value.has(image.id)) return
  const next = new Set(savingIds.value)
  next.add(image.id)
  savingIds.value = next
  const newLabels = { ...oldLabels }
  if (value) {
    newLabels[axisKey] = value
  } else {
    delete newLabels[axisKey]
  }
  image.labels = newLabels
  try {
    const updated = await patchDatasetImage(currentDataset.value.id, image.id, { labels: newLabels })
    Object.assign(image, updated)
    flashSaved(image.id)
  } catch (err) {
    image.labels = oldLabels
    ElMessage.error('更新失败: ' + (err.message || err))
  } finally {
    const after = new Set(savingIds.value)
    after.delete(image.id)
    savingIds.value = after
  }
}

const quickDelete = async (image) => {
  try {
    await ElMessageBox.confirm(`确认删除样本 ${image.filename}？此操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch { return }
  if (!currentDataset.value) return
  try {
    await deleteDatasetImage(currentDataset.value.id, image.id)
    ElMessage.success('已删除')
    selectedIds.value.delete(image.id)
    await reloadImages(page.value)
  } catch (err) {
    ElMessage.error('删除失败: ' + (err.message || err))
  }
}

const toggleImage = (id) => {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

const toggleSelectAllOnPage = () => {
  const next = new Set(selectedIds.value)
  if (allOnPageSelected.value) {
    images.value.forEach(img => next.delete(img.id))
  } else {
    images.value.forEach(img => next.add(img.id))
  }
  selectedIds.value = next
}

const clearSelection = () => {
  selectedIds.value = new Set()
}

const openDetail = (img) => {
  detailImage.value = img
  editForm.value = {
    keyword: img.keyword || '',
    labels: { ...(img.labels || {}) },
    mask_status: img.mask_status || 'not_requested',
    source_page_title: img.source_page_title || '',
  }
  detailVisible.value = true
}

const detailIndex = computed(() => {
  if (!detailImage.value) return -1
  return images.value.findIndex(i => i.id === detailImage.value.id)
})

const hasPrev = computed(() => detailIndex.value > 0)
const hasNext = computed(() => detailIndex.value >= 0 && detailIndex.value < images.value.length - 1)

const detailDirty = computed(() => {
  if (!detailImage.value) return false
  const img = detailImage.value
  const f = editForm.value
  if ((f.keyword || '') !== (img.keyword || '')) return true
  if ((f.source_page_title || '') !== (img.source_page_title || '')) return true
  if ((f.mask_status || '') !== (img.mask_status || '')) return true
  const orig = img.labels || {}
  const keys = new Set([...Object.keys(f.labels || {}), ...Object.keys(orig)])
  for (const k of keys) {
    if ((f.labels[k] || '') !== (orig[k] || '')) return true
  }
  return false
})

const confirmDiscardDirty = async () => {
  if (!detailDirty.value) return true
  try {
    await ElMessageBox.confirm('当前样本有未保存的修改，切换将丢弃这些修改。', '未保存的修改', {
      type: 'warning',
      confirmButtonText: '丢弃并继续',
      cancelButtonText: '取消',
    })
    return true
  } catch {
    return false
  }
}

const gotoPrev = async () => {
  if (!hasPrev.value) return
  if (!(await confirmDiscardDirty())) return
  openDetail(images.value[detailIndex.value - 1])
}

const gotoNext = async () => {
  if (!hasNext.value) return
  if (!(await confirmDiscardDirty())) return
  openDetail(images.value[detailIndex.value + 1])
}

const saveDetail = async () => {
  if (!detailImage.value || !currentDataset.value) return
  detailSaving.value = true
  try {
    const payload = {
      keyword: editForm.value.keyword,
      labels: editForm.value.labels,
      mask_status: editForm.value.mask_status,
      source_page_title: editForm.value.source_page_title,
    }
    await patchDatasetImage(currentDataset.value.id, detailImage.value.id, payload)
    // detailImage.value 指向 images 中的同一个响应式 proxy，直接修改属性即可
    detailImage.value.keyword = editForm.value.keyword
    detailImage.value.labels = { ...editForm.value.labels }
    detailImage.value.mask_status = editForm.value.mask_status
    detailImage.value.source_page_title = editForm.value.source_page_title
    ElMessage.success('已保存')
    detailVisible.value = false
  } catch (err) {
    ElMessage.error('保存失败：' + (err.message || err))
  } finally {
    detailSaving.value = false
  }
}

const deleteOne = async (imageId) => {
  try {
    await ElMessageBox.confirm('确认删除该样本？此操作不可恢复。', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch { return }
  if (!currentDataset.value) return
  detailSaving.value = true
  try {
    await deleteDatasetImage(currentDataset.value.id, imageId)
    ElMessage.success('已删除')
    detailVisible.value = false
    selectedIds.value.delete(imageId)
    await reloadImages(page.value)
  } catch (err) {
    ElMessage.error('删除失败：' + (err.message || err))
  } finally {
    detailSaving.value = false
  }
}

const openBulkLabelDialog = () => {
  bulkForm.value = { labels: {} }
  axes.value.forEach(ax => { bulkForm.value.labels[ax.axis_key] = '' })
  bulkDialogVisible.value = true
}

const applyBulkLabel = async () => {
  const setLabels = {}
  for (const [k, v] of Object.entries(bulkForm.value.labels || {})) {
    if (v) setLabels[k] = v
  }
  if (Object.keys(setLabels).length === 0) {
    ElMessage.warning('至少选择一个分类轴的新值')
    return
  }
  bulkApplying.value = true
  try {
    const ids = Array.from(selectedIds.value)
    await bulkUpdateDatasetImages(currentDataset.value.id, {
      image_ids: ids,
      set: { labels: setLabels },
    })
    ElMessage.success(`已更新 ${ids.length} 项`)
    bulkDialogVisible.value = false
    clearSelection()
    await reloadImages(page.value)
  } catch (err) {
    ElMessage.error('批量更新失败：' + (err.message || err))
  } finally {
    bulkApplying.value = false
  }
}

const bulkUpdateMask = async (status) => {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return
  try {
    await bulkUpdateDatasetImages(currentDataset.value.id, {
      image_ids: ids,
      set: { mask_status: status },
    })
    ElMessage.success(`已将 ${ids.length} 项标记为 ${status}`)
    await reloadImages(page.value)
  } catch (err) {
    ElMessage.error('更新失败：' + (err.message || err))
  }
}

const bulkDelete = async () => {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${ids.length} 项样本？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch { return }
  let ok = 0
  let failed = 0
  for (const id of ids) {
    try {
      await deleteDatasetImage(currentDataset.value.id, id)
      ok++
    } catch (err) {
      failed++
    }
  }
  ElMessage.success(`已删除 ${ok} 项${failed ? `，${failed} 项失败` : ''}`)
  clearSelection()
  await reloadImages(page.value)
}

let stopDatasetListWatch = null
onMounted(() => {
  loadDatasets()
  // Cross-component sync via shared reactive bus (works in same tab).
  // The bus also bumps a localStorage key so other browser tabs can react via the `storage` event.
  stopDatasetListWatch = onDatasetListChanged(() => {
    loadDatasets()
  })
  window.addEventListener('keydown', handleListKeydown)
  document.addEventListener('click', handleDocClick)
})

const handleListKeydown = (e) => {
  if (e.key === 'Escape' && listFullscreen.value) {
    listFullscreen.value = false
  }
  if (e.key === 'Escape' && activeAxImgId.value) {
    closeAxPanel()
  }
}

const handleDocClick = (e) => {
  if (activeAxImgId.value && !e.target.closest('.cell-ax-wrap')) {
    closeAxPanel()
  }
}

onUnmounted(() => {
  if (stopDatasetListWatch) {
    stopDatasetListWatch()
    stopDatasetListWatch = null
  }
  window.removeEventListener('keydown', handleListKeydown)
})
</script>

<style scoped>
.edit-ds-page { padding: 0 4px; max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.page-header h2 { margin: 0 0 4px; font-size: 20px; font-weight: 600; color: var(--text-primary); }
.page-desc { margin: 0; font-size: 13px; color: var(--text-tertiary); }
.header-actions { display: flex; gap: 8px; }

/* Buttons use global .app-btn utilities defined in App.vue. */

/* Dataset picker */
.ds-picker { display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: var(--glass-bg); border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 16px; }
.ds-picker-label { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
.ds-picker-select { flex: 1; max-width: 480px; }
.ds-option { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.ds-option-name { font-size: 13px; color: var(--text-primary); }
.ds-option-meta { font-size: 12px; color: var(--text-tertiary); }
.ds-empty { font-size: 13px; color: var(--text-tertiary); }
.ds-empty a { color: #3a7d7e; text-decoration: none; font-weight: 500; }
.ds-empty a:hover { text-decoration: underline; }

/* Hint card shown when datasets exist but none is selected */
.ds-hint-card {
  display: flex; gap: 18px; align-items: flex-start;
  padding: 20px 22px; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(58,125,126,0.06), rgba(58,125,126,0.02));
  border: 1px dashed rgba(58,125,126,0.35);
  border-radius: 12px;
}
.ds-hint-icon {
  flex-shrink: 0; width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(58,125,126,0.12); color: #3a7d7e;
  border-radius: 12px;
}
.ds-hint-body { flex: 1; }
.ds-hint-body h4 { margin: 0 0 6px; font-size: 15px; font-weight: 600; color: var(--text-primary); }
.ds-hint-body p { margin: 0 0 12px; font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.ds-hint-body strong { color: var(--accent-secondary); font-weight: 600; }
.ds-hint-cta {
  display: inline-block; padding: 7px 14px; border-radius: 8px;
  background: #3a7d7e; color: white; font-size: 12.5px;
  text-decoration: none; font-weight: 500; transition: background 0.15s ease;
}
.ds-hint-cta:hover { background: #2f6667; }

/* Dataset info bar */
.ds-info-bar { display: flex; flex-direction: column; gap: 0; padding: 16px 18px; background: rgba(58,125,126,0.05); border: 1px solid rgba(58,125,126,0.12); border-radius: 12px; margin-bottom: 16px; }
.ds-info-top { display: flex; align-items: center; gap: 20px; }
.ds-info-main { flex: 1; min-width: 0; }
.ds-info-main h3 { margin: 0 0 4px; font-size: 16px; font-weight: 600; color: var(--text-primary); }
.ds-info-name { display: inline-flex; align-items: center; gap: 8px; }
.ds-info-desc { font-size: 13px; color: var(--text-secondary); margin: 10px 0 0; line-height: 1.5; word-break: break-all; }
.rename-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 5px;
  background: transparent; border: 1px solid transparent;
  color: var(--text-tertiary); cursor: pointer; padding: 0;
  transition: all 0.15s ease;
}
.rename-btn:hover:not(:disabled) {
  background: rgba(58, 125, 126, 0.10);
  color: var(--accent-primary);
  border-color: rgba(58, 125, 126, 0.25);
}
.rename-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.ds-info-stats { display: flex; gap: 20px; }
.ds-info-stats .stat { display: flex; flex-direction: column; align-items: flex-end; }
.ds-info-stats .stat-value { font-size: 16px; font-weight: 600; color: #3a7d7e; }
.ds-info-stats .stat-label { font-size: 11px; color: var(--text-tertiary); }
.ds-info-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.ds-info-actions { display: flex; align-items: center; justify-content: flex-end; }
.axis-chip { font-size: 11.5px; padding: 3px 9px; border-radius: 999px; background: rgba(58,125,126,0.12); color: var(--accent-secondary); }
.axis-chip em { font-style: normal; opacity: 0.7; margin-left: 3px; }
.axis-chip.mask { background: rgba(245,158,11,0.12); color: #b45309; }

/* Filter bar */
.filter-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
.filter-left { display: flex; gap: 8px; align-items: center; }
.fullscreen-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 36px; height: 36px;
  border-radius: 8px; border: none;
  background: rgba(58,125,126,0.08);
  backdrop-filter: blur(8px);
  cursor: pointer; transition: all 0.15s;
  flex-shrink: 0;
}
.fullscreen-btn .icon-dark { display: none; }
.dark .fullscreen-btn .icon-light { display: none; }
.dark .fullscreen-btn .icon-dark { display: block; }

.fullscreen-btn:hover {
  background: rgba(58,125,126,0.15);
}
.filter-right { font-size: 12.5px; color: var(--text-tertiary); display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.filter-input, .filter-select { padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 12.5px; background: var(--bg-secondary); color: var(--text-primary); min-width: 130px; }
.filter-input.small { min-width: 90px; max-width: 110px; }
.filter-input:focus, .filter-select:focus { outline: none; border-color: #3a7d7e; }

/* Select bar */
.select-bar { display: flex; align-items: center; gap: 12px; padding: 6px 12px; margin-bottom: 10px; font-size: 12.5px; color: var(--text-secondary); }
.select-all { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.selected-pill { background: rgba(58,125,126,0.1); color: var(--accent-secondary); padding: 2px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 500; }

/* Image grid */
.grid-loading, .grid-empty { padding: 40px 0; text-align: center; font-size: 13px; color: var(--text-tertiary); }
.image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
.image-card { position: relative; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; transition: all 0.15s ease; }
.image-card:hover { border-color: rgba(58,125,126,0.4); box-shadow: 0 4px 12px rgba(58,125,126,0.08); }
.image-card.selected { border-color: #3a7d7e; box-shadow: 0 0 0 2px rgba(58,125,126,0.18); }
.image-check { position: absolute; top: 6px; left: 6px; z-index: 2; background: var(--bg-secondary); border-radius: 6px; padding: 3px 5px; cursor: pointer; display: flex; }
.image-thumb { position: relative; aspect-ratio: 1; background: var(--bg-tertiary); cursor: pointer; overflow: hidden; }
.image-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.mask-badge { position: absolute; top: 6px; right: 6px; background: rgba(58,125,126,0.92); color: white; font-size: 10px; font-weight: 600; width: 18px; height: 18px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.mask-badge.failed { background: rgba(239,68,68,0.92); }
.image-meta { padding: 8px 10px; }
.image-name { font-size: 11.5px; color: var(--text-primary); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.image-keyword { font-size: 11px; color: var(--text-secondary); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.image-labels { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.label-chip { font-size: 10px; padding: 1px 6px; border-radius: 999px; background: rgba(245,158,11,0.12); color: #92400e; }

/* Pagination */
.pagination-bulk-row { display: flex; justify-content: space-between; align-items: center; margin: 16px 0 0; }
.pagination { display: flex; justify-content: flex-end; align-items: center; gap: 12px; }
.page-btn { padding: 6px 12px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); cursor: pointer; font-size: 12px; color: var(--text-secondary); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 12.5px; color: var(--text-secondary); }

/* Bulk action floating bar */
.bulk-bar { position: sticky; bottom: 20px; margin: 16px auto 0; max-width: 700px; display: flex; align-items: center; gap: 10px; padding: 12px 18px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 14px; box-shadow: var(--shadow-lg); z-index: 5; }
.bulk-count { font-size: 13px; flex: 1; color: var(--text-primary); }
.bulk-count b { color: var(--accent-primary); font-weight: 600; }
.bulk-btn { padding: 6px 12px; border-radius: 6px; background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border-color); font-size: 12.5px; cursor: pointer; transition: all 0.15s ease; }
.bulk-btn:hover:not(:disabled) { border-color: var(--accent-primary); color: var(--accent-primary); }
.bulk-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.bulk-btn.danger { background: rgba(239,68,68,0.1); color: var(--danger); border-color: rgba(239,68,68,0.3); }
.bulk-btn.danger:hover { background: var(--danger); color: white; border-color: var(--danger); }
.bulk-fade-enter-active, .bulk-fade-leave-active { transition: all 0.2s ease; }
.bulk-fade-enter-from, .bulk-fade-leave-to { transform: translateY(20px); opacity: 0; }

/* Image detail dialog */
.image-detail-dialog .el-dialog__body { padding: 0; }
.detail-content { display: grid; grid-template-columns: 1fr 1fr; min-height: 420px; }
.detail-preview { position: relative; background: var(--bg-primary); display: flex; flex-direction: column; gap: 8px; padding: 12px; }
.detail-preview > img { width: 100%; flex: 1; object-fit: contain; border-radius: 6px; background: var(--bg-secondary); }
.preview-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--bg-secondary); color: #3a7d7e;
  border: 1px solid rgba(58,125,126,0.35); cursor: pointer;
  font-size: 22px; line-height: 1; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s ease; z-index: 3;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  padding: 0;
}
.preview-nav:hover:not(:disabled) { background: #3a7d7e; color: white; border-color: #3a7d7e; }
.preview-nav:disabled { opacity: 0.3; cursor: not-allowed; }
.preview-nav.prev { left: 20px; }
.preview-nav.next { right: 20px; }
.mask-preview { position: relative; cursor: pointer; transition: opacity 0.15s ease; }
.mask-preview:hover { opacity: 0.88; }
.mask-preview img { width: 100%; height: 120px; object-fit: contain; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-color); }
.mask-preview-label { position: absolute; top: 6px; left: 6px; background: rgba(58,125,126,0.92); color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.mask-preview.empty {
  display: flex; align-items: center; justify-content: center;
  border: 1px dashed rgba(58,125,126,0.4); border-radius: 6px;
  background: rgba(58,125,126,0.04); padding: 14px;
  min-height: 100px;
}
.mask-preview.empty:hover { background: rgba(58,125,126,0.08); }
.mask-empty-detail {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  color: #3a7d7e; font-size: 12px; font-weight: 500;
}
.detail-fields { padding: 18px 20px; overflow-y: auto; max-height: 480px; }
.detail-fields .field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.detail-fields label { font-size: 12px; color: var(--text-tertiary); }
.detail-fields input, .detail-fields select { padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 13px; background: var(--bg-secondary); color: var(--text-primary); }
.detail-fields input:focus, .detail-fields select:focus { outline: none; border-color: #3a7d7e; }
.detail-fields .readonly span { font-size: 12.5px; color: var(--text-secondary); padding: 6px 0; display: block; }
.detail-fields .readonly .readonly-text { word-break: break-all; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; color: var(--text-secondary); }
.caption-text { width: 100%; padding: 6px 8px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 12px; line-height: 1.5; color: var(--text-primary); background: var(--bg-primary); resize: vertical; font-family: inherit; }
.json-link { display: inline-flex; align-items: center; gap: 4px; text-decoration: none; color: #3a7d7e; font-weight: 500; font-family: inherit; font-size: 12px; }
.json-link:hover { text-decoration: underline; background: rgba(58,125,126,0.06); padding: 2px 6px; border-radius: 4px; }
.label-chip { display: inline-block; padding: 2px 8px; margin: 1px 2px; border-radius: 10px; font-size: 10.5px; background: rgba(58,125,126,0.10); color: var(--accent-secondary); }
.image-keyword { font-size: 10.5px; color: #3a7d7e; margin-top: 2px; font-weight: 500; }
.detail-footer { display: flex; justify-content: flex-end; gap: 8px; }

/* Bulk form */
.bulk-form .field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.bulk-form label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }

/* Ensure bulk dialog text readable in light mode */
:deep(.bulk-dialog) .el-dialog__body,
:deep(.bulk-dialog) .bulk-form {
  color: var(--text-primary);
}
:deep(.bulk-dialog) .bulk-form .field label,
:deep(.bulk-dialog) .bulk-form label {
  color: var(--text-secondary) !important;
}
:deep(.bulk-dialog) .bulk-form select {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--border-color);
}
.bulk-form select { padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 13px; background: var(--bg-secondary); color: var(--text-primary); }
.bulk-tip { font-size: 12px; color: var(--text-secondary); margin: 8px 0 0; line-height: 1.5; }


/* View mode toggle */
.view-toggle { display: inline-flex; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-right: 12px; }
.view-toggle button { padding: 5px 14px; background: var(--bg-secondary); color: var(--text-secondary); font-size: 12.5px; border: none; cursor: pointer; transition: all 0.15s ease; }
.view-toggle button:hover { background: rgba(58,125,126,0.05); color: var(--accent-secondary); }
.view-toggle button.active { background: #3a7d7e; color: white; }
.view-toggle button + button { border-left: 1px solid rgba(148,163,184,0.3); }

/* Fullscreen list container */
.list-fullscreen-wrap { display: contents; }
.list-fullscreen-wrap.fullscreen-active {
  position: fixed; inset: 0; z-index: 999;
  background: var(--bg-primary);
  display: flex; flex-direction: column;
  overflow: hidden;
  padding: 16px;
}
.list-fullscreen-wrap.fullscreen-active .filter-bar { flex-shrink: 0; }
.list-fullscreen-wrap.fullscreen-active .select-bar { flex-shrink: 0; }
.list-fullscreen-wrap.fullscreen-active .image-list-wrap { flex: 1; overflow: auto; }
.list-fullscreen-wrap.fullscreen-active .bulk-bar { position: static; margin: 0 auto; border-radius: 14px; border-left: 1px solid var(--border-color); border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); flex-shrink: 0; }
.list-fullscreen-wrap.fullscreen-active .pagination-bulk-row { margin: 0; padding: 12px 16px; border-top: 1px solid var(--border-color); background: var(--bg-secondary); border-radius: 0 0 14px 14px; }
.list-fullscreen-wrap.fullscreen-active .pagination { margin: 0; }

.image-list-wrap { overflow-x: auto; }
.image-list-wrap::-webkit-scrollbar { height: 6px; }
.image-list-wrap::-webkit-scrollbar-track { background: transparent; }
.image-list-wrap::-webkit-scrollbar-thumb { background: rgba(58,125,126,0.3); border-radius: 999px; }
.image-list-wrap::-webkit-scrollbar-thumb:hover { background: rgba(58,125,126,0.6); }
.image-list-wrap .image-list { overflow: auto; }
.image-list { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
.image-list .list-header,
.image-list .list-row { display: grid; align-items: center; gap: 8px; padding: 8px 12px; }
.image-list .list-header { background: rgba(58,125,126,0.06); border-bottom: 1px solid rgba(58,125,126,0.18); font-size: 11.5px; font-weight: 600; color: var(--accent-secondary); letter-spacing: 0.02em; }
.image-list .list-row { position: relative; border-bottom: 1px solid rgba(148,163,184,0.1); transition: background 0.15s ease; font-size: 12.5px; }
.image-list .list-row:last-child { border-bottom: none; }
.image-list .list-row:hover { background: rgba(58,125,126,0.03); }
.image-list .list-row.selected { background: rgba(58,125,126,0.09); }
.image-list .list-row.saving { opacity: 0.6; }
.image-list .col { min-width: 0; }
.image-list .col-check { display: flex; justify-content: center; }
.image-list .col-check input { cursor: pointer; }
.image-list .col-thumb img { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; cursor: pointer; background: var(--bg-tertiary); border: 1px solid var(--border-color); transition: transform 0.15s ease; }
.image-list .mask-thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; cursor: pointer; background: var(--bg-tertiary); border: 1px solid var(--border-color); }
.image-list .mask-empty { font-size: 12px; color: var(--text-tertiary); }
.image-list .col-thumb img:hover { transform: scale(1.06); }
.image-list .col-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-primary); cursor: pointer; }
.image-list .col-name:hover { color: #3a7d7e; }
.image-list .cell-ax-wrap { position: relative; display: flex; align-items: center; }
.image-list .cell-ax-input { flex: 1; width: 100%; padding: 5px 6px; border: 1px solid transparent; border-radius: 5px; font-size: 12px; background: transparent; color: #000; font-family: inherit; cursor: pointer; min-width: 0; }
.image-list .cell-ax-input:focus { outline: none; border-color: var(--accent-primary); background: var(--bg-secondary); }
.image-list .cell-ax-input::placeholder { color: var(--text-tertiary); }
.dark .image-list .cell-ax-input { color: #fff; }
.ax-arrow { flex-shrink: 0; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; cursor: pointer; color: var(--text-tertiary); padding: 0; margin-right: 2px; transition: transform 0.15s; }
.ax-arrow:hover { color: var(--accent-primary); }
.ax-arrow.open { transform: rotate(180deg); }
.image-list .cell-ax-dropdown { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: var(--shadow-lg); z-index: 100; max-height: 200px; overflow-y: auto; }
.image-list .ax-option { padding: 7px 10px; font-size: 12px; cursor: pointer; color: var(--text-primary); }
.image-list .ax-option:hover { background: rgba(58,125,126,0.1); }
.image-list .ax-option.active { background: rgba(58,125,126,0.15); color: var(--accent-primary); font-weight: 600; }
.image-list .ax-option-empty { color: var(--text-tertiary); cursor: default; text-align: center; }
.image-list .ax-option-empty:hover { background: transparent; }
.col-filter-btn { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border: none; background: transparent; cursor: pointer; color: var(--text-tertiary); padding: 0; border-radius: 3px; vertical-align: middle; margin-left: 3px; transition: all 0.15s; }
.col-filter-btn:hover { color: var(--accent-primary); }
.col-filter-btn.active { color: #fff; background: var(--accent-primary); }
.col-filter-dialog .col-filter-body { padding: 4px 0 12px; }
.col-filter-hint { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
.col-filter-hint b { color: var(--text-primary); }
.col-filter-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 13px; background: var(--bg-secondary); color: var(--text-primary); box-sizing: border-box; }
.col-filter-input:focus { outline: none; border-color: var(--accent-primary); }
.image-list .col-actions { display: flex; gap: 6px; justify-content: flex-end; align-items: center; }
.image-list .icon-btn { padding: 4px 10px; border-radius: 6px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); cursor: pointer; font-size: 11.5px; transition: all 0.15s ease; }
.image-list .icon-btn:hover { background: rgba(58,125,126,0.08); color: #3a7d7e; border-color: rgba(58,125,126,0.18); }
.image-list .icon-btn.danger:hover { background: rgba(239,68,68,0.08); color: #ef4444; border-color: rgba(239,68,68,0.22); }
.saved-pulse { font-size: 10.5px; color: var(--accent-primary); background: rgba(58,125,126,0.12); padding: 2px 7px; border-radius: 999px; animation: savedFade 1.5s ease; }
@keyframes savedFade { 0% { opacity: 0; transform: translateY(-2px); } 15% { opacity: 1; transform: translateY(0); } 80% { opacity: 1; } 100% { opacity: 0.6; } }

/* Delete dataset confirmation dialog */
.delete-dataset-body { display: flex; flex-direction: column; gap: 16px; }
.delete-warning {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 14px 16px; border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
}
.delete-warning-icon {
  flex-shrink: 0; width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(239, 68, 68, 0.15); color: #ef4444;
  border-radius: 50%;
}
.delete-warning-text { flex: 1; }
.delete-warning-title { margin: 0 0 4px; font-size: 14px; font-weight: 600; color: var(--danger); }
.delete-warning-detail { margin: 0; font-size: 12.5px; line-height: 1.55; color: var(--text-secondary); }
.delete-summary {
  display: flex; flex-direction: column; gap: 6px;
  padding: 12px 16px; border-radius: 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
}
.delete-summary-row { display: flex; justify-content: space-between; gap: 12px; font-size: 12.5px; }
.delete-summary-label { color: var(--text-tertiary); }
.delete-summary-value { color: var(--text-primary); font-weight: 500; }
.delete-summary-value.name { color: var(--accent-primary); font-weight: 600; }
.delete-confirm-input label {
  display: block; font-size: 12.5px; color: var(--text-secondary); margin-bottom: 6px; line-height: 1.5;
}
.delete-confirm-input code {
  padding: 1px 6px; border-radius: 4px;
  background: rgba(58, 125, 126, 0.12); color: var(--accent-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px; font-weight: 600;
}
.delete-input {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px; font-family: inherit;
  transition: all 0.15s ease;
}
.delete-input:focus {
  outline: none;
  border-color: var(--danger);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.18);
}
.delete-input::placeholder { color: var(--text-tertiary); }
.delete-footer { display: flex; justify-content: flex-end; gap: 8px; }

/* Rename dataset dialog */
.rename-dataset-body { display: flex; flex-direction: column; gap: 14px; }
.rename-field label { display: block; font-size: 12.5px; color: var(--text-secondary); margin-bottom: 6px; }
.rename-current-name {
  padding: 8px 12px; border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  word-break: break-all;
}
.rename-input {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px; font-family: inherit;
  transition: all 0.15s ease;
}
.rename-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(58, 125, 126, 0.18);
}
.rename-input::placeholder { color: var(--text-tertiary); }
.rename-error { margin: 6px 0 0; font-size: 12px; color: var(--danger); }
.rename-hint { margin: 6px 0 0; font-size: 12px; color: var(--text-tertiary); }
.rename-footer { display: flex; justify-content: flex-end; gap: 8px; }
</style>
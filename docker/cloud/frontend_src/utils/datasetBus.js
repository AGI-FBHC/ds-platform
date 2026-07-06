import { reactive, watch } from 'vue'

// Tiny reactive event bus for "dataset list changed" notifications.
//
// Why not just `localStorage` storage events?
//   The browser only fires `storage` events in *other* tabs, not the originating
//   tab -- which is exactly the case when the user deletes a dataset from
//   MyDatasets in the same tab and expects EditDatasets's dropdown to refresh.
//
// So we use a module-level reactive counter for same-tab subscribers, and we
// also mirror every change to `localStorage` so that *other* browser tabs can
// react via the standard `storage` event if they want.
//
// Usage:
//   import { refreshDatasetList, onDatasetListChanged } from '@/utils/datasetBus'
//   const stop = onDatasetListChanged(() => loadDatasets())   // subscribe
//   onUnmounted(stop)                                         // cleanup
//   refreshDatasetList()                                       // after a mutation

const state = reactive({
  version: 0,
})

const STORAGE_KEY = 'datasetListVersion'

export function refreshDatasetList() {
  state.version += 1
  // Best-effort: bump a localStorage key so *other* browser tabs/windows
  // can listen via the standard `storage` event.
  try {
    localStorage.setItem(STORAGE_KEY, String(Date.now()))
  } catch (_) {
    // ignore quota / private-mode errors
  }
}

export function getDatasetListVersion() {
  return state.version
}

// Subscribe to dataset-list-changed notifications.
// Returns a stop handle the caller may invoke in onUnmounted to clean up.
export function onDatasetListChanged(callback) {
  const stopWatch = watch(() => state.version, () => callback())
  const onStorage = (e) => {
    if (e.key === STORAGE_KEY) callback()
  }
  window.addEventListener('storage', onStorage)
  return () => {
    stopWatch()
    window.removeEventListener('storage', onStorage)
  }
}

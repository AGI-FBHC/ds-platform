import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Datasets from '../views/Datasets.vue'
import AppLayout from '../views/AppLayout.vue'
import MyDatasets from '../views/MyDatasets.vue'
import Tasks from '../views/Tasks.vue'
import EditDatasets from '../views/EditDatasets.vue'
import DatasetDetail from '../views/DatasetDetail.vue'
import { isLoggedIn, getCurrentUser, removeToken } from '../utils/api'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: '/datasets',
    name: 'GuestDatasets',
    component: Datasets,
    meta: { requiresAuth: false },
  },
  {
    path: '/dataset/:id',
    name: 'GuestDatasetDetail',
    component: DatasetDetail,
    meta: { requiresAuth: false },
  },
  {
    path: '/app',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'datasets',
        name: 'AppDatasets',
        component: Datasets,
      },
      {
        path: 'my-datasets',
        name: 'MyDatasets',
        component: MyDatasets,
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: Tasks,
      },
      {
        path: 'edit-dataset',
        name: 'EditDataset',
        component: EditDatasets,
      },
      {
        path: 'dataset/:id',
        name: 'DatasetDetail',
        component: DatasetDetail,
      },
      {
        path: '',
        redirect: '/app/datasets',
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  if (requiresAuth) {
    if (!isLoggedIn()) {
      next('/')
      return
    }
    try {
      const user = await getCurrentUser()
      localStorage.setItem('userInfo', JSON.stringify(user))
      next()
    } catch (error) {
      removeToken()
      next('/')
    }
  } else {
    next()
  }
})

export default router

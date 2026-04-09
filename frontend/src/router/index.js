import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ExportHistory from '../views/ExportHistory.vue'
import VideoUploader from '../views/VideoUploader.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/export-history',
    name: 'ExportHistory',
    component: ExportHistory,
  },
  {
    path: '/video-upload',
    name: 'VideoUploader',
    component: VideoUploader,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
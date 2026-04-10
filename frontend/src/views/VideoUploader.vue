<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div class="flex items-center gap-4">
          <h1 class="text-2xl font-bold text-xhs-red">视频上传</h1>
          <router-link
            to="/"
            class="text-gray-600 hover:text-gray-800 text-sm"
          >
            返回评论获取
          </router-link>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8">
      <div v-if="checkingChrome" class="bg-white rounded-lg shadow-md p-8 mb-6">
        <div class="text-center">
          <div class="mb-6">
            <svg class="w-20 h-20 mx-auto text-gray-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <p class="text-gray-500">检查 Chrome 状态中...</p>
        </div>
      </div>

      <div v-else-if="!chromeStarted" class="bg-white rounded-lg shadow-md p-8 mb-6">
        <div class="text-center">
          <div class="mb-6">
            <svg class="w-20 h-20 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 class="text-xl font-bold text-gray-800 mb-2">第一步：启动 Chrome 并登录</h2>
          <p class="text-gray-500 mb-6">点击下方按钮启动 Chrome，请手动登录创作者平台账号</p>
          <button
            @click="startChrome"
            :disabled="startingChrome"
            class="bg-xhs-red text-white py-3 px-8 rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg"
          >
            {{ startingChrome ? '启动中...' : '启动 Chrome' }}
          </button>
          <p v-if="chromeError" class="text-red-500 mt-4">{{ chromeError }}</p>
        </div>
      </div>

      <div v-else class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-bold text-gray-800 mb-6">视频上传到创作者平台</h2>
        
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            选择平台（可多选）
          </label>
          <div class="grid grid-cols-4 gap-3">
            <button
              @click="togglePlatform('xiaohongshu')"
              :class="[
                'p-3 rounded-lg border-2 transition-all text-left relative',
                selectedPlatforms.includes('xiaohongshu') 
                  ? 'border-xhs-red bg-red-50' 
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div v-if="selectedPlatforms.includes('xiaohongshu')" class="absolute top-1 right-1 w-5 h-5 bg-xhs-red rounded-full flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-xhs-red flex items-center justify-center">
                  <span class="text-white font-bold text-sm">X</span>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm">小红书</p>
                  <p class="text-xs text-gray-400">xiaohongshu</p>
                </div>
              </div>
            </button>
            <button
              @click="togglePlatform('douyin')"
              :class="[
                'p-3 rounded-lg border-2 transition-all text-left relative',
                selectedPlatforms.includes('douyin') 
                  ? 'border-pink-500 bg-pink-50' 
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div v-if="selectedPlatforms.includes('douyin')" class="absolute top-1 right-1 w-5 h-5 bg-pink-500 rounded-full flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
                  <span class="text-white font-bold text-sm">D</span>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm">抖音</p>
                  <p class="text-xs text-gray-400">douyin</p>
                </div>
              </div>
            </button>
            <button
              @click="togglePlatform('kuaishou')"
              :class="[
                'p-3 rounded-lg border-2 transition-all text-left relative',
                selectedPlatforms.includes('kuaishou') 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div v-if="selectedPlatforms.includes('kuaishou')" class="absolute top-1 right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center">
                  <span class="text-white font-bold text-sm">K</span>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm">快手</p>
                  <p class="text-xs text-gray-400">kuaishou</p>
                </div>
              </div>
            </button>
            <button
              @click="togglePlatform('baijiahao')"
              :class="[
                'p-3 rounded-lg border-2 transition-all text-left relative',
                selectedPlatforms.includes('baijiahao') 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div v-if="selectedPlatforms.includes('baijiahao')" class="absolute top-1 right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                  <span class="text-white font-bold text-sm">B</span>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm">百家号</p>
                  <p class="text-xs text-gray-400">baijiahao</p>
                </div>
              </div>
            </button>
            <button
              @click="togglePlatform('bilibili')"
              :class="[
                'p-3 rounded-lg border-2 transition-all text-left relative',
                selectedPlatforms.includes('bilibili') 
                  ? 'border-pink-400 bg-pink-50' 
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div v-if="selectedPlatforms.includes('bilibili')" class="absolute top-1 right-1 w-5 h-5 bg-pink-400 rounded-full flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-blue-500 flex items-center justify-center">
                  <span class="text-white font-bold text-sm">B</span>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm">B站</p>
                  <p class="text-xs text-gray-400">bilibili</p>
                </div>
              </div>
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">已选择 {{ selectedPlatforms.length }} 个平台</p>
        </div>

        <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-sm text-blue-700">
            <span class="font-semibold">提示：</span>
            请确保您已在 Chrome 中登录小红书和抖音账号。系统将依次打开创作者平台发布页面并自动上传视频。
          </p>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            视频文件
          </label>
          <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-xhs-red transition-colors">
            <input
              type="file"
              accept="video/*"
              @change="handleFileSelect"
              class="hidden"
              ref="fileInput"
            />
            <div v-if="!selectedFile" class="cursor-pointer" @click="triggerFileInput">
              <svg class="w-12 h-12 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p class="text-gray-500">点击选择视频文件</p>
              <p class="text-xs text-gray-400 mt-1">支持 MP4, MOV, AVI 等格式</p>
            </div>
            <div v-else class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div class="text-left">
                  <p class="text-sm font-medium text-gray-700">{{ selectedFile.name }}</p>
                  <p class="text-xs text-gray-400">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
              </div>
              <button
                @click.stop="selectedFile = null"
                class="text-gray-400 hover:text-red-500"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            标题（可选）
          </label>
          <input
            v-model="title"
            type="text"
            :placeholder="'输入视频标题'"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent"
          />
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            描述（可选）
          </label>
          <textarea
            v-model="description"
            rows="3"
            placeholder="输入视频描述"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent"
          ></textarea>
        </div>

        <button
          @click="handleUpload"
          :disabled="uploading || !selectedFile || selectedPlatforms.length === 0"
          :class="[
            'w-full py-3 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg text-white',
            'bg-gradient-to-r from-xhs-red to-pink-500 hover:from-red-600 hover:to-pink-600'
          ]"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </button>

        <p v-if="error" class="text-red-500 mt-4 text-center">{{ error }}</p>
      </div>

      <div v-if="success" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
        <p class="font-medium">成功！</p>
        <p class="text-sm mt-1">{{ success }}</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">上传说明</h3>
        <ul class="space-y-2 text-sm text-gray-600">
          <li class="flex items-start gap-2">
            <span class="text-xhs-red font-bold">1.</span>
            <span>请确保已安装并启动 Chrome 浏览器</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-xhs-red font-bold">2.</span>
            <span>系统将依次打开已选平台的创作者平台发布页面</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-xhs-red font-bold">3.</span>
            <span>视频将自动上传并填写标题</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-xhs-red font-bold">4.</span>
            <span>请在浏览器中确认上传状态并完成发布</span>
          </li>
        </ul>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { xhsApi } from '../api/xhs'

const checkingChrome = ref(true)
const chromeStarted = ref(false)
const startingChrome = ref(false)
const chromeError = ref('')
const fileInput = ref(null)
const selectedFile = ref(null)
const title = ref('')
const description = ref('')
const selectedPlatforms = ref(['xiaohongshu', 'douyin', 'kuaishou', 'baijiahao', 'bilibili'])
const uploading = ref(false)
const uploadingPlatforms = ref([])
const error = ref('')
const success = ref('')

const startChrome = async () => {
  startingChrome.value = true
  chromeError.value = ''

  try {
    const res = await xhsApi.startChrome()
    if (res.success) {
      chromeStarted.value = true
    } else {
      chromeError.value = res.error || '启动 Chrome 失败'
    }
  } catch (e) {
    chromeError.value = e.message || '网络错误'
  } finally {
    startingChrome.value = false
  }
}

const checkChromeStatus = async () => {
  try {
    const res = await xhsApi.checkChrome()
    chromeStarted.value = res.data?.running || false
  } catch (e) {
    chromeStarted.value = false
  } finally {
    checkingChrome.value = false
  }
}

const togglePlatform = (p) => {
  const idx = selectedPlatforms.value.indexOf(p)
  if (idx === -1) {
    selectedPlatforms.value.push(p)
  } else {
    selectedPlatforms.value.splice(idx, 1)
  }
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    error.value = '请选择视频文件'
    return
  }

  if (selectedPlatforms.value.length === 0) {
    error.value = '请选择至少一个平台'
    return
  }

  uploading.value = true
  error.value = ''
  success.value = ''
  
  const platformNames = {
    'xiaohongshu': '小红书',
    'douyin': '抖音',
    'kuaishou': '快手',
    'baijiahao': '百家号',
    'bilibili': 'B站',
    'weixin_video': '视频号'
  }
  
  const results = []
  
  for (const p of selectedPlatforms.value) {
    uploadingPlatforms.value = [platformNames[p] || p]
    
    try {
      const formData = new FormData()
      formData.append('video', selectedFile.value)
      formData.append('title', title.value)
      formData.append('description', description.value)
      formData.append('platform', p)

      const res = await fetch('/api/upload-video', {
        method: 'POST',
        body: formData,
      })
      const json = await res.json()
      
      if (json.success) {
        results.push(platformNames[p] || p)
      } else {
        error.value = `${platformNames[p] || p}: ${json.error || '上传失败'}`
      }
    } catch (e) {
      error.value = `${platformNames[p] || p}: ${e.message || '网络错误'}`
    }
  }
  
  uploadingPlatforms.value = []
  
  if (results.length > 0) {
    success.value = `已在 ${results.join(', ')} 打开创作者平台，视频上传进行中，请在浏览器中确认上传状态`
    selectedFile.value = null
  }
  
  uploading.value = false
}

onMounted(() => {
  checkChromeStatus()
})
</script>

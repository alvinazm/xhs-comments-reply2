<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-xhs-red">小红书评论获取</h1>
        <button
          @click="showSettings = true"
          class="flex items-center gap-2 text-gray-600 hover:text-gray-800"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>设置</span>
        </button>
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
          <p class="text-gray-500 mb-6">点击下方按钮启动 Chrome 并打开小红书，请手动登录</p>
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
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            小红书链接
          </label>
          <input
            v-model="url"
            type="text"
            placeholder="https://xiaohongshu.com/explore/xxxxxxxx?xsec_token=xxxxxx"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent"
          />
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            最大评论数
          </label>
          <input
            v-model.number="maxComments"
            type="number"
            min="1"
            max="100"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent"
          />
        </div>

        <button
          @click="fetchComments"
          :disabled="loading"
          class="w-full bg-xhs-red text-white py-2 px-4 rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ loading ? '获取中...' : '获取评论' }}
        </button>
      </div>

      <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center justify-between">
        <span>{{ error }}</span>
        <button
          @click="fetchComments"
          class="ml-4 text-sm bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
        >
          重试
        </button>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6 mt-6">
        <h2 class="text-xl font-bold mb-6">导出历史</h2>
        
        <div v-if="exportStore.state.tasks.length === 0" class="text-center py-8 text-gray-500">
          暂无导出记录
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="task in exportStore.state.tasks"
            :key="task.task_id"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <span 
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="{
                    'bg-yellow-100 text-yellow-700': task.status === 'pending',
                    'bg-blue-100 text-blue-700': task.status === 'running',
                    'bg-green-100 text-green-700': task.status === 'completed',
                    'bg-red-100 text-red-700': task.status === 'failed',
                  }"
                >
                  {{ task.status === 'completed' ? '已完成' : task.status === 'running' ? '获取中' : task.status === 'failed' ? '获取失败' : '等待中' }}
                </span>
                <span v-if="task.status === 'running'" class="text-xs text-gray-400">
                  获取进度: {{ task.progress }}%
                </span>
                <span v-else-if="task.note_title" class="text-sm font-medium text-gray-800">
                  {{ task.note_title }}
                </span>
                <span class="text-sm text-gray-500">
                  {{ formatTime(task.created_at) }}
                </span>
                <span v-if="task.comment_count" class="text-xs text-gray-400">
                  共 {{ task.comment_count }} 条评论
                </span>
              </div>

              <div v-if="task.status === 'running'" class="mt-2">
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    class="bg-blue-500 h-2 rounded-full transition-all"
                    :style="{ width: task.progress + '%' }"
                  ></div>
                </div>
                <p class="text-xs text-gray-500 mt-1">
                  已获取 {{ task.total_fetched }} 条评论
                </p>
              </div>

              <div class="flex gap-2">
                <button
                  v-if="task.status === 'completed'"
                  @click="downloadTask(task.task_id)"
                  class="bg-green-500 text-white py-1 px-3 rounded-lg hover:bg-green-600 text-sm"
                >
                  下载CSV
                </button>
                <button
                  v-if="task.status === 'completed' && task.classification_status === 'none'"
                  @click="handleClassify(task)"
                  class="bg-purple-500 text-white py-1 px-3 rounded-lg hover:bg-purple-600 text-sm"
                >
                  AI智能分类
                </button>
                <button
                  v-if="task.status === 'completed' && task.classification_status === 'completed'"
                  @click="downloadClassified(task)"
                  class="bg-blue-500 text-white py-1 px-3 rounded-lg hover:bg-blue-600 text-sm"
                >
                  下载分类CSV
                </button>
              </div>
            </div>
            
            <p class="text-xs text-blue-500 hover:underline cursor-pointer mb-1" @click="openUrl(task.url)">
              {{ task.url }}
            </p>
            
            <p v-if="task.status === 'completed'" class="text-sm text-gray-600">
              已获取 {{ task.total_fetched }} 条评论
            </p>

            <div v-if="task.classification_status === 'running'" class="mt-2">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-purple-600">AI分类中...</span>
                <span class="text-gray-500">{{ task.classification_progress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div 
                  class="bg-purple-500 h-2 rounded-full transition-all"
                  :style="{ width: task.classification_progress + '%' }"
                ></div>
              </div>
            </div>

            <div v-if="task.classification_status === 'completed'" class="mt-2">
              <div class="inline-flex items-center gap-2 px-3 py-1 bg-purple-50 rounded-full">
                <span class="text-sm text-purple-700">AI分类完成:</span>
                <span class="text-xs text-gray-600">
                  正面: {{ task.classification_summary?.praise || 0 }},
                  问题: {{ task.classification_summary?.question || 0 }},
                  中性: {{ task.classification_summary?.neutral || 0 }},
                  建设性: {{ task.classification_summary?.constructive || 0 }},
                  垃圾: {{ task.classification_summary?.spam || 0 }},
                  攻击性: {{ task.classification_summary?.hate || 0 }}
                </span>
              </div>

              <div class="mt-3 flex gap-2 flex-wrap">
                <span class="text-sm text-gray-500">回复:</span>
                <div v-if="replyProgress[task.task_id]?.completed" class="flex items-center gap-2">
                  <span class="text-sm text-green-600 bg-green-50 px-3 py-1 rounded">
                    已完成
                  </span>
                </div>
                <div v-else class="flex gap-2">
                  <label 
                    v-if="!replyData[task.task_id]?.fileName"
                    class="cursor-pointer bg-blue-500 text-white py-1 px-3 rounded-lg hover:bg-blue-600 text-sm"
                  >
                    上传CSV回复
                    <input
                      type="file"
                      accept=".csv"
                      class="hidden"
                      @change="(e) => handleCsvUpload(e, task)"
                    />
                  </label>
                  <div v-if="replyData[task.task_id]?.fileName" class="flex items-center gap-2">
                    <span class="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded">
                      {{ replyData[task.task_id].fileName }}
                    </span>
                    <button
                      @click="() => removeUploadedFile(task.task_id)"
                      class="text-red-500 hover:text-red-700 text-sm"
                    >
                      删除
                    </button>
                  </div>
                  <button
                    v-if="task.classification_status === 'completed'"
                    @click="() => directReply(task)"
                    class="bg-purple-500 text-white py-1 px-3 rounded-lg hover:bg-purple-600 text-sm"
                  >
                    直接回复
                  </button>
                </div>
              </div>

              <div v-if="replyData[task.task_id]?.to_reply > 0" class="mt-3 bg-green-50 border border-green-200 rounded-lg p-3">
                <div v-if="replyProgress[task.task_id]?.completed">
                  <p class="text-sm text-green-700">
                    成功回复 {{ replyProgress[task.task_id].sended }} 条
                  </p>
                </div>
                <div v-else>
                  <p class="text-sm text-green-700 mb-2">
                    确认发送 {{ replyData[task.task_id].to_reply }} 条回复？
                  </p>
                  <button
                    @click="() => confirmReply(task)"
                    :disabled="replyProgress[task.task_id]?.running"
                    class="bg-green-500 text-white py-1 px-3 rounded-lg hover:bg-green-600 text-sm disabled:opacity-50"
                  >
                    确认发送
                  </button>
                </div>
              </div>

              <div v-if="replyProgress[task.task_id]?.running" class="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p class="text-sm text-blue-700">
                  正在发送 {{ replyProgress[task.task_id].current }}/{{ replyProgress[task.task_id].total }}
                </p>
                <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    class="bg-blue-500 h-2 rounded-full"
                    :style="{ width: (replyProgress[task.task_id].current / replyProgress[task.task_id].total * 100) + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <div v-if="showReplyModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-bold mb-4">回复评论</h3>
        
        <div v-if="replyTarget" class="mb-4 p-3 bg-gray-50 rounded-lg text-sm">
          <p class="text-gray-600">回复: {{ replyTarget.user.nickname }}</p>
          <p class="text-gray-800 mt-1">{{ replyTarget.content }}</p>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            回复内容
          </label>
          <textarea
            v-model="replyContent"
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent"
            placeholder="输入回复内容..."
          ></textarea>
        </div>

        <div class="flex gap-3">
          <button
            @click="submitReply"
            :disabled="replying"
            class="flex-1 bg-xhs-red text-white py-2 px-4 rounded-lg hover:bg-red-600 disabled:opacity-50"
          >
            {{ replying ? '发送中...' : '发送' }}
          </button>
          <button
            @click="closeReplyModal"
            class="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSettings" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-bold mb-4">设置</h3>
        
        <div class="mb-4 border-b border-gray-200">
          <nav class="flex gap-4">
            <button
              v-for="tab in ['prompt', 'api', 'whitelist']"
              :key="tab"
              @click="activeSettingsTab = tab"
              class="pb-2 px-1 text-sm font-medium transition-colors border-b-2"
              :class="activeSettingsTab === tab ? 'border-xhs-red text-xhs-red' : 'border-transparent text-gray-500 hover:text-gray-700'"
            >
              {{ tab === 'prompt' ? '提示词设置' : tab === 'api' ? 'MiniMax API 配置' : '白名单设置' }}
            </button>
          </nav>
        </div>
        
        <div v-if="activeSettingsTab === 'prompt'" class="space-y-4">
          <div>
            <h4 class="text-md font-semibold mb-2 text-gray-800">分类标准 <span class="text-red-500">*</span></h4>
            <p class="text-xs text-gray-500 mb-2">定义评论分类类别和描述</p>
            <div class="space-y-2">
              <div v-for="(rule, index) in promptConfig.classificationRules" :key="index" class="flex gap-2 items-center">
                <input
                  v-model="rule.category"
                  type="text"
                  class="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent font-mono text-sm"
                  placeholder="praise"
                />
                <input
                  v-model="rule.description"
                  type="text"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent text-sm"
                  placeholder="正面反馈、赞美、感谢"
                />
                <button
                  v-if="promptConfig.classificationRules.length > 1"
                  @click="removeClassificationRule(index)"
                  class="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <button
                @click="addClassificationRule"
                class="flex items-center gap-1 text-sm text-blue-500 hover:text-blue-600"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                添加分类
              </button>
            </div>
          </div>
          
          <div>
            <h4 class="text-md font-semibold mb-2 text-gray-800">置信度规则 <span class="text-red-500">*</span></h4>
            <p class="text-xs text-gray-500 mb-2">配置置信度分数区间和对应描述</p>
            <div class="space-y-2">
              <div v-for="(rule, index) in promptConfig.confidenceRules" :key="index" class="flex gap-2 items-center">
                <input
                  v-model="rule.range"
                  type="text"
                  class="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent font-mono text-sm"
                  placeholder="85-100"
                />
                <input
                  v-model="rule.description"
                  type="text"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent text-sm"
                  placeholder="分类明确"
                />
                <button
                  v-if="promptConfig.confidenceRules.length > 1"
                  @click="removeConfidenceRule(index)"
                  class="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <button
                @click="addConfidenceRule"
                class="flex items-center gap-1 text-sm text-blue-500 hover:text-blue-600"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                添加规则
              </button>
            </div>
          </div>
          
          <div>
            <h4 class="text-md font-semibold mb-2 text-gray-800">回复视角 <span class="text-red-500">*</span></h4>
            <p class="text-xs text-gray-500 mb-2">以博主或第三方视角生成回复</p>
            <textarea
              v-model="promptConfig.systemPrompt"
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent text-sm"
              placeholder="以博主的身份生成回复内容，当评论为索要资料时，回复..."
            ></textarea>
          </div>
          
          <div>
            <h4 class="text-md font-semibold mb-2 text-gray-800">回复策略 <span class="text-red-500">*</span></h4>
            <p class="text-xs text-gray-500 mb-2">设置每个分类的回复动作（根据分类标准自动更新）</p>
            <div class="space-y-2">
              <div v-for="(action, category) in promptConfig.replyStrategy" :key="category" class="flex items-center gap-4 p-2 bg-gray-50 rounded-lg">
                <span class="w-24 text-sm font-medium text-gray-700">{{ category }}</span>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    :name="'reply-action-' + category"
                    value="reply"
                    v-model="promptConfig.replyStrategy[category]"
                    class="w-4 h-4 text-xhs-red focus:ring-xhs-red"
                  />
                  <span class="text-sm text-gray-600">回复</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    :name="'reply-action-' + category"
                    value="ignore"
                    v-model="promptConfig.replyStrategy[category]"
                    class="w-4 h-4 text-xhs-red focus:ring-xhs-red"
                  />
                  <span class="text-sm text-gray-600">忽略</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p class="text-xs text-blue-700 mb-1 font-medium">预览：完整提示词</p>
            <pre class="text-xs text-blue-800 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto">{{ assembledPrompt }}</pre>
          </div>
          
          <button
            @click="savePromptSettings"
            :disabled="savingPrompt"
            class="w-full bg-xhs-red text-white py-2 px-4 rounded-lg hover:bg-red-600 disabled:opacity-50"
          >
            {{ savingPrompt ? '保存中...' : '保存提示词设置' }}
          </button>
        </div>
        
        <div v-if="activeSettingsTab === 'api'" class="space-y-4">
          <div>
            <h4 class="text-md font-semibold mb-3 text-gray-800">MiniMax API 配置</h4>
            
            <div class="mb-3">
              <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                v-model="minimaxApiKey"
                type="password"
                rows="4"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent font-mono text-sm"
                placeholder="sk-cp-xxxxxxxx"
              />
            </div>
            
            <div class="mb-3">
              <label class="block text-sm font-medium text-gray-700 mb-1">API 地址</label>
              <div class="w-full px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg font-mono text-sm text-gray-600">
                {{ minimaxBaseUrl || 'https://api.minimaxi.com/v1' }}
              </div>
            </div>
            
            <p class="text-xs text-gray-500 mb-3">
              获取 API Key: <a href="https://platform.minimaxi.com/user-center/basic-information/interface-key" target="_blank" class="text-blue-500 hover:underline">https://platform.minimaxi.com</a>
            </p>
            
            <button
              @click="saveConfig"
              :disabled="savingConfig"
              class="w-full bg-xhs-red text-white py-2 px-4 rounded-lg hover:bg-red-600 disabled:opacity-50"
            >
              {{ savingConfig ? '保存中...' : '保存 API 配置' }}
            </button>
          </div>
        </div>
        
        <div v-if="activeSettingsTab === 'whitelist'" class="space-y-4">
          <div>
            <h4 class="text-md font-semibold mb-3 text-gray-800">白名单设置</h4>
            
            <p class="text-sm text-gray-600 mb-3">请输入要排除的用户ID，每行一个：</p>
            
            <textarea
              v-model="whitelistInput"
              rows="8"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-xhs-red focus:border-transparent font-mono text-sm"
              placeholder="user_id_1
user_id_2
user_id_3"
            ></textarea>

            <p class="text-xs text-gray-500 mt-2">白名单用户的评论不会被保存到CSV中</p>
            
            <button
              @click="saveWhitelist"
              :disabled="savingWhitelist"
              class="w-full bg-xhs-red text-white py-2 px-4 rounded-lg hover:bg-red-600 disabled:opacity-50 mt-3"
            >
              {{ savingWhitelist ? '保存中...' : '保存白名单' }}
            </button>
          </div>
        </div>
        
        <div class="flex gap-3 mt-4">
          <button
            @click="showSettings = false"
            class="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { xhsApi } from '../api/xhs'
import { useExportStore } from '../stores/export'

const router = useRouter()
const exportStore = useExportStore()

const chromeStarted = ref(false)
const checkingChrome = ref(true)
const startingChrome = ref(false)
const chromeError = ref('')
const url = ref('')
const maxComments = ref(20)
const loading = ref(false)
const replying = ref(false)
const error = ref('')
const note = ref(null)
const comments = ref([])
const totalComments = ref(0)
const displayedCount = 5
const showReplyModal = ref(false)
const replyTarget = ref(null)
const replyContent = ref('')
const replyData = ref({})
const replyProgress = ref({})
let replyInterval = null
const showSettings = ref(false)
const whitelistInput = ref('')
const savingWhitelist = ref(false)
const minimaxApiKey = ref('')
const minimaxBaseUrl = ref('')
const savingConfig = ref(false)
const activeSettingsTab = ref('prompt')
const savingPrompt = ref(false)

const defaultOutputFormat = `返回纯JSON数组，无任何额外文本。
\`\`\`json
[
  {
    "id": "c0",
    "category": "praise|question|neutral|constructive|spam|hate",
    "confidence": 85,
    "reason": "简要原因（中文）",
    "action": "回复|忽略",
    "generated_reply": "建议的回复内容（如需回复），中文，不超过50字。如果action为"忽略"，则generated_reply为空字符串"
  }
]
\`\`\`

**重要：generated_reply字段必须始终存在**：
- 当action="回复"时，generated_reply应包含具体的回复内容（中文，不超过50字）
- 当action="忽略"时，generated_reply为空字符串""`

const defaultClassificationCriteria = `- praise: 正面反馈、赞美、感谢
- question: 提问、询问信息
- neutral: 通用反应（笑哈哈、哇）、仅表情包
- constructive: 建设性批评、建议、详细反馈
- spam: 推广链接、垃圾信息、机器人重复内容
- hate: 仇恨、侮辱、威胁、攻击性言论`

const defaultClassificationRules = [
  { category: 'praise', description: '正面反馈、赞美、感谢' },
  { category: 'question', description: '提问、询问信息' },
  { category: 'neutral', description: '通用反应（笑哈哈、哇）、仅表情包' },
  { category: 'constructive', description: '建设性批评、建议、详细反馈' },
  { category: 'spam', description: '推广链接、垃圾信息、机器人重复内容' },
  { category: 'hate', description: '仇恨、侮辱、威胁、攻击性言论' },
]

const defaultConfidenceRules = [
  { range: '85-100', description: '分类明确' },
  { range: '60-84', description: '较确定，可能有歧义' },
  { range: '0-59', description: '存在歧义，选择最可能的类别' },
]

const defaultReplyStrategy = {
  praise: 'reply',
  question: 'reply',
  neutral: 'ignore',
  constructive: 'reply',
  spam: 'ignore',
  hate: 'ignore',
}

const promptConfig = ref({
  classificationCriteria: defaultClassificationCriteria,
  classificationRules: JSON.parse(JSON.stringify(defaultClassificationRules)),
  confidenceRules: JSON.parse(JSON.stringify(defaultConfidenceRules)),
  replyStrategy: { ...defaultReplyStrategy },
  systemPrompt: '',
})

const displayedComments = computed(() => {
  return comments.value.slice(0, displayedCount)
})

const assembledPrompt = computed(() => {
  const systemPrompt = promptConfig.value.systemPrompt.trim()
  
  const criteriaLines = promptConfig.value.classificationRules
    .filter(r => r.category && r.description)
    .map(r => `- ${r.category}: ${r.description}`)
    .join('\n')
  
  const categories = promptConfig.value.classificationRules
    .filter(r => r.category)
    .map(r => r.category)
    .join('|')
  
  const rules = promptConfig.value.confidenceRules
  const strategy = promptConfig.value.replyStrategy
  
  const strategyLines = Object.entries(strategy)
    .filter(([cat]) => categories.includes(cat))
    .map(([cat, action]) => `- ${cat} → action: "${action === 'reply' ? '回复' : '忽略'}"`)
    .join('\n')
  
  const rulesLines = rules
    .filter(r => r.range && r.description)
    .map(r => `- ${r.range}: ${r.description}`)
    .join('\n')
  
  const outputFormatJson = `[
  {
    "id": "c0",
    "category": "${categories || 'category'}",
    "confidence": 85,
    "reason": "简要原因（中文）",
    "action": "回复|忽略",
    "generated_reply": "建议的回复内容（如需回复），中文，不超过50字。如果action为"忽略"，则generated_reply为空字符串"
  }
]`
  
  return `你是一个评论分类及自动生成回复器。将每条评论分类到以下类别：

**分类标准：**
${criteriaLines}

**输出格式：** 返回纯JSON数组，无任何额外文本。
\`\`\`json
${outputFormatJson}
\`\`\`

**重要：generated_reply字段必须始终存在**：
- 当action="回复"时，generated_reply应包含具体的回复内容（中文，不超过250个字）
- 当action="忽略"时，generated_reply为空字符串""

**置信度规则：**
${rulesLines}

**重要：回复视角**
${systemPrompt}

**回复策略：**
${strategyLines}

只返回JSON数组，不要markdown格式，不要解释。`
})

const addConfidenceRule = () => {
  promptConfig.value.confidenceRules.push({ range: '', description: '' })
}

const removeConfidenceRule = (index) => {
  promptConfig.value.confidenceRules.splice(index, 1)
}

const addClassificationRule = () => {
  promptConfig.value.classificationRules.push({ category: '', description: '' })
}

const removeClassificationRule = (index) => {
  promptConfig.value.classificationRules.splice(index, 1)
}

const goToExportHistory = async () => {
  if (!url.value) {
    error.value = '请先输入小红书链接'
    return
  }
  
  try {
    await xhsApi.exportCommentsAsync(url.value, maxComments.value)
    exportStore.startPolling()
    router.push('/export-history')
  } catch (e) {
    error.value = e.message || '启动导出失败'
  }
}

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

const fetchComments = async () => {
  if (!url.value) {
    error.value = '请输入小红书链接'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const res = await xhsApi.getComments(url.value, maxComments.value)
    if (res.success) {
      note.value = res.data.note
      comments.value = res.data.comments
      totalComments.value = res.data.total_comments
      await exportStore.fetchTasks()
    } else {
      error.value = res.error || '获取评论失败'
    }
  } catch (e) {
    error.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const openReplyModal = (comment) => {
  replyTarget.value = comment
  showReplyModal.value = true
}

const closeReplyModal = () => {
  showReplyModal.value = false
  replyTarget.value = null
  replyContent.value = ''
}

const submitReply = async () => {
  if (!replyContent.value) {
    error.value = '请输入回复内容'
    return
  }

  replying.value = true
  error.value = ''

  try {
    const res = await xhsApi.replyComment(
      url.value,
      replyContent.value,
      replyTarget.value?.id || '',
      replyTarget.value?.user?.user_id || ''
    )
    if (res.success) {
      closeReplyModal()
    } else {
      error.value = res.error || '回复失败'
    }
  } catch (e) {
    error.value = e.message || '网络错误'
  } finally {
    replying.value = false
  }
}

const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const classificationPollInterval = ref(null)

const handleClassify = async (task) => {
  if (classificationPollInterval.value) {
    clearInterval(classificationPollInterval.value)
  }
  try {
    await xhsApi.startClassify(task.task_id)
    await exportStore.fetchTasks()
    pollClassificationStatus(task.task_id)
  } catch (e) {
    console.error('分类失败', e)
    alert(`分类失败: ${e.message}`)
    await exportStore.fetchTasks()
  }
}

const pollClassificationStatus = async (taskId) => {
  let attempts = 0
  classificationPollInterval.value = setInterval(async () => {
    attempts++
    if (attempts >= 150) {
      clearInterval(classificationPollInterval.value)
      return
    }
    try {
      const res = await xhsApi.getClassificationStatus(taskId)
      const data = res.data.data
      if (data.classification_status === 'completed' || data.classification_status === 'failed') {
        clearInterval(classificationPollInterval.value)
        await exportStore.fetchTasks()
      }
    } catch (e) {
      console.error('获取分类状态失败', e)
    }
  }, 2000)
}

const downloadClassified = async (task) => {
  try {
    const res = await xhsApi.downloadClassifiedFile(task.task_id)
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.download = `classified_${task.task_id.slice(0, 8)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载失败', e)
  }
}

onMounted(() => {
  checkChromeStatus()
  exportStore.fetchTasks()
  exportStore.startPolling()
})

onUnmounted(() => {
  if (replyInterval) clearInterval(replyInterval)
  exportStore.stopPolling()
})

const downloadTask = async (taskId) => {
  try {
    const response = await fetch(`/api/export-download/${taskId}`)
    const contentType = response.headers.get('content-type') || ''
    if (response.ok && contentType.includes('text/csv')) {
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `comments_${taskId.slice(0, 8)}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
    }
  } catch (e) {
    console.error('下载失败', e)
  }
}

const openUrl = (url) => {
  window.open(url, '_blank')
}

const handleCsvUpload = async (event, task) => {
  const file = event.target.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch('/api/reply-from-csv', {
      method: 'POST',
      body: formData,
    })
    const json = await res.json()
    if (json.success) {
      replyData.value = { ...replyData.value, [task.task_id]: { ...json.data, fileName: file.name } }
    } else {
      alert(json.error || '上传失败')
    }
  } catch (e) {
    alert(`上传失败: ${e.message}`)
  }
  event.target.value = ''
}

const removeUploadedFile = (taskId) => {
  const newReplyData = { ...replyData.value }
  delete newReplyData[taskId]
  replyData.value = newReplyData
}

const confirmReply = async (task) => {
  const data = replyData.value[task.task_id]
  if (!data || data.to_reply === 0) return

  try {
    await fetch('/api/reply-confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: task.url,
        comments: data.comments,
      }),
    })
    replyProgress.value = {
      ...replyProgress.value,
      [task.task_id]: { running: true, current: 0, total: data.to_reply, sended: 0, completed: false },
    }
    pollReplyStatus(task.task_id)
  } catch (e) {
    alert(`发送失败: ${e.message}`)
  }
}

const directReply = async (task) => {
  try {
    const res = await fetch('/api/reply-direct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: task.task_id }),
    })
    const json = await res.json()
    if (json.success) {
      replyData.value = {
        ...replyData.value,
        [task.task_id]: { to_reply: json.data.to_reply, fileName: 'AI分类回复' },
      }
      replyProgress.value = {
        ...replyProgress.value,
        [task.task_id]: { running: true, current: 0, total: json.data.to_reply, sended: 0, completed: false },
      }
      pollReplyStatus(task.task_id)
    } else {
      alert(json.error || '直接回复失败')
    }
  } catch (e) {
    alert(`直接回复失败: ${e.message}`)
  }
}

const pollReplyStatus = (taskId) => {
  if (replyInterval) clearInterval(replyInterval)

  replyInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/reply-status')
      const json = await res.json()
      if (json.success) {
        const status = json.data
        replyProgress.value = {
          ...replyProgress.value,
          [taskId]: {
            current: status.current,
            total: status.total,
            sended: status.sended,
            failed: status.failed,
            running: status.running,
            completed: !status.running,
          },
        }
        if (!status.running) {
          clearInterval(replyInterval)
          replyInterval = null
        }
      }
    } catch (e) {
      console.error('查询状态失败', e)
    }
  }, 2000)
}

const loadWhitelist = async () => {
  try {
    const res = await xhsApi.getWhitelist()
    if (res.success) {
      whitelistInput.value = (res.data.user_ids || []).join('\n')
    }
  } catch (e) {
    console.error('加载白名单失败', e)
  }
}

const saveWhitelist = async () => {
  savingWhitelist.value = true
  try {
    const userIds = whitelistInput.value
      .split('\n')
      .map(s => s.trim())
      .filter(s => s)
    
    await xhsApi.saveWhitelist(userIds)
    showSettings.value = false
    alert('白名单已保存')
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    savingWhitelist.value = false
  }
}

const loadConfig = async () => {
  try {
    const res = await xhsApi.getConfig()
    if (res.success) {
      minimaxApiKey.value = res.data.minimax_api_key || ''
      minimaxBaseUrl.value = res.data.minimax_base_url || 'https://api.minimaxi.com/v1'
    }
  } catch (e) {
    console.error('加载配置失败', e)
  }
}

const saveConfig = async () => {
  savingConfig.value = true
  try {
    await xhsApi.saveConfig({
      minimax_api_key: minimaxApiKey.value,
      minimax_base_url: minimaxBaseUrl.value,
    })
    alert('配置已保存')
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    savingConfig.value = false
  }
}

const parsePromptToStructuredData = (promptText) => {
  if (!promptText) return

  const systemPromptMatch = promptText.match(/\*\*重要：回复视角\*\*(.*?)(\*\*回复策略：\*\*)/s)
  if (systemPromptMatch) {
    promptConfig.value.systemPrompt = systemPromptMatch[1].trim()
  } else {
    promptConfig.value.systemPrompt = ''
  }

  const classificationRules = []
  const criteriaMatch = promptText.match(/\*\*分类标准：\*\*(.*?)(?=\*\*输出格式：\*\*|\n\n)/s)
  if (criteriaMatch) {
    const lines = criteriaMatch[1].trim().split('\n')
    lines.forEach(line => {
      const match = line.match(/^-\s*(\w+):\s*(.+)/)
      if (match) {
        classificationRules.push({ category: match[1], description: match[2] })
      }
    })
  }
  if (classificationRules.length > 0) {
    promptConfig.value.classificationRules = classificationRules
  }

  const confidenceRules = []
  const confMatch = promptText.match(/\*\*置信度规则：\*\*(.*?)\*\*/s)
  if (confMatch) {
    const lines = confMatch[1].trim().split('\n')
    lines.forEach(line => {
      const match = line.match(/^-\s*(\d+-\d+):\s*(.+)/)
      if (match) {
        confidenceRules.push({ range: match[1], description: match[2] })
      }
    })
  }
  if (confidenceRules.length > 0) {
    promptConfig.value.confidenceRules = confidenceRules
  }

  const replyStrategy = {}
  const strategyMatch = promptText.match(/\*\*回复策略：\*\*(.*?)(?=只返回JSON|$)/s)
  if (strategyMatch) {
    const lines = strategyMatch[1].trim().split('\n')
    lines.forEach(line => {
      const match = line.match(/^-\s*(\w+)\s*→\s*action:\s*"(.+?)"/)
      if (match) {
        replyStrategy[match[1]] = match[2] === '回复' ? 'reply' : 'ignore'
      }
    })
  }
  if (Object.keys(replyStrategy).length > 0) {
    promptConfig.value.replyStrategy = replyStrategy
  }
}

const loadPromptConfig = async () => {
  try {
    const res = await xhsApi.getPromptConfig()
    if (res.success && res.data && res.data.prompt_text) {
      parsePromptToStructuredData(res.data.prompt_text)
    }
  } catch (e) {
    console.error('加载提示词配置失败', e)
  }
}

const updateReplyStrategyFromCriteria = () => {
  const rules = promptConfig.value.classificationRules
  const currentCategories = rules.map(r => r.category).filter(c => c)
  
  const newStrategy = {}
  currentCategories.forEach(cat => {
    newStrategy[cat] = promptConfig.value.replyStrategy[cat] || 'reply'
  })
  
  promptConfig.value.replyStrategy = newStrategy
}

const savePromptSettings = async () => {
  if (!promptConfig.value.systemPrompt.trim()) {
    alert('回复视角不能为空')
    return
  }
  
  const hasEmptyCategory = promptConfig.value.classificationRules.some(r => !r.category.trim() || !r.description.trim())
  if (hasEmptyCategory) {
    alert('分类标准的类别和描述都不能为空')
    return
  }
  
  const hasEmptyRule = promptConfig.value.confidenceRules.some(r => !r.range.trim() || !r.description.trim())
  if (hasEmptyRule) {
    alert('置信度规则的分数区间和描述都不能为空')
    return
  }
  
  savingPrompt.value = true
  try {
    await xhsApi.savePromptConfig(assembledPrompt.value)
    alert('提示词配置已保存')
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    savingPrompt.value = false
  }
}

watch(() => promptConfig.value.classificationRules, () => {
  updateReplyStrategyFromCriteria()
}, { deep: true })

onMounted(() => {
  checkChromeStatus()
  exportStore.fetchTasks()
  exportStore.startPolling()
  loadWhitelist()
  loadConfig()
  loadPromptConfig()
})
</script>
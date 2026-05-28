<script setup lang="ts">
import {computed, nextTick, onMounted, ref, watch} from 'vue'
import {ElMessage} from 'element-plus'
import {Delete, Plus} from '@element-plus/icons-vue'
import {marked} from 'marked'
import {ChatStream} from '@/request/api'

marked.setOptions({
  breaks: true,
  gfm: true,
})

function renderMarkdown(text: string): string {
  return marked.parse(text) as string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Conversation {
  id: string
  title: string
  updatedAt: string
  messages: Message[]
}

const STORAGE_KEY = 'paper_search_chat_conversations'
const WELCOME_MESSAGE = '你好！我是学术论文助手，可以帮你解释论文、总结方向、扩展检索关键词，或者回答本系统的使用问题。'
const starterPrompts = [
  '帮我解释一下 query optimization 的核心目标',
  '推荐几个数据库系统研究方向关键词',
  '如何根据一篇论文继续扩展相关阅读？',
  '请总结一下 learned index 的基本思路',
]

function createConversation(): Conversation {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: '新对话',
    updatedAt: new Date().toISOString(),
    messages: [
      {
        role: 'assistant',
        content: WELCOME_MESSAGE,
      },
    ],
  }
}

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(item => item && typeof item.id === 'string' && Array.isArray(item.messages))
      .map((item): Conversation => ({
        id: item.id,
        title: typeof item.title === 'string' && item.title.trim() ? item.title : '新对话',
        updatedAt: typeof item.updatedAt === 'string' ? item.updatedAt : new Date().toISOString(),
        messages: item.messages
          .filter((msg: any) => (msg?.role === 'user' || msg?.role === 'assistant') && typeof msg?.content === 'string')
          .map((msg: any) => ({
            role: msg.role,
            content: msg.content,
          })),
      }))
      .filter(item => item.messages.length > 0)
  } catch {
    return []
  }
}

const conversations = ref<Conversation[]>([])
const activeConversationId = ref('')
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

const activeConversation = computed(() =>
  conversations.value.find(item => item.id === activeConversationId.value) || null,
)
const messages = computed(() => activeConversation.value?.messages || [])

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function persistConversations() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.value))
}

function moveConversationToTop(id: string) {
  const index = conversations.value.findIndex(item => item.id === id)
  if (index <= 0) return
  const [conversation] = conversations.value.splice(index, 1)
  conversations.value.unshift(conversation)
}

function touchConversation(conversation: Conversation, titleSeed?: string) {
  const userMessageCount = conversation.messages.filter(item => item.role === 'user').length
  if (titleSeed && userMessageCount <= 1) {
    conversation.title = titleSeed.replace(/\s+/g, ' ').trim().slice(0, 28) || '新对话'
  }
  conversation.updatedAt = new Date().toISOString()
  moveConversationToTop(conversation.id)
}

function ensureConversation() {
  if (activeConversation.value) return activeConversation.value
  const conversation = createConversation()
  conversations.value.unshift(conversation)
  activeConversationId.value = conversation.id
  return conversation
}

function startNewConversation() {
  if (loading.value) return
  const conversation = createConversation()
  conversations.value.unshift(conversation)
  activeConversationId.value = conversation.id
  inputText.value = ''
  scrollToBottom()
}

function selectConversation(id: string) {
  activeConversationId.value = id
  inputText.value = ''
  scrollToBottom()
}

function resetCurrentConversation() {
  if (loading.value) return
  const conversation = activeConversation.value
  if (!conversation) return
  conversation.title = '新对话'
  conversation.messages = [
    {
      role: 'assistant',
      content: WELCOME_MESSAGE,
    },
  ]
  touchConversation(conversation)
  scrollToBottom()
}

function deleteConversation(id: string) {
  if (loading.value) return
  const index = conversations.value.findIndex(item => item.id === id)
  if (index === -1) return
  conversations.value.splice(index, 1)
  if (activeConversationId.value === id) {
    if (conversations.value.length === 0) {
      const conversation = createConversation()
      conversations.value = [conversation]
      activeConversationId.value = conversation.id
    } else {
      activeConversationId.value = conversations.value[0].id
    }
  }
}

function fillPrompt(prompt: string) {
  inputText.value = prompt
}

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function getConversationPreview(conversation: Conversation) {
  const lastContent = [...conversation.messages]
    .reverse()
    .find(item => item.content.trim())
    ?.content
  return (lastContent || '点击继续这段对话').replace(/\s+/g, ' ').slice(0, 58)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  const conversation = ensureConversation()
  conversation.messages.push({role: 'user', content: text})
  touchConversation(conversation, text)
  inputText.value = ''
  scrollToBottom()

  conversation.messages.push({role: 'assistant', content: ''})
  loading.value = true
  scrollToBottom()

  const apiMessages = conversation.messages.slice(0, -1).map(item => ({
    role: item.role,
    content: item.content,
  }))

  try {
    await ChatStream(
      apiMessages,
      (chunk: string) => {
        conversation.messages[conversation.messages.length - 1].content += chunk
        if (conversation.id === activeConversationId.value) {
          scrollToBottom()
        }
      },
      () => {
        touchConversation(conversation)
        loading.value = false
        if (conversation.id === activeConversationId.value) {
          scrollToBottom()
        }
      },
    )
  } catch (_error) {
    conversation.messages[conversation.messages.length - 1].content = '抱歉，请求出错，请稍后重试。'
    touchConversation(conversation)
    loading.value = false
    ElMessage.error('发送失败')
  }
}

watch(conversations, () => {
  persistConversations()
}, {deep: true})

watch(activeConversationId, () => {
  scrollToBottom()
})

onMounted(() => {
  const savedConversations = loadConversations()
  if (savedConversations.length > 0) {
    savedConversations.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    conversations.value = savedConversations
    activeConversationId.value = savedConversations[0].id
  } else {
    const conversation = createConversation()
    conversations.value = [conversation]
    activeConversationId.value = conversation.id
  }
  scrollToBottom()
})
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <p class="page-eyebrow">AI Assistant</p>
      <h1 class="hero-title">保存会话的学术聊天助手</h1>
      <p class="hero-description">
        现在会按“经典聊天记录”形式在左侧保存会话列表，刷新页面或切换页面后仍能继续之前的对话。
      </p>
      <div class="prompt-tags">
        <el-tag
          v-for="prompt in starterPrompts"
          :key="prompt"
          effect="dark"
          class="prompt-tag"
          @click="fillPrompt(prompt)"
        >
          {{ prompt }}
        </el-tag>
      </div>
    </section>

    <section class="chat-layout">
      <aside class="page-card conversation-panel">
        <div class="conversation-header">
          <div>
            <h2 class="card-heading">聊天记录</h2>
            <p class="muted-text">当前浏览器会自动保存全部会话。</p>
          </div>
          <el-button type="primary" :icon="Plus" :disabled="loading" @click="startNewConversation">
            新建对话
          </el-button>
        </div>

        <div class="conversation-list">
          <div
            v-for="conversation in conversations"
            :key="conversation.id"
            class="conversation-item"
            :class="{ active: conversation.id === activeConversationId }"
            @click="selectConversation(conversation.id)"
          >
            <div class="conversation-top">
              <strong>{{ conversation.title }}</strong>
              <span>{{ formatTime(conversation.updatedAt) }}</span>
            </div>
            <p>{{ getConversationPreview(conversation) }}</p>
            <el-button
              text
              class="delete-btn"
              :icon="Delete"
              :disabled="loading"
              @click.stop="deleteConversation(conversation.id)"
            >
              删除
            </el-button>
          </div>
        </div>
      </aside>

      <section class="page-card chat-card">
        <div class="chat-toolbar">
          <div>
            <h2 class="card-heading">{{ activeConversation?.title || '新对话' }}</h2>
            <p class="muted-text">切换页面后返回，聊天内容仍会保留。</p>
          </div>
          <el-button plain :disabled="loading" @click="resetCurrentConversation">
            清空当前对话
          </el-button>
        </div>

        <div class="chat-messages" ref="chatContainer">
          <div v-for="(msg, idx) in messages" :key="idx" class="message-row" :class="msg.role">
            <div class="avatar" v-if="msg.role === 'assistant'">AI</div>
            <div class="bubble" :class="msg.role">
              <div
                class="markdown-body"
                v-if="msg.role === 'assistant' && msg.content"
                v-html="renderMarkdown(msg.content)"
              ></div>
              <span class="bubble-text" v-else-if="msg.content">{{ msg.content }}</span>
              <span class="typing-indicator" v-else-if="loading && idx === messages.length - 1">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              </span>
            </div>
            <div class="avatar user-avatar" v-if="msg.role === 'user'">我</div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea
            v-model="inputText"
            class="chat-input"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            :disabled="loading"
            @keydown="handleKeydown"
            rows="1"
          />
          <button class="send-btn" :disabled="loading || !inputText.trim()" @click="sendMessage">
            <span v-if="loading" class="sending-icon">⏳</span>
            <span v-else>发送</span>
          </button>
        </div>
      </section>
    </section>
  </div>
</template>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
}

.prompt-tags {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.prompt-tag {
  cursor: pointer;
  border-color: rgba(255, 255, 255, 0.16);
}

.conversation-panel {
  display: flex;
  flex-direction: column;
  min-height: 720px;
}

.conversation-header {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
  overflow-y: auto;
}

.conversation-item {
  width: 100%;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.conversation-item:hover {
  transform: translateY(-2px);
  border-color: rgba(37, 99, 235, 0.24);
  box-shadow: 0 16px 28px rgba(37, 99, 235, 0.08);
}

.conversation-item.active {
  border-color: rgba(37, 99, 235, 0.34);
  background: linear-gradient(180deg, #eff6ff 0%, #f8fbff 100%);
  box-shadow: 0 16px 28px rgba(37, 99, 235, 0.12);
}

.conversation-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.conversation-top strong {
  font-size: 15px;
  color: #0f172a;
}

.conversation-top span {
  color: #64748b;
  font-size: 12px;
  flex-shrink: 0;
}

.conversation-item p {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #64748b;
}

.delete-btn {
  margin-top: 6px;
  padding-left: 0;
}

.chat-card {
  display: flex;
  flex-direction: column;
  min-height: 720px;
}

.chat-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  border-radius: 22px;
  background: linear-gradient(180deg, #f8fbff 0%, #f4f8ff 100%);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.message-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 10px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  background: #409eff;
  color: #fff;
}

.user-avatar {
  background: #22c55e;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.bubble.assistant {
  background: #fff;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-top-left-radius: 4px;
}

.bubble.user {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  border-top-right-radius: 4px;
  white-space: pre-wrap;
}

.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.chat-input {
  flex: 1;
  resize: none;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  font-family: inherit;
  min-height: 54px;
  max-height: 160px;
  overflow-y: auto;
  background: #fff;
}

.chat-input:focus {
  border-color: #2563eb;
}

.chat-input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.send-btn {
  min-width: 96px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  flex-shrink: 0;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.2);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
}

.bubble-text {
  white-space: pre-wrap;
}

.markdown-body :deep(p) {
  margin: 0 0 10px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  background: #eff6ff;
  padding: 2px 6px;
  border-radius: 6px;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 20px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: blink 1.4s infinite ease-in-out both;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@media (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .conversation-panel,
  .chat-card {
    min-height: auto;
  }
}

@keyframes blink {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>

<script setup lang="ts">
import {ref, nextTick, computed} from 'vue'
import {ChatStream} from '@/request/api'
import {ElMessage} from 'element-plus'
import {marked} from 'marked'

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

const messages = ref<Message[]>([
  {role: 'assistant', content: '你好！我是学术论文助手，可以回答学术问题或帮助你使用本系统。请问有什么可以帮你的？'}
])
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({role: 'user', content: text})
  inputText.value = ''
  scrollToBottom()

  // Add placeholder for assistant reply
  messages.value.push({role: 'assistant', content: ''})
  loading.value = true
  scrollToBottom()

  // Build message history for API (exclude the empty assistant placeholder)
  const apiMessages = messages.value.slice(0, -1).map(m => ({
    role: m.role,
    content: m.content,
  }))

  try {
    await ChatStream(
        apiMessages,
        (chunk: string) => {
          messages.value[messages.value.length - 1].content += chunk
          scrollToBottom()
        },
        () => {
          loading.value = false
          scrollToBottom()
        },
    )
  } catch (e) {
    console.error(e)
    messages.value[messages.value.length - 1].content = '抱歉，请求出错，请稍后重试。'
    loading.value = false
    ElMessage.error('发送失败')
  }
}
</script>

<template>
  <div class="chat-wrapper">
    <div class="chat-header">聊天助手</div>
    <div class="chat-messages" ref="chatContainer">
      <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="msg.role"
      >
        <div class="avatar" v-if="msg.role === 'assistant'">AI</div>
        <div class="bubble" :class="msg.role">
          <div class="markdown-body" v-if="msg.role === 'assistant' && msg.content" v-html="renderMarkdown(msg.content)"></div>
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
      <button
          class="send-btn"
          :disabled="loading || !inputText.trim()"
          @click="sendMessage"
      >
        <span v-if="loading" class="sending-icon">⏳</span>
        <span v-else>发送</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  max-width: 900px;
  margin: 0 auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
}

.chat-header {
  padding: 14px 20px;
  font-size: 16px;
  font-weight: 600;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  color: #303133;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
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
  background: #67c23a;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.bubble.user {
  white-space: pre-wrap;
}

.bubble.assistant {
  background: #fff;
  color: #303133;
  border: 1px solid #e4e7ed;
  border-top-left-radius: 4px;
}

.bubble.user {
  background: #409eff;
  color: #fff;
  border-top-right-radius: 4px;
}

.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
}

.chat-input {
  flex: 1;
  resize: none;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  font-family: inherit;
  min-height: 20px;
  max-height: 120px;
  overflow-y: auto;
}

.chat-input:focus {
  border-color: #409eff;
}

.chat-input:disabled {
  background: #f5f7fa;
  cursor: not-allowed;
}

.send-btn {
  padding: 10px 20px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.send-btn:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
  padding: 4px 0;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #909399;
  animation: bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* Markdown content styles */
.markdown-body {
  line-height: 1.6;
}

.markdown-body :deep(p) {
  margin: 0 0 8px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 4px 0 8px;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin-bottom: 2px;
}

.markdown-body :deep(code) {
  background: #f0f2f5;
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 13px;
  font-family: 'Courier New', Courier, monospace;
}

.markdown-body :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  font-size: 13px;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #409eff;
  margin: 8px 0;
  padding: 4px 12px;
  color: #606266;
  background: #f5f7fa;
  border-radius: 0 4px 4px 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 12px 0 6px;
  font-weight: 600;
}

.markdown-body :deep(h1) { font-size: 1.3em; }
.markdown-body :deep(h2) { font-size: 1.15em; }
.markdown-body :deep(h3) { font-size: 1.05em; }

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 6px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 10px 0;
}

.markdown-body :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}
</style>

<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {GetPaperDetail, ChatStream} from '@/request/api'
import {marked} from 'marked'

marked.setOptions({breaks: true, gfm: true})
function renderMarkdown(text: string): string {
  return marked.parse(text) as string
}

const route = useRoute()
const router = useRouter()
const paper = ref<any>(null)
const loading = ref(true)

const pdfBlobUrl = ref<string | null>(null)
const pdfLoading = ref(false)

const keywordList = computed(() =>
  String(paper.value?.keywords || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean),
)

// ---- Paper Q&A Chat ----
interface QAMessage {
  role: 'user' | 'assistant'
  content: string
}

const qaMessages = ref<QAMessage[]>([
  {role: 'assistant', content: '我已阅读了这篇论文的全文，你可以问我任何问题。'},
])
const qaInput = ref('')
const qaLoading = ref(false)
const qaContainer = ref<HTMLElement | null>(null)
const qaQuickPrompts = ['核心方法', '主要贡献', '局限性', '与哪些工作相关']

function qaScrollToBottom() {
  nextTick(() => {
    if (qaContainer.value) {
      qaContainer.value.scrollTop = qaContainer.value.scrollHeight
    }
  })
}

function qaHandleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendQAMessage()
  }
}

function fillQAPrompt(prompt: string) {
  qaInput.value = prompt
}

async function sendQAMessage() {
  const text = qaInput.value.trim()
  if (!text || qaLoading.value || !paper.value) return

  qaMessages.value.push({role: 'user', content: text})
  qaInput.value = ''
  qaScrollToBottom()

  qaMessages.value.push({role: 'assistant', content: ''})
  qaLoading.value = true
  qaScrollToBottom()

  const apiMessages = qaMessages.value.slice(0, -1).map(m => ({role: m.role, content: m.content}))

  try {
    await ChatStream(
      apiMessages,
      (chunk: string) => {
        qaMessages.value[qaMessages.value.length - 1].content += chunk
        qaScrollToBottom()
      },
      () => {
        qaLoading.value = false
        qaScrollToBottom()
      },
      {paperId: paper.value.id},
    )
  } catch (_error) {
    qaMessages.value[qaMessages.value.length - 1].content = '抱歉，请求出错，请稍后重试。'
    qaLoading.value = false
    ElMessage.error('发送失败')
  }
}

const loadPdf = async (paperId: number) => {
  pdfLoading.value = true
  try {
    const token = localStorage.getItem('token') || ''
    const resp = await fetch(`/api/papers/${paperId}/pdf`, {
      headers: {Authorization: `Bearer ${token}`},
    })
    if (resp.ok) {
      pdfBlobUrl.value = URL.createObjectURL(await resp.blob())
    }
  } catch (_e) {
    // silently fail — fallback UI will show
  } finally {
    pdfLoading.value = false
  }
}

onMounted(async () => {
  const paperId = Number(route.params.paperId)
  if (!paperId) {
    ElMessage.error('无效的论文ID')
    router.push('/index/paperSearch')
    return
  }
  try {
    paper.value = await GetPaperDetail(paperId)
    if (paper.value?.has_pdf) {
      loadPdf(paperId)
    }
  } catch (_error) {
    ElMessage.error('获取论文详情失败')
    router.push('/index/paperSearch')
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
  }
})
</script>

<template>
  <div class="page-shell" v-loading="loading">
    <section class="page-card detail-toolbar">
      <el-button text @click="router.push('/index/paperSearch')">← 返回搜索</el-button>
      <el-link v-if="paper?.url" :href="paper.url" target="_blank" rel="noopener" type="primary">
        打开原文链接
      </el-link>
    </section>

    <section v-if="paper" class="page-hero detail-hero">
      <p class="page-eyebrow">Paper Detail</p>
      <h1 class="hero-title">{{ paper.title }}</h1>
      <div class="detail-tags">
        <el-tag type="primary" effect="dark">作者：{{ paper.authors }}</el-tag>
        <el-tag v-for="kw in keywordList" :key="kw" effect="dark" class="keyword-tag">
          {{ kw }}
        </el-tag>
      </div>
    </section>

    <section v-if="paper" class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">论文信息</h2>
          <p class="muted-text">这里展示元数据和可跳转链接。</p>
        </div>
      </div>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="作者" :span="2">
          {{ paper.authors }}
        </el-descriptions-item>
        <el-descriptions-item label="会议/期刊">
          {{ paper.venue }}
        </el-descriptions-item>
        <el-descriptions-item label="年份">
          {{ paper.year }}
        </el-descriptions-item>
        <el-descriptions-item label="关键词" :span="2">
          {{ paper.keywords }}
        </el-descriptions-item>
        <el-descriptions-item label="链接" :span="2" v-if="paper.url">
          <a :href="paper.url" target="_blank" rel="noopener" class="paper-link">{{ paper.url }}</a>
        </el-descriptions-item>
      </el-descriptions>
    </section>

    <section v-if="paper" class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">摘要</h2>
          <p class="muted-text">已尽量使用更真实、更完整的论文摘要文本。</p>
        </div>
      </div>
      <p class="abstract-text">{{ paper.abstract }}</p>
    </section>

    <section v-if="paper" class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">论文全文</h2>
          <p class="muted-text">在线阅读 PDF 全文。</p>
        </div>
      </div>

      <div v-if="paper.has_pdf && pdfBlobUrl" class="pdf-viewer">
        <iframe :src="pdfBlobUrl" class="pdf-iframe" />
      </div>
      <div v-else-if="paper.has_pdf && pdfLoading" v-loading="true" class="pdf-placeholder">
        加载 PDF 中…
      </div>
      <div v-else class="pdf-fallback">
        <el-empty description="暂无本地 PDF">
          <template #description>
            <p>该论文暂未收录 PDF 全文。</p>
            <el-link
              v-if="paper.url"
              :href="paper.url"
              target="_blank"
              rel="noopener"
              type="primary"
            >
              前往原文链接查看
            </el-link>
          </template>
        </el-empty>
      </div>
    </section>

    <!-- Paper Q&A Chat -->
    <section v-if="paper" class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">AI 论文问答</h2>
          <p class="muted-text">基于论文全文内容的智能问答，可以问任何关于这篇论文的问题。</p>
        </div>
      </div>

      <div class="qa-quick-prompts">
        <el-tag
          v-for="prompt in qaQuickPrompts"
          :key="prompt"
          effect="plain"
          class="qa-prompt-tag"
          @click="fillQAPrompt(prompt)"
        >
          {{ prompt }}
        </el-tag>
      </div>

      <div class="qa-messages" ref="qaContainer">
        <div v-for="(msg, idx) in qaMessages" :key="idx" class="qa-message-row" :class="msg.role">
          <div class="qa-avatar" v-if="msg.role === 'assistant'">AI</div>
          <div class="qa-bubble" :class="msg.role">
            <div
              class="qa-markdown-body"
              v-if="msg.role === 'assistant' && msg.content"
              v-html="renderMarkdown(msg.content)"
            ></div>
            <span v-else-if="msg.content">{{ msg.content }}</span>
            <span class="qa-typing" v-else-if="qaLoading && idx === qaMessages.length - 1">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </span>
          </div>
          <div class="qa-avatar qa-user-avatar" v-if="msg.role === 'user'">我</div>
        </div>
      </div>

      <div class="qa-input-area">
        <textarea
          v-model="qaInput"
          class="qa-input"
          placeholder="问一个关于这篇论文的问题..."
          :disabled="qaLoading"
          @keydown="qaHandleKeydown"
          rows="1"
        />
        <button class="qa-send-btn" :disabled="qaLoading || !qaInput.trim()" @click="sendQAMessage">
          {{ qaLoading ? '...' : '发送' }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.detail-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 16px;
  padding-bottom: 16px;
}

.detail-tags {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.keyword-tag {
  border-color: rgba(255, 255, 255, 0.14);
}

.abstract-text {
  font-size: 15px;
  line-height: 1.8;
  color: #0f172a;
  text-align: justify;
  white-space: pre-wrap;
}

.pdf-viewer {
  margin-top: 12px;
}

.pdf-iframe {
  width: 100%;
  height: 80vh;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.pdf-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.pdf-fallback {
  margin-top: 12px;
}

/* Paper Q&A Chat */
.qa-quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.qa-prompt-tag {
  cursor: pointer;
  transition: background 0.2s;
}

.qa-prompt-tag:hover {
  background: #ecf5ff;
}

.qa-messages {
  max-height: 420px;
  overflow-y: auto;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #f4f8ff 100%);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.qa-message-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 8px;
}

.qa-message-row.user {
  justify-content: flex-end;
}

.qa-message-row.assistant {
  justify-content: flex-start;
}

.qa-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  background: #409eff;
  color: #fff;
}

.qa-user-avatar {
  background: #22c55e;
}

.qa-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.qa-bubble.assistant {
  background: #fff;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-top-left-radius: 4px;
}

.qa-bubble.user {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  border-top-right-radius: 4px;
  white-space: pre-wrap;
}

.qa-markdown-body :deep(p) {
  margin: 0 0 8px;
}

.qa-markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.qa-markdown-body :deep(code) {
  background: #eff6ff;
  padding: 2px 6px;
  border-radius: 6px;
}

.qa-input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.qa-input {
  flex: 1;
  resize: none;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  font-family: inherit;
  min-height: 48px;
  max-height: 120px;
  overflow-y: auto;
  background: #fff;
}

.qa-input:focus {
  border-color: #2563eb;
}

.qa-input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.qa-send-btn {
  min-width: 72px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}

.qa-send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.qa-send-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
}

.qa-typing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 18px;
}

.qa-typing .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #94a3b8;
  animation: qa-blink 1.4s infinite ease-in-out both;
}

.qa-typing .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.qa-typing .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes qa-blink {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>

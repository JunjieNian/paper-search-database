<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Delete, Link, Upload} from '@element-plus/icons-vue'
import {
  DeletePaper,
  GetMyPapers,
  ImportArxiv,
  PreviewArxiv,
  RecordClick,
  type ArxivImportPayload,
} from '@/request/api'

const router = useRouter()

const arxivUrl = ref('')
const previewing = ref(false)
const importing = ref(false)
const showForm = ref(false)
const sourceHint = ref('') // '' | 'openalex' | 'none'

const form = ref<ArxivImportPayload>({
  arxiv_id: '',
  title: '',
  abstract: '',
  authors: '',
  venue: 'arXiv',
  year: 0,
  keywords: '',
  url: '',
})

const papers = ref<any[]>([])
const loading = ref(true)
const deletingId = ref<number | null>(null)

const exampleLinks = [
  'https://arxiv.org/abs/2310.06825',
  'https://arxiv.org/abs/1706.03762',
]

function errDetail(error: any, fallback: string): string {
  return error?.response?.data?.detail || error?.message || fallback
}

function useExample(link: string) {
  arxivUrl.value = link
}

async function doPreview() {
  const url = arxivUrl.value.trim()
  if (!url) {
    ElMessage.warning('请粘贴 arXiv 论文链接')
    return
  }
  previewing.value = true
  try {
    const preview = await PreviewArxiv(url)
    form.value = {
      arxiv_id: preview.arxiv_id,
      title: preview.title || '',
      abstract: preview.abstract || '',
      authors: preview.authors || '',
      venue: preview.venue || 'arXiv',
      year: preview.year || 0,
      keywords: preview.keywords || '',
      url: preview.url || '',
    }
    sourceHint.value = preview.source
    showForm.value = true
    if (preview.source === 'none') {
      ElMessage.warning('未能从 OpenAlex 自动获取元数据，请手动补全后再导入')
    } else {
      ElMessage.success('已自动提取论文信息，确认无误后导入')
    }
  } catch (error: any) {
    ElMessage.error(errDetail(error, '解析失败'))
  } finally {
    previewing.value = false
  }
}

function cancelForm() {
  showForm.value = false
  sourceHint.value = ''
}

async function doImport() {
  if (!form.value.title.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }
  importing.value = true
  try {
    await ImportArxiv(form.value)
    ElMessage.success('导入成功，已加入你的论文库')
    showForm.value = false
    arxivUrl.value = ''
    sourceHint.value = ''
    await loadMine()
  } catch (error: any) {
    ElMessage.error(errDetail(error, '导入失败'))
  } finally {
    importing.value = false
  }
}

async function loadMine() {
  loading.value = true
  try {
    const res = await GetMyPapers()
    papers.value = res.papers || []
  } catch (_error) {
    ElMessage.error('获取我的论文失败')
  } finally {
    loading.value = false
  }
}

async function viewPaper(paperId: number) {
  try {
    await RecordClick(paperId)
  } catch (_error) {
    // ignore click recording failure
  }
  router.push(`/index/paperDetail/${paperId}`)
}

async function removePaper(paperId: number, title: string) {
  try {
    await ElMessageBox.confirm(
      `确定删除《${title}》吗？该操作会同时移除其 PDF、搜索/推荐与问答索引。`,
      '删除确认',
      {type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'},
    )
  } catch {
    return // 用户取消
  }
  deletingId.value = paperId
  try {
    await DeletePaper(paperId)
    ElMessage.success('已删除')
    await loadMine()
  } catch (error: any) {
    ElMessage.error(errDetail(error, '删除失败'))
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  loadMine()
})
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <p class="page-eyebrow">My Library</p>
      <h1 class="hero-title">上传并管理我的论文</h1>
      <div class="example-tags">
        <span>试试示例链接：</span>
        <el-tag
          v-for="item in exampleLinks"
          :key="item"
          class="example-tag"
          effect="dark"
          @click="useExample(item)"
        >
          {{ item }}
        </el-tag>
      </div>
    </section>

    <!-- 上传区 -->
    <section class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">从 arXiv 链接导入</h2>
        </div>
      </div>

      <div class="upload-bar">
        <el-input
          v-model="arxivUrl"
          placeholder="粘贴 arXiv 链接，例如 https://arxiv.org/abs/2310.06825"
          size="large"
          clearable
          @keyup.enter="doPreview"
        >
          <template #append>
            <el-button :icon="Upload" :loading="previewing" @click="doPreview">
              解析
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 可编辑元数据表单 -->
      <div v-if="showForm" class="preview-form">
        <el-alert
          v-if="sourceHint === 'none'"
          type="warning"
          :closable="false"
          show-icon
          title="未能自动获取元数据，请手动补全（标题必填）后导入"
          class="form-alert"
        />
        <el-alert
          v-else
          type="success"
          :closable="false"
          show-icon
          title="已从 OpenAlex 自动提取，可按需修改后导入"
          class="form-alert"
        />

        <el-form :model="form" label-width="84px" label-position="top">
          <el-form-item label="标题" required>
            <el-input v-model="form.title" placeholder="论文标题" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="作者">
              <el-input v-model="form.authors" placeholder="作者，逗号分隔" />
            </el-form-item>
            <el-form-item label="会议/期刊">
              <el-input v-model="form.venue" placeholder="arXiv" />
            </el-form-item>
            <el-form-item label="年份">
              <el-input-number v-model="form.year" :min="0" :max="2100" controls-position="right" />
            </el-form-item>
          </div>
          <el-form-item label="关键词">
            <el-input v-model="form.keywords" placeholder="关键词，逗号分隔" />
          </el-form-item>
          <el-form-item label="摘要">
            <el-input
              v-model="form.abstract"
              type="textarea"
              :autosize="{minRows: 3, maxRows: 8}"
              placeholder="论文摘要（用于语义搜索/推荐，建议填写）"
            />
          </el-form-item>
          <el-form-item label="原文链接">
            <el-input v-model="form.url" placeholder="https://arxiv.org/abs/..." />
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="cancelForm">取消</el-button>
          <el-button type="primary" :loading="importing" @click="doImport">
            确认导入
          </el-button>
        </div>
      </div>
    </section>

    <!-- 我的论文列表 -->
    <section class="page-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="card-heading">我的论文</h2>
        </div>
        <div v-if="papers.length > 0" class="result-summary">
          共 {{ papers.length }} 篇
        </div>
      </div>

      <div v-if="!loading && papers.length === 0" class="placeholder-panel">
        <el-empty description="还没有上传论文，粘贴 arXiv 链接开始导入吧" />
      </div>

      <el-table
        v-else
        :data="papers"
        stripe
        style="width: 100%; margin-top: 8px"
        @row-click="(row: any) => viewPaper(row.id)"
        class="clickable-table"
      >
        <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="authors" label="作者" min-width="180" show-overflow-tooltip />
        <el-table-column prop="venue" label="来源" width="120" />
        <el-table-column prop="year" label="年份" width="90" />
        <el-table-column label="PDF" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_pdf" type="success" size="small">PDF</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="链接" width="70" align="center">
          <template #default="{ row }">
            <a
              v-if="row.url"
              :href="row.url"
              target="_blank"
              rel="noopener"
              @click.stop
              class="paper-link"
            >
              <el-icon :size="18"><Link /></el-icon>
            </a>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-button
              text
              type="danger"
              :icon="Delete"
              :loading="deletingId === row.id"
              @click.stop="removePaper(row.id, row.title)"
            />
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.upload-bar {
  margin: 16px 0 4px;
  max-width: 920px;
}

.example-tags {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  color: rgba(255, 255, 255, 0.88);
}

.example-tag {
  cursor: pointer;
  border-color: rgba(255, 255, 255, 0.16);
}

.preview-form {
  margin-top: 18px;
  padding: 18px;
  border-radius: 18px;
  background: #f8fbff;
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.form-alert {
  margin-bottom: 16px;
  border-radius: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 160px;
  gap: 0 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
}

.result-summary {
  padding: 10px 14px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 14px;
  font-weight: 600;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #2563eb;
}

.placeholder-panel {
  margin-top: 20px;
}

@media (max-width: 960px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

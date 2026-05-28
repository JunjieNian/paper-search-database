<script setup lang="ts">
import {onMounted, ref, watch} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {InfoFilled, Link, Search} from '@element-plus/icons-vue'
import {GetSearchHistory, RecordClick, SearchPapers} from '@/request/api'

const router = useRouter()
const RERANK_STORAGE_KEY = 'paper_search_enable_rerank'

const searchQuery = ref('')
const papers = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const searchHistory = ref<any[]>([])
const searched = ref(false)
const rerankEnabled = ref(localStorage.getItem(RERANK_STORAGE_KEY) === 'true')

const exampleQueries = [
  'database query optimization',
  'cardinality estimation for SQL',
  'learned index structures',
  'approximate query processing',
]

watch(rerankEnabled, value => {
  localStorage.setItem(RERANK_STORAGE_KEY, String(value))
})

const loadHistory = async () => {
  try {
    const res = await GetSearchHistory()
    const seen = new Set<string>()
    searchHistory.value = (res.items || [])
      .filter((item: any) => {
        if (seen.has(item.query)) return false
        seen.add(item.query)
        return true
      })
      .slice(0, 10)
  } catch (_error) {
    // ignore
  }
}

const doSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  searched.value = true
  loading.value = true
  try {
    const res = await SearchPapers({
      query: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value,
      use_rerank: rerankEnabled.value,
      rerank_provider: rerankEnabled.value ? 'qwen' : undefined,
    })
    papers.value = res.papers || []
    total.value = res.total || 0
    await loadHistory()
  } catch (error: any) {
    ElMessage.error('搜索失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  if (searched.value) doSearch()
}

const viewPaper = async (paperId: number) => {
  try {
    await RecordClick(paperId)
  } catch (_error) {
    // ignore click recording failure
  }
  router.push(`/index/paperDetail/${paperId}`)
}

const useHistoryQuery = (query: string) => {
  searchQuery.value = query
  currentPage.value = 1
  doSearch()
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <p class="page-eyebrow">Academic Retrieval</p>
      <h1 class="hero-title">语义搜索数据库相关论文</h1>
      <p class="hero-description">
        输入研究主题、方法名、问题场景或关键词组合，系统会基于论文标题、摘要和关键词返回更相关的结果。
      </p>
      <div class="example-tags">
        <span>试试这些主题：</span>
        <el-tag
          v-for="item in exampleQueries"
          :key="item"
          class="example-tag"
          effect="dark"
          @click="useHistoryQuery(item)"
        >
          {{ item }}
        </el-tag>
      </div>
    </section>

    <section class="page-card">
      <div class="section-header">
        <div>
          <h2 class="card-heading">论文搜索</h2>
          <p class="muted-text">支持回车搜索，点击表格行可以进入论文详情。</p>
        </div>
        <div v-if="searched && total > 0" class="result-summary">
          共找到 {{ total }} 篇相关论文
        </div>
      </div>

      <div class="search-toolbar">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="例如：database query optimization / learned cardinality estimation"
            size="large"
            clearable
            @keyup.enter="doSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="doSearch" :loading="loading">
                搜索
              </el-button>
            </template>
          </el-input>
        </div>

        <div class="rerank-panel">
          <div class="rerank-copy">
            <strong>启用 Qwen Rerank</strong>
            <span>相关性通常更好，但搜索会明显变慢。</span>
          </div>
          <el-switch v-model="rerankEnabled" inline-prompt active-text="开" inactive-text="关" />
        </div>
      </div>

      <div class="rerank-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>这是实验功能开关。关闭时走基础向量检索；开启时走“向量召回 + qwen3-rerank 精排”。</span>
      </div>

      <div class="history-tags" v-if="searchHistory.length > 0">
        <span class="history-label">最近搜索：</span>
        <el-tag
          v-for="item in searchHistory"
          :key="item.id"
          class="history-tag"
          type="info"
          effect="plain"
          @click="useHistoryQuery(item.query)"
        >
          {{ item.query }}
        </el-tag>
      </div>

      <div v-if="!searched" class="placeholder-panel">
        <el-empty description="输入关键词后开始搜索论文" />
      </div>

      <div v-else-if="!loading && papers.length === 0" class="placeholder-panel">
        <el-empty description="没有找到相关论文，可以换个关键词试试" />
      </div>

      <template v-else>
        <el-table
          :data="papers"
          v-loading="loading"
          stripe
          style="width: 100%; margin-top: 12px"
          @row-click="(row: any) => viewPaper(row.id)"
          class="clickable-table"
        >
          <el-table-column prop="title" label="标题" min-width="320" show-overflow-tooltip />
          <el-table-column prop="authors" label="作者" min-width="220" show-overflow-tooltip />
          <el-table-column prop="venue" label="会议/期刊" width="150" />
          <el-table-column prop="year" label="年份" width="90" />
          <el-table-column prop="keywords" label="关键词" min-width="220" show-overflow-tooltip />
          <el-table-column label="链接" width="80" align="center">
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
        </el-table>

        <div class="pagination" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.search-toolbar {
  display: flex;
  align-items: stretch;
  gap: 16px;
  margin: 18px 0 10px;
}

.search-bar {
  flex: 1;
  min-width: 0;
  max-width: 860px;
}

.rerank-panel {
  min-width: 280px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f8fbff;
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.rerank-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rerank-copy strong {
  font-size: 14px;
  color: #0f172a;
}

.rerank-copy span {
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
}

.rerank-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #64748b;
  font-size: 13px;
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

.result-summary {
  padding: 10px 14px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 14px;
  font-weight: 600;
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.history-label {
  color: #64748b;
  font-size: 14px;
}

.history-tag {
  cursor: pointer;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #2563eb;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 960px) {
  .search-toolbar {
    flex-direction: column;
  }

  .search-bar {
    max-width: none;
  }

  .rerank-panel {
    min-width: 0;
  }
}
</style>

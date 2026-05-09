<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { SearchPapers, RecordClick, GetSearchHistory } from '@/request/api'
import { ElMessage } from 'element-plus'
import { Search, Link } from '@element-plus/icons-vue'

const router = useRouter()

const searchQuery = ref('')
const papers = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const searchHistory = ref<any[]>([])

const loadHistory = async () => {
  try {
    const res = await GetSearchHistory()
    // 去重
    const seen = new Set<string>()
    searchHistory.value = (res.items || []).filter((item: any) => {
      if (seen.has(item.query)) return false
      seen.add(item.query)
      return true
    }).slice(0, 10)
  } catch (e) {
    // ignore
  }
}

const doSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  loading.value = true
  try {
    const res = await SearchPapers({
      query: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    papers.value = res.papers || []
    total.value = res.total || 0
    loadHistory()
  } catch (e: any) {
    ElMessage.error('搜索失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  doSearch()
}

const viewPaper = async (paperId: number) => {
  try {
    await RecordClick(paperId)
  } catch (e) {
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
  <div class="paper-search">
    <h2>论文搜索</h2>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="输入关键词搜索论文..."
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

    <div class="history-tags" v-if="searchHistory.length > 0">
      <span class="history-label">搜索历史：</span>
      <el-tag
        v-for="item in searchHistory"
        :key="item.id"
        class="history-tag"
        type="info"
        effect="plain"
        @click="useHistoryQuery(item.query)"
        style="cursor: pointer"
      >
        {{ item.query }}
      </el-tag>
    </div>

    <el-table
      :data="papers"
      v-loading="loading"
      stripe
      style="width: 100%; margin-top: 20px"
      @row-click="(row: any) => viewPaper(row.id)"
      class="clickable-table"
    >
      <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
      <el-table-column prop="authors" label="作者" min-width="200" show-overflow-tooltip />
      <el-table-column prop="venue" label="会议/期刊" width="120" />
      <el-table-column prop="year" label="年份" width="80" />
      <el-table-column prop="keywords" label="关键词" min-width="200" show-overflow-tooltip />
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
  </div>
</template>

<style scoped>
.paper-search {
  padding: 20px;
}

.search-bar {
  margin: 20px 0;
  max-width: 700px;
}

.history-tags {
  margin-bottom: 10px;
}

.history-label {
  color: #909399;
  font-size: 14px;
  margin-right: 8px;
}

.history-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #409eff;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.paper-link {
  color: #409eff;
  transition: color 0.2s;
}

.paper-link:hover {
  color: #66b1ff;
}
</style>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {Link} from '@element-plus/icons-vue'
import {GetRecommendations, RecordClick} from '@/request/api'

const router = useRouter()
const papers = ref<any[]>([])
const loading = ref(true)
const hasClicks = ref(true)

const loadRecommendations = async () => {
  loading.value = true
  try {
    const res = await GetRecommendations()
    papers.value = res.papers || []
    hasClicks.value = papers.value.length > 0
  } catch (_error) {
    ElMessage.error('获取推荐失败')
  } finally {
    loading.value = false
  }
}

const viewPaper = async (paperId: number) => {
  try {
    await RecordClick(paperId)
  } catch (_error) {
    // ignore
  }
  router.push(`/index/paperDetail/${paperId}`)
}

onMounted(() => {
  loadRecommendations()
})
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <p class="page-eyebrow">Personalized Recommendation</p>
      <h1 class="hero-title">根据浏览记录推荐相关论文</h1>
    </section>

    <section class="page-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="card-heading">推荐结果</h2>
        </div>
        <el-button plain @click="router.push('/index/paperSearch')">
          去搜索论文
        </el-button>
      </div>

      <div v-if="!loading && !hasClicks" class="empty-tip">
        <el-empty description="暂无推荐" />
      </div>

      <div v-else-if="papers.length > 0" class="recommend-list">
        <el-table
          :data="papers"
          stripe
          style="width: 100%; margin-top: 8px"
          @row-click="(row: any) => viewPaper(row.id)"
          class="clickable-table"
        >
          <el-table-column prop="title" label="标题" min-width="320" show-overflow-tooltip />
          <el-table-column prop="authors" label="作者" min-width="220" show-overflow-tooltip />
          <el-table-column prop="venue" label="会议/期刊" width="150" />
          <el-table-column prop="year" label="年份" width="90" />
          <el-table-column prop="keywords" label="关键词" min-width="220" show-overflow-tooltip />
          <el-table-column label="PDF" width="70" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.has_pdf" type="success" size="small">PDF</el-tag>
            </template>
          </el-table-column>
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
      </div>

      <div v-else-if="!loading" class="empty-tip">
        <el-empty description="暂时没有推荐结果" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.empty-tip {
  margin-top: 26px;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #2563eb;
}
</style>

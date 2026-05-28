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
      <p class="hero-description">
        推荐结果会优先参考你最近点击查看的论文内容。如果当前为空，先去搜索并打开几篇论文即可。
      </p>
    </section>

    <section class="page-card" v-loading="loading">
      <div class="section-header">
        <div>
          <h2 class="card-heading">推荐结果</h2>
          <p class="muted-text">点击任意一行可继续查看论文详情。</p>
        </div>
        <el-button plain @click="router.push('/index/paperSearch')">
          去搜索论文
        </el-button>
      </div>

      <div v-if="!loading && !hasClicks" class="empty-tip">
        <el-empty description="暂无推荐">
          <template #description>
            <p class="tip-text">
              你还没有浏览过论文。先前往
              <el-link type="primary" @click="router.push('/index/paperSearch')">论文搜索</el-link>
              页面搜索并点击论文，系统才会生成更有针对性的推荐。
            </p>
          </template>
        </el-empty>
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

.tip-text {
  color: #64748b;
  font-size: 14px;
  line-height: 1.8;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #2563eb;
}
</style>

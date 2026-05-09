<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { GetRecommendations, RecordClick } from '@/request/api'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'

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
  } catch (e: any) {
    ElMessage.error('获取推荐失败')
  } finally {
    loading.value = false
  }
}

const viewPaper = async (paperId: number) => {
  try {
    await RecordClick(paperId)
  } catch (e) {
    // ignore
  }
  router.push(`/index/paperDetail/${paperId}`)
}

onMounted(() => {
  loadRecommendations()
})
</script>

<template>
  <div class="paper-recommend" v-loading="loading">
    <h2>论文推荐</h2>

    <div v-if="!loading && !hasClicks" class="empty-tip">
      <el-empty description="暂无推荐">
        <template #description>
          <p>您还没有浏览过论文，请先前往
            <el-link type="primary" @click="router.push('/index/paperSearch')">论文搜索</el-link>
            页面搜索并点击论文，系统将根据您的浏览记录为您推荐相关论文。
          </p>
        </template>
      </el-empty>
    </div>

    <div v-if="papers.length > 0" class="recommend-list">
      <p class="tip-text">根据您的浏览记录，为您推荐以下论文：</p>
      <el-table
        :data="papers"
        stripe
        style="width: 100%; margin-top: 16px"
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
    </div>
  </div>
</template>

<style scoped>
.paper-recommend {
  padding: 20px;
}

.empty-tip {
  margin-top: 60px;
}

.tip-text {
  color: #606266;
  font-size: 14px;
}

.clickable-table :deep(tbody tr) {
  cursor: pointer;
}

.clickable-table :deep(tbody tr:hover) {
  color: #409eff;
}

.paper-link {
  color: #409eff;
  transition: color 0.2s;
}

.paper-link:hover {
  color: #66b1ff;
}
</style>

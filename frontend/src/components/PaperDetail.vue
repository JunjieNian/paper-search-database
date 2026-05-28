<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {GetPaperDetail} from '@/request/api'

const route = useRoute()
const router = useRouter()
const paper = ref<any>(null)
const loading = ref(true)

const keywordList = computed(() =>
  String(paper.value?.keywords || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean),
)

onMounted(async () => {
  const paperId = Number(route.params.paperId)
  if (!paperId) {
    ElMessage.error('无效的论文ID')
    router.push('/index/paperSearch')
    return
  }
  try {
    paper.value = await GetPaperDetail(paperId)
  } catch (_error) {
    ElMessage.error('获取论文详情失败')
    router.push('/index/paperSearch')
  } finally {
    loading.value = false
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
      <p class="hero-description">
        {{ paper.venue || 'Unknown Venue' }} · {{ paper.year || 'Unknown Year' }}
      </p>
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
</style>

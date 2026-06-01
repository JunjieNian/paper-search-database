<script setup lang="ts">
import {ChatDotRound, Search, Star, SwitchButton} from '@element-plus/icons-vue'
import {computed, onBeforeMount, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {GetUserInfoByUserName} from '@/request/api'
import {useUserstore} from '@/store/user'

const userStore = useUserstore()
const route = useRoute()
const router = useRouter()

const user = ref({
  username: '',
  first_name: '',
  last_name: '',
  email: '',
})

const displayName = computed(() => {
  const fullName = [user.value.first_name, user.value.last_name].filter(Boolean).join(' ')
  return fullName || user.value.username || '同学'
})

const quickActions = [
  {
    title: '开始搜索',
    desc: '按标题、摘要和关键词查找相关论文',
    path: '/index/paperSearch',
    icon: Search,
  },
  {
    title: '查看推荐',
    desc: '根据浏览记录获得个性化论文推荐',
    path: '/index/paperRecommend',
    icon: Star,
  },
  {
    title: '打开 AI 助手',
    desc: '用自然语言提问，让模型解释论文或研究方向',
    path: '/index/chat',
    icon: ChatDotRound,
  },
]

async function logout() {
  userStore.clearUser()
  ElMessage.success('已退出登录')
  await router.push('/')
}

async function getUserInfo() {
  try {
    let username = userStore.userName
    if (typeof route.params.username === 'string') {
      username = route.params.username
    }
    const res = await GetUserInfoByUserName({
      userName: username,
    })
    user.value.username = res.username
    user.value.email = res.email
    user.value.first_name = res.first_name
    user.value.last_name = res.last_name
  } catch (_error) {
    ElMessage.error('个人信息查询失败')
  }
}

onBeforeMount(() => {
  getUserInfo()
})
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <p class="page-eyebrow">Home</p>
      <h1 class="hero-title">欢迎回来，{{ displayName }}</h1>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="router.push('/index/paperSearch')">
          开始搜索
        </el-button>
        <el-button size="large" @click="router.push('/index/chat')">
          打开 AI 助手
        </el-button>
        <el-button plain size="large" :icon="SwitchButton" @click="logout">
          退出登录
        </el-button>
      </div>
    </section>

    <section class="profile-grid">
      <div class="page-card quickstart-card">
        <div class="section-header">
          <div>
            <h2 class="card-heading">快速开始</h2>
            <p class="muted-text">从下面的入口开始使用搜索、推荐和聊天功能。</p>
          </div>
        </div>

        <button
          v-for="item in quickActions"
          :key="item.path"
          class="shortcut-item"
          type="button"
          @click="router.push(item.path)"
        >
          <div class="shortcut-icon">
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
          </div>
          <div class="shortcut-copy">
            <strong>{{ item.title }}</strong>
            <span>{{ item.desc }}</span>
          </div>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  margin-top: 14px;
}

.profile-grid {
  display: block;
}

.quickstart-card {
  display: flex;
  flex-direction: column;
}

.shortcut-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
  margin-top: 12px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.shortcut-item:hover {
  transform: translateY(-2px);
  border-color: rgba(37, 99, 235, 0.26);
  box-shadow: 0 18px 32px rgba(37, 99, 235, 0.1);
}

.shortcut-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #1d4ed8;
  background: #eaf2ff;
  font-size: 18px;
}

.shortcut-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.shortcut-copy strong {
  font-size: 15px;
  color: #0f172a;
}

.shortcut-copy span {
  color: #64748b;
  line-height: 1.7;
}

@media (max-width: 960px) {
  .hero-actions {
    flex-wrap: wrap;
  }
}
</style>

<script setup lang="ts">
import {ChatDotRound, Search, Star} from '@element-plus/icons-vue'
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

const userEmail = computed(() => {
  if (user.value.email) return user.value.email
  if (user.value.username) return `${user.value.username}@example.com`
  return '暂未设置'
})

const avatarText = computed(() => displayName.value.slice(0, 1).toUpperCase())

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
      <p class="page-eyebrow">Workspace Overview</p>
      <h1 class="hero-title">欢迎回来，{{ displayName }}</h1>
      <p class="hero-description">
        这里是你的论文检索工作台。你可以直接开始搜索论文、查看推荐结果，
        或者进入 AI 助手继续围绕文献进行提问。
      </p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="router.push('/index/paperSearch')">
          开始搜索
        </el-button>
        <el-button size="large" @click="router.push('/index/chat')">
          打开 AI 助手
        </el-button>
      </div>
    </section>

    <section class="profile-grid">
      <div class="page-card profile-card">
        <div class="avatar">{{ avatarText }}</div>
        <div class="profile-info">
          <h2>{{ displayName }}</h2>
          <p class="username">@{{ user.username || 'unknown' }}</p>
          <div class="info-list">
            <div class="info-item">
              <span>用户名</span>
              <strong>{{ user.username || '未设置' }}</strong>
            </div>
            <div class="info-item">
              <span>姓名</span>
              <strong>{{ displayName }}</strong>
            </div>
            <div class="info-item">
              <span>邮箱</span>
              <strong>{{ userEmail }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="page-card quickstart-card">
        <div class="section-header">
          <div>
            <h2 class="card-heading">快速开始</h2>
            <p class="muted-text">主流程已经收敛为检索、推荐和聊天三大能力。</p>
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
  margin-top: 22px;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 20px;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 22px;
}

.avatar {
  width: 96px;
  height: 96px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 30px;
  font-size: 34px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.2);
}

.profile-info h2 {
  margin: 0;
  font-size: 24px;
}

.username {
  margin: 6px 0 0;
  color: #64748b;
}

.info-list {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.info-item span {
  color: #64748b;
  font-size: 14px;
}

.info-item strong {
  color: #0f172a;
  text-align: right;
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
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .profile-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-actions {
    flex-wrap: wrap;
  }
}
</style>

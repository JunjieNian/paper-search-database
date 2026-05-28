<script setup lang="ts">
import {ChatDotRound, Search, Star, UserFilled} from '@element-plus/icons-vue'
import {computed} from 'vue'
import {useRoute} from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/index/paperSearch')) return '/index/paperSearch'
  if (route.path.startsWith('/index/paperRecommend')) return '/index/paperRecommend'
  if (route.path.startsWith('/index/chat')) return '/index/chat'
  return '/index/'
})

const menuItems = [
  {
    index: '/index/',
    label: '主页概览',
    icon: UserFilled,
  },
  {
    index: '/index/paperSearch',
    label: '论文搜索',
    icon: Search,
  },
  {
    index: '/index/paperRecommend',
    label: '智能推荐',
    icon: Star,
  },
  {
    index: '/index/chat',
    label: 'AI 助手',
    icon: ChatDotRound,
  },
]
</script>

<template>
  <div class="sidebar">
    <div class="sidebar-intro">
      <div class="sidebar-logo">PS</div>
      <div class="sidebar-copy">
        <h2>Paper Search</h2>
        <p>聚焦论文搜索、推荐与问答，隐藏无关的用户管理入口。</p>
      </div>
    </div>

    <el-menu :default-active="activeMenu" class="sidebar-menu" :router="true">
      <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-footer">
      <p>主导航现在只保留核心功能，避免“添加用户”之类的干扰项。</p>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 18px;
  background: linear-gradient(180deg, #0f172a 0%, #172554 58%, #1d4ed8 100%);
  color: #e2e8f0;
}

.sidebar-intro {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 6px 10px 24px;
}

.sidebar-logo {
  width: 48px;
  height: 48px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.sidebar-copy h2 {
  margin: 2px 0 6px;
  font-size: 18px;
  color: #fff;
}

.sidebar-copy p {
  margin: 0;
  color: rgba(226, 232, 240, 0.75);
  font-size: 13px;
  line-height: 1.6;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
}

.sidebar-footer {
  margin-top: 22px;
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.sidebar-footer p {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.74);
}

:deep(.el-menu) {
  background: transparent;
}

:deep(.el-menu-item) {
  margin-bottom: 10px;
  border-radius: 16px;
  color: #cbd5e1;
  transition: all 0.2s ease;
}

:deep(.el-menu-item:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

:deep(.el-menu-item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.9), rgba(124, 58, 237, 0.9));
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.24);
}
</style>

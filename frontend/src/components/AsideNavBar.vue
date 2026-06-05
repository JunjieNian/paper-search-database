<script setup lang="ts">
import {ArrowLeftBold, ArrowRightBold, ChatDotRound, Folder, Search, Star, UserFilled} from '@element-plus/icons-vue'
import {computed} from 'vue'
import {useRoute} from 'vue-router'

withDefaults(defineProps<{
  collapsed?: boolean
}>(), {
  collapsed: false,
})

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
}>()

const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/index/paperSearch')) return '/index/paperSearch'
  if (route.path.startsWith('/index/paperRecommend')) return '/index/paperRecommend'
  if (route.path.startsWith('/index/myPapers')) return '/index/myPapers'
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
    index: '/index/myPapers',
    label: '我的论文',
    icon: Folder,
  },
  {
    index: '/index/chat',
    label: 'AI 助手',
    icon: ChatDotRound,
  },
]
</script>

<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <div class="sidebar-toolbar">
      <div class="sidebar-intro">
        <div class="sidebar-logo">PS</div>
        <div v-if="!collapsed" class="sidebar-copy">
          <h2>Paper Search</h2>
        </div>
      </div>
      <button
          type="button"
          class="collapse-button"
          :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
          @click="emit('toggle-collapse')"
      >
        <el-icon>
          <ArrowRightBold v-if="collapsed" />
          <ArrowLeftBold v-else />
        </el-icon>
      </button>
    </div>

    <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :router="true"
        :collapse="collapsed"
        :collapse-transition="false"
    >
      <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index" :title="item.label">
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
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
  transition: padding 0.24s ease;
}

.sidebar--collapsed {
  padding: 24px 12px;
}

.sidebar-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.sidebar--collapsed .sidebar-toolbar {
  flex-direction: column;
  align-items: center;
}

.collapse-button {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-button:hover {
  background: rgba(255, 255, 255, 0.16);
  transform: translateY(-1px);
}

.sidebar-intro {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  flex: 1;
  padding: 6px 10px 24px;
}

.sidebar--collapsed .sidebar-intro {
  flex: none;
  padding: 6px 0 12px;
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

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
  min-width: 0;
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

:deep(.el-menu--collapse) {
  border-right: none;
}

:deep(.el-menu--collapse .el-menu-item) {
  justify-content: center;
  padding: 0;
}

:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
}
</style>

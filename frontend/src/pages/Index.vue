<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import AsideNavBar from '@/components/AsideNavBar.vue'

const SIDEBAR_STORAGE_KEY = 'paper-search-sidebar-collapsed'
const isSidebarCollapsed = ref(false)
const route = useRoute()
const isChatRoute = computed(() => route.path.startsWith('/index/chat'))

onMounted(() => {
  isSidebarCollapsed.value = window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true'
})

watch(isSidebarCollapsed, (value) => {
  window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(value))
})

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--chat': isChatRoute }">
    <aside class="app-sidebar" :class="{ 'app-sidebar--collapsed': isSidebarCollapsed }">
      <AsideNavBar :collapsed="isSidebarCollapsed" @toggle-collapse="toggleSidebar" />
    </aside>
    <section class="app-workspace" :class="{ 'app-workspace--chat': isChatRoute }">
      <main class="app-content" :class="{ 'app-content--chat': isChatRoute }">
        <router-view />
      </main>
    </section>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  gap: 20px;
  padding: 24px;
}

.app-shell--chat {
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

.app-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-radius: 30px;
  overflow: hidden;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.18);
  transition: width 0.24s ease;
}

.app-sidebar--collapsed {
  width: 96px;
}

.app-workspace {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.app-workspace--chat {
  overflow: hidden;
}

.app-content {
  flex: 1;
  min-height: 0;
  padding: 24px;
  border-radius: 30px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(255, 255, 255, 0.66);
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
}

.app-content--chat {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-content--chat :deep(.chat-page) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .app-shell {
    flex-direction: column;
    padding: 16px;
  }

  .app-shell--chat {
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .app-sidebar {
    width: 100%;
  }

  .app-sidebar--collapsed {
    width: 100%;
  }

  .app-content {
    padding: 18px;
    border-radius: 24px;
  }

  .app-content--chat {
    overflow: visible;
  }

  .app-content--chat :deep(.chat-page) {
    overflow: visible;
  }
}
</style>

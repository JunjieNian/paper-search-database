<script setup lang="ts">
import AsideNavBar from '@/components/AsideNavBar.vue'
import Header from '@/components/Header.vue'
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <AsideNavBar />
    </aside>
    <section class="app-workspace">
      <Header />
      <main class="app-content">
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

.app-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-radius: 30px;
  overflow: hidden;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.18);
}

.app-workspace {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
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

@media (max-width: 1024px) {
  .app-shell {
    flex-direction: column;
    padding: 16px;
  }

  .app-sidebar {
    width: 100%;
  }

  .app-content {
    padding: 18px;
    border-radius: 24px;
  }
}
</style>

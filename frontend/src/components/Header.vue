<script setup lang="ts">
import {computed} from 'vue'
import {ElMessage} from 'element-plus'
import {SwitchButton} from '@element-plus/icons-vue'
import {useRouter} from 'vue-router'
import {useUserstore} from '@/store/user'

const router = useRouter()
const userStore = useUserstore()
const userName = computed(() => userStore.userName || '未登录用户')

async function logout() {
  userStore.clearUser()
  ElMessage.success('已退出登录')
  await router.push('/')
}
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <div class="brand-badge">PS</div>
      <div>
        <p class="brand-title">Paper Search Assistant</p>
        <p class="brand-subtitle">论文检索、推荐与 AI 助手的一体化前端</p>
      </div>
    </div>

    <div class="topbar-actions">
      <div class="user-pill">
        <span class="status-dot"></span>
        <span>{{ userName }}</span>
      </div>
      <el-button type="primary" plain :icon="SwitchButton" @click="logout">
        退出登录
      </el-button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 22px;
  border-radius: 26px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(16px);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-badge {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.22);
}

.brand-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.brand-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1e3a8a;
  font-size: 14px;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.14);
}

@media (max-width: 720px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .topbar-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

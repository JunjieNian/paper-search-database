<script setup lang="ts">
import LoginForm from '@/components/LoginForm.vue'
</script>

<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-showcase">
        <div>
          <span class="auth-showcase-badge">Academic Search</span>
          <h1>Paper Search Assistant</h1>
        </div>

        <ul class="auth-feature-list">
          <li class="auth-feature-item">
            <strong>论文搜索</strong>
          </li>
          <li class="auth-feature-item">
            <strong>智能推荐</strong>
          </li>
          <li class="auth-feature-item">
            <strong>聊天助手</strong>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <LoginForm />
      </section>
    </div>
  </div>
</template>

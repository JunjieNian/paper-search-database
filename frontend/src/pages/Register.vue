<script setup lang="ts">
import RegisterForm from '@/components/RegisterForm.vue'
</script>

<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-showcase">
        <div>
          <span class="auth-showcase-badge">Create Account</span>
          <h1>创建你的论文检索账号</h1>
        </div>

        <ul class="auth-feature-list">
          <li class="auth-feature-item">
            <strong>快速开始</strong>
          </li>
          <li class="auth-feature-item">
            <strong>统一体验</strong>
          </li>
          <li class="auth-feature-item">
            <strong>AI 问答</strong>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <RegisterForm />
      </section>
    </div>
  </div>
</template>

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
          <p>
            注册后即可使用论文搜索、推荐和 AI 问答功能。
          </p>
        </div>

        <ul class="auth-feature-list">
          <li class="auth-feature-item">
            <strong>快速开始</strong>
            <span>登录后可直接进入搜索、推荐和问答页面。</span>
          </li>
          <li class="auth-feature-item">
            <strong>统一体验</strong>
            <span>主页、搜索、详情和聊天页面保持一致的界面风格。</span>
          </li>
          <li class="auth-feature-item">
            <strong>AI 问答</strong>
            <span>可以围绕论文内容、关键词和研究方向继续提问。</span>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <RegisterForm />
      </section>
    </div>
  </div>
</template>

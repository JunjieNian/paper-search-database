<script setup lang="ts">
import RegisterForm from '@/components/RegisterForm.vue'
</script>

<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-showcase">
        <div>
          <span class="auth-showcase-badge">Join the Workspace</span>
          <h1>创建你的论文检索账号</h1>
          <p>
            注册后即可使用完整的论文搜索、推荐和 AI 问答流程。界面已经简化为更适合作业演示的核心功能。
          </p>
        </div>

        <ul class="auth-feature-list">
          <li class="auth-feature-item">
            <strong>更清晰的导航</strong>
            <span>移除了“添加用户”等对演示无帮助的入口。</span>
          </li>
          <li class="auth-feature-item">
            <strong>更好的视觉层次</strong>
            <span>主页、搜索页、详情页和聊天页都做了统一改版。</span>
          </li>
          <li class="auth-feature-item">
            <strong>会话自动保存</strong>
            <span>聊天内容保存在本地浏览器，切换页面后不会丢失。</span>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <RegisterForm />
      </section>
    </div>
  </div>
</template>

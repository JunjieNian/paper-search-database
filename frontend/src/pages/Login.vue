<script setup lang="ts">
import LoginForm from '@/components/LoginForm.vue'
</script>

<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-showcase">
        <div>
          <span class="auth-showcase-badge">Academic Demo</span>
          <h1>Paper Search Assistant</h1>
          <p>
            一个更聚焦的论文搜索系统前端，支持语义检索、个性化推荐和带会话记录的 AI 助手。
          </p>
        </div>

        <ul class="auth-feature-list">
          <li class="auth-feature-item">
            <strong>论文搜索</strong>
            <span>基于标题、摘要和关键词进行语义检索。</span>
          </li>
          <li class="auth-feature-item">
            <strong>智能推荐</strong>
            <span>根据浏览记录给出更贴近兴趣的候选论文。</span>
          </li>
          <li class="auth-feature-item">
            <strong>聊天助手</strong>
            <span>支持保存会话记录，回来后继续上次对话。</span>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <LoginForm />
      </section>
    </div>
  </div>
</template>

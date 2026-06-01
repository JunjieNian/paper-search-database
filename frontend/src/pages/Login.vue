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
          <p>
            面向学术论文检索、推荐与问答的系统，支持语义搜索、个性化推荐和 AI 助手。
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
            <span>围绕论文内容、研究方向和检索思路进行问答。</span>
          </li>
        </ul>
      </section>

      <section class="auth-panel">
        <LoginForm />
      </section>
    </div>
  </div>
</template>

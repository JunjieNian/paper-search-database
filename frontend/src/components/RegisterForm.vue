<script setup lang="ts">
import {reactive, ref} from 'vue'
import type {FormInstance} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {RegisterApi} from '@/request/api'

const router = useRouter()
const ruleFormRef = ref<FormInstance>()

const registerForm = reactive({
  userName: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
})

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async valid => {
    if (!valid) {
      ElMessage.error('注册失败请重新输入')
      return
    }
    try {
      await RegisterApi({
        username: registerForm.userName,
        password: registerForm.password,
        first_name: registerForm.first_name,
        last_name: registerForm.last_name,
        email: registerForm.email,
      })
      ElMessage.success('注册成功')
      await router.push('/')
    } catch (_error) {
      ElMessage.error('注册失败请重新输入')
    }
  })
}

function jumpToLogin() {
  router.push('/')
}
</script>

<template>
  <div class="auth-form-card">
    <div class="form-copy">
      <p class="form-eyebrow">Create Account</p>
      <h2>注册账号</h2>
    </div>

    <el-form ref="ruleFormRef" :model="registerForm" label-position="top" class="auth-form">
      <el-form-item label="用户名" prop="userName">
        <el-input v-model="registerForm.userName" type="text" autocomplete="off" placeholder="请输入用户名" />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="registerForm.password" type="password" autocomplete="off" show-password placeholder="请输入密码" />
      </el-form-item>

      <div class="name-grid">
        <el-form-item label="名" prop="first_name">
          <el-input v-model="registerForm.first_name" type="text" autocomplete="off" placeholder="例如 Junjie" />
        </el-form-item>

        <el-form-item label="姓" prop="last_name">
          <el-input v-model="registerForm.last_name" type="text" autocomplete="off" placeholder="例如 Nian" />
        </el-form-item>
      </div>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="registerForm.email" type="text" autocomplete="off" placeholder="请输入邮箱地址" />
      </el-form-item>

      <el-form-item class="actions">
        <el-button type="primary" class="primary-btn" @click="submitForm(ruleFormRef)">
          注册
        </el-button>
        <el-button class="secondary-btn" @click="jumpToLogin()">
          返回登录
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-copy {
  margin-bottom: 22px;
}

.form-eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.form-copy h2 {
  margin: 0;
  font-size: 28px;
  color: #0f172a;
}

.auth-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

.name-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.actions {
  margin-top: 10px;
  margin-bottom: 0;
}

.primary-btn,
.secondary-btn {
  min-width: 120px;
}

@media (max-width: 640px) {
  .name-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>

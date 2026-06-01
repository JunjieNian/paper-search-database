<script setup lang="ts">
import {reactive, ref} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {LoginApi} from '@/request/api'
import {useUserstore} from '@/store/user'

const userStore = useUserstore()
const router = useRouter()
const ruleFormRef = ref<FormInstance>()

const ruleForm = reactive({
  userName: '',
  password: '',
})

const checkUserName = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请输入用户名'))
  } else {
    callback()
  }
}

const checkPassword = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    callback()
  }
}

const rules = reactive<FormRules<typeof ruleForm>>({
  userName: [{validator: checkUserName, trigger: 'blur'}],
  password: [{validator: checkPassword, trigger: 'blur'}],
})

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async valid => {
    if (!valid) {
      ElMessage.error('登陆失败，未输入用户名和密码')
      return
    }
    try {
      const res = await LoginApi({
        username: ruleForm.userName,
        password: ruleForm.password,
      })
      ElMessage.success('登陆成功')
      userStore.setUser(ruleForm.userName, res.access_token)
      await router.push({name: 'IndexMain', params: {userName: ruleForm.userName}})
    } catch (_error) {
      ElMessage.error('登陆失败，请重新输入用户名和密码')
    }
  })
}

function jumpToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="auth-form-card">
    <div class="form-copy">
      <p class="form-eyebrow">Welcome Back</p>
      <h2>登录系统</h2>
      <p>输入你的账号后，即可进入论文搜索、推荐和 AI 助手。</p>
    </div>

    <el-form ref="ruleFormRef" :model="ruleForm" :rules="rules" label-position="top" class="auth-form">
      <el-form-item label="用户名" prop="userName">
        <el-input v-model="ruleForm.userName" type="text" autocomplete="off" placeholder="请输入用户名" />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="ruleForm.password" type="password" autocomplete="off" show-password placeholder="请输入密码" />
      </el-form-item>

      <el-form-item class="actions">
        <el-button type="primary" class="primary-btn" @click="submitForm(ruleFormRef)">
          登录
        </el-button>
        <el-button class="secondary-btn" @click="jumpToRegister()">
          去注册
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

.form-copy p {
  margin: 10px 0 0;
  color: #64748b;
  line-height: 1.8;
}

.auth-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

.actions {
  margin-top: 10px;
  margin-bottom: 0;
}

.primary-btn,
.secondary-btn {
  min-width: 120px;
}
</style>

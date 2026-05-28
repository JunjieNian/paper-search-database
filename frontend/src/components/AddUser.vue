<script setup lang="ts">
import {reactive, ref} from 'vue'
import type {FormInstance} from 'element-plus'
import {ElMessage} from 'element-plus'
import {RegisterApi} from '@/request/api'

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
      ElMessage.error('添加失败请重新输入')
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
      ElMessage.success('添加成功')
    } catch (_error) {
      ElMessage.error('添加失败请重新输入')
    }
  })
}
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="registerForm"
    style="max-width: 600px"
    label-width="auto"
    class="demo-ruleForm"
  >
    <el-form-item label="用户名" prop="userName">
      <el-input v-model="registerForm.userName" type="text" autocomplete="off" />
    </el-form-item>

    <el-form-item label="密码" prop="password">
      <el-input v-model="registerForm.password" type="password" autocomplete="off" />
    </el-form-item>

    <el-form-item label="名" prop="first_name">
      <el-input v-model="registerForm.first_name" type="text" autocomplete="off" />
    </el-form-item>

    <el-form-item label="姓" prop="last_name">
      <el-input v-model="registerForm.last_name" type="text" autocomplete="off" />
    </el-form-item>

    <el-form-item label="邮箱" prop="email">
      <el-input v-model="registerForm.email" type="text" autocomplete="off" />
    </el-form-item>

    <el-form-item>
      <el-button type="success" @click="submitForm(ruleFormRef)">
        添加
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import {ElMessage, ElNotification as notify} from 'element-plus'
import {LogoutApi} from "@/request/api";
import {useRouter} from 'vue-router'
import {useUserstore} from "@/store/user";
const router = useRouter()
const userStore=useUserstore()
async function logout() {
  userStore.clearUser()
  ElMessage.success("登出成功")
  await router.push('/')
}
</script>

<template>
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="Logo" style="height: 50px;">
    <div>
      <el-button type="info" @click="logout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>

</style>
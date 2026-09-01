<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <main class="not-found">
    <span>404</span>
    <h1>页面还没有建设</h1>
    <p>回到身份选择页，进入当前可用的演示页面。</p>
    <el-button type="primary" @click="router.push('/')">返回首页</el-button>
  </main>
</template>


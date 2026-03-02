<template>
  <router-view />
</template>

<script setup lang="ts">
// App.vue 现在只作为路由的容器
// 具体内容由各个路由组件决定
</script>

<style>
/* Global styles */
body {
  margin: 0;
  padding: 0;
}

#app {
  height: 100vh;
  width: 100vw;
}
</style>

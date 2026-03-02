<template>
  <div class="app h-screen w-screen overflow-hidden bg-dark-bg text-dark-text">
    <div class="flex h-full">
      <!-- Left Sidebar -->
      <Sidebar class="w-80 flex-shrink-0" />

      <!-- Main Chat Area -->
      <ChatWindow class="flex-1" />
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '../components/Sidebar.vue'
import ChatWindow from '../components/ChatWindow.vue'
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

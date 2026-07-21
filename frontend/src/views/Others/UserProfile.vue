<template>
  <admin-layout>
    <PageBreadcrumb :pageTitle="currentPageTitle" />

    <div
      class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] lg:p-6"
    >
      <h3 class="mb-5 text-lg font-semibold text-gray-800 dark:text-white/90 lg:mb-7">
        Perfil de Usuario
      </h3>
      <personal-info-card v-if="authStore.user" :user="authStore.user" />
    </div>
  </admin-layout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AdminLayout from '../../components/layout/AdminLayout.vue'
import PageBreadcrumb from '@/components/common/PageBreadcrumb.vue'
import PersonalInfoCard from '../../components/profile/PersonalInfoCard.vue'
import { useAuthStore } from '../../stores/auth'

const currentPageTitle = ref('Perfil de Usuario')
const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.user && authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()
  }
})
</script>

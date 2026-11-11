<template>
  <FullScreenLayout>
    <div
      class="relative flex items-center justify-center w-full h-screen bg-white dark:bg-gray-900"
    >
      <div class="w-full max-w-md p-6">
        <p
          v-if="state === 'loading' || state === 'redirecting'"
          class="text-sm text-center text-gray-500 dark:text-gray-400"
        >
          {{ state === 'loading' ? 'Cargando autorización...' : 'Volviendo a la aplicación...' }}
        </p>

        <div
          v-else-if="state === 'error'"
          class="p-3 text-sm text-center text-red-600 bg-red-50 rounded-lg"
        >
          La solicitud de autorización no es válida o expiró. Vuelve a conectar desde la aplicación.
        </div>

        <div
          v-else-if="state === 'forbidden'"
          class="p-3 text-sm text-center text-red-600 bg-red-50 rounded-lg"
        >
          Tu cuenta no tiene acceso activo a Print Quote.
        </div>

        <template v-else-if="details">
          <div class="mb-8 text-center">
            <h1
              class="mb-2 font-semibold text-gray-800 text-title-sm dark:text-white/90 sm:text-title-md"
            >
              Autorizar acceso
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              <strong class="text-gray-800 dark:text-white/90">{{ details.client.name }}</strong>
              quiere crear y consultar cotizaciones como
              <strong class="text-gray-800 dark:text-white/90">{{ details.user.email }}</strong
              >, con tu mismo rol y clientes.
            </p>
          </div>

          <div v-if="scopes.length" class="mb-6 text-sm text-gray-500 dark:text-gray-400">
            Permisos solicitados: {{ scopes.join(', ') }}
          </div>

          <div class="flex gap-3">
            <button
              type="button"
              :disabled="submitting"
              class="flex items-center justify-center w-full px-4 py-3 text-sm font-medium text-gray-700 transition bg-white border border-gray-300 rounded-lg shadow-theme-xs hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300"
              @click="deny"
            >
              Rechazar
            </button>
            <button
              type="button"
              :disabled="submitting"
              class="flex items-center justify-center w-full px-4 py-3 text-sm font-medium text-white transition rounded-lg bg-brand-500 shadow-theme-xs hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed"
              @click="approve"
            >
              Aprobar
            </button>
          </div>
        </template>
      </div>
    </div>
  </FullScreenLayout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import FullScreenLayout from '@/components/layout/FullScreenLayout.vue'
import { useAuth } from '@/composables/useAuth'
import { useOAuthConsent } from '@/composables/useOAuthConsent'
import { supabase } from '@/config/supabase'

const route = useRoute()
const { fetchCurrentUser } = useAuth()
const { state, details, scopes, submitting, load, approve, deny } = useOAuthConsent(
  supabase.auth.oauth,
  fetchCurrentUser,
  (url) => window.location.assign(url),
)

onMounted(() => load(route.query.authorization_id))
</script>

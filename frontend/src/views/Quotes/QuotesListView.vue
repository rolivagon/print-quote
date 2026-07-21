<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Cotizaciones</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Cotizaciones</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Gestiona las cotizaciones del sistema
          </p>
        </div>
        <div class="flex gap-3">
          <router-link
            to="/quotes/new"
            class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-600"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Nueva Cotización
          </router-link>
        </div>
      </div>

      <!-- Filters -->
      <div
        class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <div class="border-b border-gray-200 p-4 dark:border-gray-700">
          <div class="flex flex-wrap items-center gap-4">
            <!-- Search -->
            <div class="relative flex-1 min-w-[200px] max-w-md">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Buscar cotizaciones..."
                class="h-11 w-full rounded-lg border border-gray-300 bg-transparent pl-10 pr-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              />
              <svg
                class="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <!-- Status Filter -->
            <div class="min-w-[150px]">
              <select
                v-model="statusFilter"
                class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              >
                <option value="">Todos los estados</option>
                <option
                  v-for="option in QUOTE_STATUS_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
            <!-- Refresh Button -->
            <button
              @click="fetchQuotes"
              class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <RefreshIcon class="h-4 w-4" />
              Actualizar
            </button>
          </div>
        </div>

        <!-- Table -->
        <div class="max-w-full overflow-x-auto">
          <table class="min-w-full">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="px-5 py-3 text-left sm:px-6 w-16">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">ID</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-1/4">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Cliente</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Fecha</p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Total</p>
                </th>
                <th class="px-5 py-3 text-center sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Estado</p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Acciones</p>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-if="loading" class="border-t border-gray-100 dark:border-gray-800">
                <td colspan="6" class="px-5 py-8 sm:px-6 text-center">
                  <div class="flex items-center justify-center">
                    <div
                      class="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent"
                    ></div>
                  </div>
                </td>
              </tr>
              <tr
                v-else-if="filteredQuotes.length === 0"
                class="border-t border-gray-100 dark:border-gray-800"
              >
                <td
                  colspan="6"
                  class="px-5 py-8 sm:px-6 text-center text-gray-500 dark:text-gray-400"
                >
                  No se encontraron cotizaciones
                </td>
              </tr>
              <tr
                v-for="quote in filteredQuotes"
                :key="quote.id"
                class="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td class="px-5 py-4 sm:px-6">
                  <p class="font-mono text-sm text-gray-600 dark:text-gray-400">#{{ quote.id }}</p>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <div v-if="quote.client">
                    <p class="font-medium text-gray-800 text-theme-sm dark:text-white/90">
                      {{
                        quote.client.client_type === 'individual'
                          ? `${quote.client.first_name} ${quote.client.last_name}`
                          : quote.client.company_name
                      }}
                    </p>
                    <p class="text-xs text-gray-400">{{ quote.client.tax_id }}</p>
                  </div>
                  <p v-else class="text-sm text-gray-500">Cliente #{{ quote.client_id }}</p>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    {{ formatDate(quote.created_at) }}
                  </p>
                </td>
                <td class="px-5 py-4 sm:px-6 text-right">
                  <p class="font-medium text-gray-800 text-theme-sm dark:text-white/90">
                    {{ formatCurrency(quote.total) }}
                  </p>
                </td>
                <td class="px-5 py-4 sm:px-6 text-center">
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      getStatusBadgeClass(quote.status),
                    ]"
                  >
                    {{ getQuoteStatusLabel(quote.status) }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      v-if="quote.status === 'draft'"
                      @click="updateStatus(quote.id, 'sent')"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-success-500 hover:bg-success-50 dark:hover:bg-success-500/10"
                      title="Enviar cotización"
                    >
                      <SendIcon class="h-4 w-4" />
                    </button>
                    <button
                      v-if="quote.status === 'sent'"
                      @click="updateStatus(quote.id, 'approved')"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-success-500 hover:bg-success-50 dark:hover:bg-success-500/10"
                      title="Aprobar cotización"
                    >
                      <CheckIcon class="h-4 w-4" />
                    </button>
                    <button
                      v-if="quote.status === 'sent'"
                      @click="updateStatus(quote.id, 'rejected')"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-error-500 hover:bg-error-50 dark:hover:bg-error-500/10"
                      title="Rechazar cotización"
                    >
                      <TrashIcon class="h-4 w-4" />
                    </button>
                    <router-link
                      :to="`/quotes/${quote.id}`"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10"
                      title="Ver detalle"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useApi } from '@/composables/useApi'
import { RefreshIcon, SendIcon, CheckIcon, TrashIcon } from '@/icons'
import { QUOTE_STATUS_OPTIONS, getQuoteStatusLabel } from '@/constants'
import type { Quote, QuoteStatus } from '@/types'

const { get, patch } = useApi()

const quotes = ref<Quote[]>([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref<QuoteStatus | ''>('')

const filteredQuotes = computed(() => {
  let result = quotes.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter((quote) => {
      const clientName = quote.client
        ? quote.client.client_type === 'individual'
          ? `${quote.client.first_name} ${quote.client.last_name}`.toLowerCase()
          : quote.client.company_name?.toLowerCase() || ''
        : ''
      return clientName.includes(query) || quote.id.toString().includes(query)
    })
  }

  if (statusFilter.value) {
    result = result.filter((quote) => quote.status === statusFilter.value)
  }

  return result
})

const getStatusBadgeClass = (status: QuoteStatus | undefined) => {
  const classes: Record<string, string> = {
    draft: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    sent: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    approved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  }
  return classes[status || 'draft']
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatCurrency = (amount: string | undefined) => {
  if (!amount) return '$0'
  const num = parseFloat(amount)
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(num)
}

const fetchQuotes = async () => {
  loading.value = true
  try {
    const params: Record<string, string> = { limit: '50' }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    const queryString = new URLSearchParams(params).toString()
    const response = await get<Quote[]>(`/quotes/?${queryString}`)
    quotes.value = response || []
  } catch (error) {
    console.error('Error fetching quotes:', error)
  } finally {
    loading.value = false
  }
}

const updateStatus = async (quoteId: number, status: QuoteStatus) => {
  try {
    await patch(`/quotes/${quoteId}/status`, { status })
    await fetchQuotes()
  } catch (error) {
    console.error('Error updating quote status:', error)
    alert('Error al actualizar el estado de la cotización')
  }
}

onMounted(() => {
  fetchQuotes()
})
</script>

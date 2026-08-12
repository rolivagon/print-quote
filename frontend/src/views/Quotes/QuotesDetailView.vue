<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div
          class="h-10 w-10 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"
        ></div>
      </div>

      <template v-else-if="quote">
        <!-- Breadcrumb -->
        <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
          <span>/</span>
          <router-link to="/quotes" class="hover:text-brand-500">Cotizaciones</router-link>
          <span>/</span>
          <span class="text-gray-900 dark:text-white">Cotización #{{ quote.id }}</span>
        </div>

        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
              Cotización #{{ quote.id }}
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ formatDate(quote.created_at) }}
            </p>
          </div>
          <div class="flex gap-3">
            <router-link
              to="/quotes"
              class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Volver al Listado
            </router-link>
            <router-link
              to="/quotes/new"
              class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-600"
            >
              <PlusIcon class="h-4 w-4" />
              Nueva Cotización
            </router-link>
          </div>
        </div>

        <!-- Quote Status Card -->
        <div
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Estado de la Cotización
            </h2>
          </div>
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <span
                  :class="[
                    'inline-flex items-center rounded-full px-4 py-2 text-sm font-medium',
                    getStatusBadgeClass(quote.status),
                  ]"
                >
                  {{ getQuoteStatusLabel(quote.status) }}
                </span>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Última actualización: {{ formatDate(quote.updated_at || undefined) }}
                </p>
              </div>
              <div class="flex gap-2">
                <button
                  v-if="quote.status === 'draft'"
                  @click="updateStatus('sent')"
                  class="inline-flex items-center gap-2 rounded-lg bg-warning-500 px-4 py-2 text-sm font-medium text-white hover:bg-warning-600"
                >
                  <SendIcon class="h-4 w-4" />
                  Enviar al Cliente
                </button>
                <button
                  v-if="quote.status === 'sent'"
                  @click="updateStatus('approved')"
                  class="inline-flex items-center gap-2 rounded-lg bg-success-500 px-4 py-2 text-sm font-medium text-white hover:bg-success-600"
                >
                  <CheckIcon class="h-4 w-4" />
                  Aprobar
                </button>
                <button
                  v-if="quote.status === 'sent'"
                  @click="updateStatus('rejected')"
                  class="inline-flex items-center gap-2 rounded-lg bg-error-500 px-4 py-2 text-sm font-medium text-white hover:bg-error-600"
                >
                  <TrashIcon class="h-4 w-4" />
                  Rechazar
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Client Info Card -->
        <div
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Información del Cliente
            </h2>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Nombre / Razón Social</p>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{
                    quote.client?.client_type === 'individual'
                      ? `${quote.client?.first_name} ${quote.client?.last_name}`
                      : quote.client?.company_name
                  }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">RUT</p>
                <p class="font-medium text-gray-900 dark:text-white font-mono">
                  {{ quote.client?.tax_id }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Email</p>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ quote.client?.email || '-' }}
                </p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Teléfono</p>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ quote.client?.phone || '-' }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quote Items -->
        <div
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Ítems Cotizados</h2>
          </div>
          <div class="divide-y divide-gray-200 dark:divide-gray-700">
            <div v-for="(item, index) in quote.items" :key="index" class="p-6">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-3">
                    <span
                      class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-600 dark:bg-brand-900/30 dark:text-brand-400"
                    >
                      {{ index + 1 }}
                    </span>
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                      {{ item.name }}
                    </h3>
                  </div>
                  <p v-if="item.description" class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    {{ item.description }}
                  </p>

                  <div class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Cantidad</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ item.quantity }} unidades
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Dimensiones</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ formatDimensions(item.width, item.height) }}
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Tipo</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ getPrintTypeLabel(item.print_type) }}
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Color</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ COLOR_MODE_LABELS[item.color_mode || '4/0'] }}
                      </p>
                    </div>
                  </div>

                  <!-- Technical details - Only visible to admin -->
                  <div v-if="isAdmin" class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Piezas por pliego</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ item.pieces_per_sheet || '-' }}
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Pliegos necesarios</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ item.sheets_needed || '-' }}
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Material</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ item.material_cost || '$0' }}
                      </p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Terminaciones</p>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ item.finishing_cost || '$0' }}
                      </p>
                    </div>
                  </div>
                </div>
                <div class="text-right">
                  <p class="text-2xl font-bold text-brand-600 dark:text-brand-400">
                    {{ item.net_before_iva || '$0' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Totals -->
        <div
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="p-6">
            <div class="flex flex-col items-end space-y-2">
              <div class="flex w-full max-w-md justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-400">Subtotal</span>
                <span class="font-medium text-gray-900 dark:text-white">{{
                  quote.subtotal || '$0'
                }}</span>
              </div>
              <div class="flex w-full max-w-md justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-400">IVA (19%)</span>
                <span class="font-medium text-gray-900 dark:text-white">{{
                  quote.tax || '$0'
                }}</span>
              </div>
              <div
                class="flex w-full max-w-md justify-between border-t border-gray-200 pt-2 dark:border-gray-700"
              >
                <span class="text-lg font-bold text-gray-900 dark:text-white">Total</span>
                <span class="text-2xl font-bold text-brand-600 dark:text-brand-400">{{
                  quote.total || '$0'
                }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Materials Section (Admin Only) -->
        <div
          v-if="isAdmin"
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div
            class="border-b border-gray-200 px-6 py-4 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
          >
            <div class="flex items-center gap-2">
              <svg
                class="h-5 w-5 text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                Detalle de Materiales (Solo Admin)
              </h2>
            </div>
          </div>
          <div class="p-6">
            <div class="space-y-6">
              <div
                v-for="(item, index) in quote.items"
                :key="`material-${index}`"
                class="border border-gray-200 rounded-lg p-4 dark:border-gray-700"
              >
                <h4 class="font-medium text-gray-900 dark:text-white mb-3">
                  {{ index + 1 }}. {{ item.name }}
                </h4>

                <!-- Información de Producción -->
                <div class="mb-4 pb-4 border-b border-gray-100 dark:border-gray-800">
                  <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Producción
                  </h5>
                  <div class="grid grid-cols-2 gap-4 md:grid-cols-4 text-sm">
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Cantidad por pliego</p>
                      <p class="font-mono">{{ item.pieces_per_sheet || '-' }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Pliegos necesarios</p>
                      <p class="font-mono">{{ item.sheets_needed || '-' }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Resmas</p>
                      <p class="font-mono">{{ Math.ceil((item.sheets_needed || 0) / 500) }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Pliegos con merma</p>
                      <p class="font-mono">{{ item.total_sheets_with_merma || '-' }}</p>
                    </div>
                  </div>
                </div>

                <!-- Precios -->
                <div class="mb-4 pb-4 border-b border-gray-100 dark:border-gray-800">
                  <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Precios</h5>
                  <div class="grid grid-cols-2 gap-4 md:grid-cols-4 text-sm">
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">{{ getPaperName(item) }}</p>
                      <p class="font-mono">{{ item.paper_unit_price }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Costo material</p>
                      <p class="font-mono">{{ item.material_cost || '$0' }}</p>
                    </div>
                    <div class="col-span-2">
                      <p class="text-gray-500 dark:text-gray-400">Terminaciones</p>
                      <div
                        v-if="item.calculation_details?.specifications?.finishes?.length"
                        class="space-y-1"
                      >
                        <div
                          v-for="finish in item.calculation_details.specifications.finishes"
                          :key="finish.id"
                          class="flex justify-between"
                        >
                          <span>{{ finish.name }}</span>
                          <span class="font-mono">{{ finish.calculated_cost }}</span>
                        </div>
                      </div>
                      <p v-else class="font-mono">{{ item.finishing_cost || '$0' }}</p>
                    </div>
                  </div>
                </div>

                <!-- Costos Offset (solo si aplica) -->
                <div
                  v-if="item.print_type === 'offset'"
                  class="mb-4 pb-4 border-b border-gray-100 dark:border-gray-800"
                >
                  <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Costos Offset
                  </h5>
                  <div class="grid grid-cols-2 gap-4 md:grid-cols-4 text-sm">
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Planchas</p>
                      <p class="font-mono">{{ item.plates_cost || '$0' }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Tiraje</p>
                      <p class="font-mono">{{ item.run_cost || '$0' }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">Costos fijos</p>
                      <p class="font-mono">{{ item.fixed_costs || '$0' }}</p>
                    </div>
                    <div>
                      <p class="text-gray-500 dark:text-gray-400">N° Diseños</p>
                      <p class="font-mono">{{ item.num_designs || 1 }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Error State -->
      <div v-else class="text-center py-20">
        <p class="text-gray-500 dark:text-gray-400">No se encontró la cotización</p>
        <router-link
          to="/quotes"
          class="mt-4 inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
        >
          Volver al Listado
        </router-link>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { PlusIcon, SendIcon, CheckIcon, TrashIcon } from '@/icons'
import { getQuoteStatusLabel, COLOR_MODE_LABELS } from '@/constants'
import { getPrintTypeLabel } from '@/constants'
import type { Quote, QuoteStatus } from '@/types'

const route = useRoute()
const router = useRouter()
const { get, patch } = useApi()
const authStore = useAuthStore()

const quote = ref<Quote | null>(null)
const loading = ref(true)

const isAdmin = computed(() => authStore.isAdmin)

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
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
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

const formatDimensions = (
  width: number | string | undefined,
  height: number | string | undefined,
) => {
  if (!width || !height) return '-'
  const w = Number(width)
  const h = Number(height)
  // Format without unnecessary decimals (e.g., 30.00 -> 30)
  const formatNumber = (n: number) => {
    return n % 1 === 0 ? n.toString() : n.toFixed(2).replace(/\.?0+$/, '')
  }
  return `${formatNumber(w)}x${formatNumber(h)} cm`
}

const getPaperName = (item: any) => {
  // Get paper name from calculation_details if available
  if (item.calculation_details?.specifications?.paper?.name) {
    return item.calculation_details.specifications.paper.name
  }
  // Fallback to generic label
  return 'Papel'
}

const fetchQuote = async () => {
  const quoteId = route.params.id as string
  loading.value = true

  try {
    const response = await get<Quote>(`/quotes/${quoteId}`)
    quote.value = response
  } catch (error) {
    console.error('Error fetching quote:', error)
  } finally {
    loading.value = false
  }
}

const updateStatus = async (status: QuoteStatus) => {
  if (!quote.value) return

  try {
    await patch(`/quotes/${quote.value.id}/status`, { status })
    await fetchQuote()
  } catch (error) {
    console.error('Error updating quote status:', error)
    alert('Error al actualizar el estado de la cotización')
  }
}

onMounted(() => {
  fetchQuote()
})
</script>

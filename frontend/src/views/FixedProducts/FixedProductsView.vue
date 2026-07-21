<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Productos Fijos</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Productos Fijos</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Gestionar productos con precios predefinidos por cantidad
          </p>
        </div>
      </div>

      <!-- Success Message -->
      <div
        v-if="successMessage"
        class="rounded-lg bg-success-50 p-4 text-sm text-success-700 dark:bg-success-500/10 dark:text-success-500"
      >
        <div class="flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          {{ successMessage }}
        </div>
      </div>

      <!-- List View -->
      <div
        class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <!-- Search & Filters -->
        <div class="border-b border-gray-200 p-4 dark:border-gray-700">
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="relative flex-1 max-w-md">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Buscar productos..."
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
            <select
              v-model="printTypeFilter"
              class="h-11 rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
            >
              <option value="">Todos los tipos</option>
              <option value="digital">Digital</option>
              <option value="offset">Offset</option>
              <option value="plotter">Plotter</option>
            </select>
          </div>
        </div>

        <!-- Table -->
        <div class="max-w-full overflow-x-auto">
          <table class="min-w-full">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="px-5 py-3 text-left sm:px-6">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Producto</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Tipo</p>
                </th>
                <th class="px-5 py-3 text-center sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Rangos</p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-48">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Acciones</p>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="product in filteredProducts"
                :key="product.id"
                class="border-b border-gray-200 last:border-b-0 dark:border-gray-700"
              >
                <td class="px-5 py-4 sm:px-6">
                  <div>
                    <p class="font-medium text-gray-900 dark:text-white">{{ product.name }}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      ID: {{ product.product_id }}
                    </p>
                    <p
                      v-if="product.client_id"
                      class="text-xs text-brand-600 dark:text-brand-400 mt-1"
                    >
                      Cliente específico
                    </p>
                  </div>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <span
                    class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-800 dark:text-gray-200"
                  >
                    {{ formatPrintType(product.print_type) }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6 text-center">
                  <span
                    class="inline-flex items-center justify-center h-8 w-8 rounded-full bg-brand-100 text-sm font-medium text-brand-600 dark:bg-brand-900/30 dark:text-brand-400"
                  >
                    {{ product.ranges?.length || 0 }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="viewProduct(product)"
                      class="inline-flex items-center gap-1 rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
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
                    </button>
                    <button
                      @click="deleteProduct(product)"
                      :disabled="deletingId === product.id"
                      class="inline-flex items-center gap-1 rounded-lg p-2 text-error-500 hover:bg-error-50 hover:text-error-600 dark:hover:bg-error-500/10"
                      title="Eliminar producto"
                    >
                      <svg
                        v-if="deletingId === product.id"
                        class="h-4 w-4 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          class="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          stroke-width="4"
                        />
                        <path
                          class="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      <svg
                        v-else
                        class="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredProducts.length === 0">
                <td colspan="4" class="px-5 py-8 text-center text-gray-500 dark:text-gray-400">
                  <p v-if="loading">Cargando productos...</p>
                  <p v-else>No hay productos fijos configurados</p>
                  <p class="text-sm mt-2">Los productos se crean desde la pantalla de cotización</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Product Detail Modal -->
    <Modal v-if="selectedProduct" v-model="showDetailModal" :title="selectedProduct.name" size="lg">
      <div class="space-y-6">
        <!-- Product Info -->
        <div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
          <h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Información del Producto
          </h4>
          <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <p><span class="font-medium">ID:</span> {{ selectedProduct.product_id }}</p>
            <p>
              <span class="font-medium">Tipo:</span>
              {{ formatPrintType(selectedProduct.print_type) }}
            </p>
            <p v-if="selectedProduct.client_id">
              <span class="font-medium">Cliente:</span> Específico
            </p>
            <p v-else><span class="font-medium">Cliente:</span> Global</p>
          </div>
        </div>

        <!-- Snapshot Info -->
        <div v-if="selectedProduct.snapshot" class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
          <h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Configuración Base
          </h4>
          <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <p>
              <span class="font-medium">Cantidad ref:</span>
              {{ selectedProduct.snapshot.reference_quantity }}
            </p>
            <p>
              <span class="font-medium">Dimensiones:</span>
              {{ selectedProduct.snapshot.dimensions?.width_cm }}x{{
                selectedProduct.snapshot.dimensions?.height_cm
              }}
              cm
            </p>
            <p>
              <span class="font-medium">Piezas/pliego:</span>
              {{ selectedProduct.snapshot.pieces_per_sheet }}
            </p>
          </div>
        </div>

        <!-- Range Manager -->
        <FixedProductRanges :product-id="selectedProduct.product_id" @saved="onRangesSaved" />

        <!-- Close Button -->
        <div class="flex justify-end pt-4">
          <button
            @click="showDetailModal = false"
            class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
          >
            Cerrar
          </button>
        </div>
      </div>
    </Modal>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import Modal from '@/components/ui/Modal.vue'
import FixedProductRanges from '@/components/fixed-products/FixedProductRanges.vue'
import { useApi } from '@/composables/useApi'

interface FixedProduct {
  id: string
  product_id: string
  name: string
  print_type: string
  client_id: number | null
  ranges?: Array<{
    id: string
    min_qty: number
    max_qty: number
    unit_price: string
  }>
  snapshot?: {
    reference_quantity: number
    dimensions?: {
      width_cm: number
      height_cm: number
    }
    pieces_per_sheet?: number
  }
}

const { get, del } = useApi()

const products = ref<FixedProduct[]>([])
const loading = ref(false)
const deletingId = ref<string | null>(null)
const searchQuery = ref('')
const printTypeFilter = ref('')
const successMessage = ref('')

const selectedProduct = ref<FixedProduct | null>(null)
const showDetailModal = ref(false)

const filteredProducts = computed(() => {
  let result = products.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(
      (p) => p.name.toLowerCase().includes(query) || p.product_id.toLowerCase().includes(query),
    )
  }

  if (printTypeFilter.value) {
    result = result.filter((p) => p.print_type === printTypeFilter.value)
  }

  return result
})

const formatPrintType = (type: string): string => {
  const labels: Record<string, string> = {
    digital: 'Digital',
    offset: 'Offset',
    plotter: 'Plotter',
  }
  return labels[type] || type
}

const loadProducts = async () => {
  loading.value = true
  try {
    const response = await get<{ items: FixedProduct[] }>('/fixed-products')
    products.value = response.items || []
  } catch (error) {
    console.error('Error loading products:', error)
  } finally {
    loading.value = false
  }
}

const viewProduct = (product: FixedProduct) => {
  selectedProduct.value = product
  showDetailModal.value = true
}

const deleteProduct = async (product: FixedProduct) => {
  if (!confirm(`¿Estás seguro de eliminar el producto "${product.name}"?`)) {
    return
  }

  deletingId.value = product.id
  try {
    await del(`/fixed-products/${product.id}`)
    successMessage.value = 'Producto eliminado exitosamente'
    setTimeout(() => (successMessage.value = ''), 5000)
    await loadProducts()
  } catch (error) {
    console.error('Error deleting product:', error)
  } finally {
    deletingId.value = null
  }
}

const onRangesSaved = () => {
  successMessage.value = 'Rangos actualizados'
  setTimeout(() => (successMessage.value = ''), 3000)
  loadProducts()
}

onMounted(() => {
  loadProducts()
})
</script>

<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <router-link to="/quotes" class="hover:text-brand-500">Cotizaciones</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Nueva Cotización</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Nueva Cotización</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Crea una nueva cotización con múltiples ítems
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
        </div>
      </div>

      <!-- Success/Error Message -->
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

      <div
        v-if="errorMessage"
        class="rounded-lg bg-error-50 p-4 text-sm text-error-700 dark:bg-error-500/10 dark:text-error-500"
      >
        <div class="flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
          {{ errorMessage }}
        </div>
      </div>

      <!-- Form -->
      <form @submit.prevent="submitQuote" class="space-y-6">
        <!-- Client Selection -->
        <div
          class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Información General</h2>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                  Cliente <span class="text-error-500">*</span>
                </label>
                <select
                  v-model="formData.client_id"
                  required
                  class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                >
                  <option value="">Selecciona un cliente</option>
                  <option v-for="client in clients" :key="client.id" :value="client.id">
                    {{
                      client.client_type === 'individual'
                        ? `${client.first_name} ${client.last_name} (${client.tax_id})`
                        : `${client.company_name} (${client.tax_id})`
                    }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Quote Items -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Ítems de la Cotización
            </h2>
            <button
              type="button"
              @click="addItem"
              class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-600"
            >
              <PlusIcon class="h-4 w-4" />
              Agregar Ítem
            </button>
          </div>

          <div
            v-for="(item, index) in formData.items"
            :key="index"
            class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
          >
            <!-- Item Header -->
            <div
              class="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-6 py-3 dark:border-gray-700 dark:bg-gray-800/50"
            >
              <div class="flex items-center gap-3">
                <span
                  class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-600 dark:bg-brand-900/30 dark:text-brand-400"
                >
                  {{ index + 1 }}
                </span>
                <h3 class="font-medium text-gray-900 dark:text-white">
                  {{ item.name || 'Nuevo Ítem' }}
                </h3>
              </div>
              <button
                v-if="formData.items.length > 1"
                type="button"
                @click="removeItem(index)"
                class="text-error-500 hover:text-error-600"
              >
                <TrashIcon class="h-5 w-5" />
              </button>
            </div>

            <!-- Item Form -->
            <div class="p-6 space-y-6">
              <!-- Row 1: Name, Description -->
              <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Nombre del trabajo <span class="text-error-500">*</span>
                  </label>
                  <input
                    v-model="item.name"
                    type="text"
                    required
                    placeholder="Ej: Flyers Corporativos"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Descripción
                  </label>
                  <input
                    v-model="item.description"
                    type="text"
                    placeholder="Descripción opcional"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
              </div>

              <!-- Row 2: Print Type, Color Mode -->
              <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Tipo de impresión <span class="text-error-500">*</span>
                  </label>
                  <select
                    v-model="item.print_type"
                    required
                    @change="onPrintTypeChange(index)"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  >
                    <option
                      v-for="option in PRINT_TYPE_OPTIONS"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </div>
                <div v-if="item.print_type !== 'plotter'">
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Modo de color <span class="text-error-500">*</span>
                  </label>
                  <select
                    v-model="item.color_mode"
                    required
                    @change="onColorModeChange(index)"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  >
                    <option value="">Selecciona modo de color</option>
                    <option
                      v-for="option in COLOR_MODE_OPTIONS"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }} - {{ option.description }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Row 3: Quantity, Dimensions -->
              <div class="grid grid-cols-1 gap-6 md:grid-cols-4">
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Cantidad <span class="text-error-500">*</span>
                  </label>
                  <input
                    v-model.number="item.quantity"
                    type="number"
                    required
                    min="1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Ancho (cm) <span class="text-error-500">*</span>
                  </label>
                  <input
                    v-model.number="item.width_cm"
                    type="number"
                    required
                    min="0.1"
                    step="0.1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Alto (cm) <span class="text-error-500">*</span>
                  </label>
                  <input
                    v-model.number="item.height_cm"
                    type="number"
                    required
                    min="0.1"
                    step="0.1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    % Merma
                  </label>
                  <input
                    v-model.number="item.loss_percentage"
                    type="number"
                    min="0"
                    max="100"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
              </div>

              <!-- Row 4: Paper -->
              <div>
                <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                  Papel <span class="text-error-500">*</span>
                </label>
                <select
                  v-model="item.paper_id"
                  required
                  :disabled="item.print_type !== 'plotter' && !item.color_mode"
                  class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {{
                      item.print_type === 'plotter'
                         ? 'Selecciona un material'
                         : item.color_mode
                           ? 'Selecciona un papel'
                           : 'Primero selecciona modo de color'
                    }}
                  </option>
                  <option
                    v-for="paper in getAvailablePapers(index)"
                    :key="paper.id"
                    :value="paper.id"
                  >
                    {{ paper.name }}{{ item.print_type === 'plotter' ? '' : ` (${paper.weight}g)` }}
                  </option>
                </select>
              </div>

              <!-- Row 5: Sheet Config (Digital/Offset only) -->
              <div
                v-if="item.print_type !== 'plotter' && item.sheet_config"
                class="grid grid-cols-1 gap-6 md:grid-cols-2"
              >
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Ancho pliego usable (cm)
                  </label>
                  <input
                    v-model.number="item.sheet_config.usable_width_cm"
                    type="number"
                    required
                    min="0.1"
                    step="0.1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Alto pliego usable (cm)
                  </label>
                  <input
                    v-model.number="item.sheet_config.usable_height_cm"
                    type="number"
                    required
                    min="0.1"
                    step="0.1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
              </div>

              <!-- Row 6: Finishes -->
              <div>
                <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                  Terminaciones
                </label>
                <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <label
                    v-for="finish in getAvailableFinishes(item.print_type)"
                    :key="finish.id"
                    class="flex items-center gap-2 rounded-lg border border-gray-200 p-3 cursor-pointer hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
                  >
                    <input
                      type="checkbox"
                      :value="finish.id"
                      v-model="item.finishes"
                      class="h-4 w-4 rounded border-gray-300 text-brand-500 focus:ring-brand-500"
                    />
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ finish.name }}</span>
                  </label>
                </div>
                <p
                  v-if="getAvailableFinishes(item.print_type).length === 0"
                  class="text-sm text-gray-500 mt-2"
                >
                  No hay terminaciones disponibles para este tipo de impresión
                </p>
              </div>

              <!-- Row 7: Offset-specific fields -->
              <div
                v-if="item.print_type === 'offset'"
                class="grid grid-cols-1 gap-6 md:grid-cols-2 border-t border-gray-200 pt-6 dark:border-gray-700"
              >
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Número de diseños
                  </label>
                  <input
                    v-model.number="item.num_designs"
                    type="number"
                    min="1"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
                <div>
                  <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-400">
                    Merma por diseño
                  </label>
                  <input
                    v-model.number="item.merma_per_design"
                    type="number"
                    min="0"
                    class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Submit Buttons -->
        <div class="flex items-center justify-end gap-3">
          <router-link
            to="/quotes"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Cancelar
          </router-link>
          <button
            v-if="isAdmin && formData.items.length > 0"
            type="button"
            @click="openCreateProductModal"
            class="inline-flex items-center gap-2 rounded-lg border border-brand-300 bg-brand-50 px-6 py-2.5 text-sm font-medium text-brand-700 hover:bg-brand-100 dark:border-brand-700 dark:bg-brand-900/30 dark:text-brand-400 dark:hover:bg-brand-900/50"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Crear como Producto
          </button>
          <button
            type="submit"
            :disabled="submitting"
            class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div
              v-if="submitting"
              class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            ></div>
            <span v-else>Crear Cotización</span>
          </button>
        </div>
      </form>
    </div>

    <!-- Create Fixed Product Modal -->
    <CreateFixedProductModal
      v-if="showCreateProductModal && selectedItemForProduct"
      v-model="showCreateProductModal"
      :quote-data="selectedItemForProduct"
      :paper-name="getSelectedPaperName(selectedItemForProduct)"
      @created="onProductCreated"
    />
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useApi } from '@/composables/useApi'
import { PlusIcon, TrashIcon } from '@/icons'
import { PRINT_TYPE_OPTIONS, COLOR_MODE_OPTIONS, DEFAULT_SHEET_CONFIGS } from '@/constants'
import type {
  Client,
  Paper,
  Finish,
  QuoteCreateRequest,
  QuoteItem,
  PrintType,
  ColorMode,
} from '@/types'
import CreateFixedProductModal from '@/components/fixed-products/CreateFixedProductModal.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { get, post } = useApi()
const authStore = useAuthStore()

const clients = ref<Client[]>([])
const papers = ref<Paper[]>([])
const finishes = ref<Finish[]>([])
const plotterFinishes = ref<Finish[]>([])
const paperPricings = ref<Record<number, string[]>>({})
const finishPricings = ref<Record<number, string[]>>({})
const filteredPapers = ref<Record<number, Paper[]>>({})
const submitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Fixed Product Modal State
const isAdmin = computed(() => authStore.isAdmin)
const showCreateProductModal = ref(false)
const selectedItemForProduct = ref<QuoteItem | null>(null)

const openCreateProductModal = () => {
  // Use the first item for creating a fixed product
  if (formData.items.length > 0) {
    selectedItemForProduct.value = formData.items[0]
    showCreateProductModal.value = true
  }
}

const onProductCreated = () => {
  successMessage.value = 'Producto fijo creado exitosamente'
  setTimeout(() => {
    successMessage.value = ''
  }, 5000)
}

const getSelectedPaperName = (item: QuoteItem): string => {
  const paper = papers.value.find((p) => p.id === item.paper_id)
  return paper ? paper.name : 'Papel no seleccionado'
}

const formData = reactive<QuoteCreateRequest>({
  client_id: 0,
  items: [],
})

const createEmptyItem = (): QuoteItem => ({
  name: '',
  description: '',
  print_type: 'digital',
  quantity: 100,
  width_cm: 10,
  height_cm: 15,
  paper_id: 0,
  color_mode: '',
  sheet_config: { ...DEFAULT_SHEET_CONFIGS.digital },
  finishes: [],
  loss_percentage: 0,
})

const addItem = () => {
  formData.items.push(createEmptyItem())
}

const removeItem = (index: number) => {
  formData.items.splice(index, 1)
}

const loadAvailablePapers = async (index: number) => {
  const item = formData.items[index]
  if (!item.print_type || (item.print_type !== 'plotter' && !item.color_mode)) {
    filteredPapers.value[index] = []
    return
  }

  try {
    const colorMode = item.print_type === 'plotter' ? '' : `&color_mode=${item.color_mode}`
    const response = await get<Paper[]>(
      `/papers/?print_type=${item.print_type}${colorMode}`,
    )
    filteredPapers.value[index] = response || []
  } catch (error) {
    console.error('Error loading filtered papers:', error)
    filteredPapers.value[index] = []
  }
}

const onPrintTypeChange = async (index: number) => {
  const item = formData.items[index]
  const printType = item.print_type

  // Reset paper, color_mode and finishes
  item.paper_id = 0
  item.color_mode = ''
  item.finishes = []

  // Apply default sheet config
  if (printType === 'digital') {
    item.sheet_config = { ...DEFAULT_SHEET_CONFIGS.digital }
  } else if (printType === 'offset') {
    item.sheet_config = { ...DEFAULT_SHEET_CONFIGS.offset }
  }
  // Plotter doesn't use sheet_config

  // Add offset-specific fields
  if (printType === 'offset') {
    item.num_designs = 1
    item.merma_per_design = 0
  } else {
    delete item.num_designs
    delete item.merma_per_design
  }

  await loadAvailablePapers(index)
}

const onColorModeChange = async (index: number) => {
  const item = formData.items[index]

  // Reset paper selection when color mode changes
  item.paper_id = 0

  await loadAvailablePapers(index)
}

const getAvailablePapers = (index: number) => {
  // Return filtered papers for this item index
  return filteredPapers.value[index] || []
}

const getAvailableFinishes = (printType: PrintType) => {
  if (printType === 'plotter') {
    return plotterFinishes.value
  }

  return finishes.value.filter((finish) => {
    const pricings = finishPricings.value[finish.id] || []
    return pricings.includes(printType)
  })
}

const loadPricingInfo = async () => {
  // Load paper pricings
  for (const paper of papers.value) {
    try {
      const response = await get<{ print_type: string }[]>(`/papers/${paper.id}/pricing`)
      paperPricings.value[paper.id] = (response || []).map((p) => p.print_type)
    } catch (error) {
      paperPricings.value[paper.id] = []
    }
  }

  // Load finish pricings
  for (const finish of finishes.value) {
    try {
      const response = await get<{ print_type: string }[]>(`/finishes/${finish.id}/pricing`)
      finishPricings.value[finish.id] = (response || []).map((p) => p.print_type)
    } catch (error) {
      finishPricings.value[finish.id] = []
    }
  }
}

const submitQuote = async () => {
  if (!formData.client_id) {
    errorMessage.value = 'Debes seleccionar un cliente'
    return
  }

  if (formData.items.length === 0) {
    errorMessage.value = 'Debes agregar al menos un ítem'
    return
  }

  // Validate items
  for (const item of formData.items) {
    if (!item.name || !item.quantity || !item.width_cm || !item.height_cm || !item.paper_id) {
      errorMessage.value = 'Todos los campos obligatorios deben estar completos'
      return
    }
  }

  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const payload = {
      ...formData,
      items: formData.items.map((item) => ({
        ...item,
        ...(item.print_type === 'plotter'
          ? {
              color_mode: '4/0',
              material_type: papers.value.find((paper) => paper.id === item.paper_id)?.name,
            }
          : {}),
      })),
    }
    const response = await post<{ id: number }>('/quotes/', payload)
    successMessage.value = 'Cotización creada exitosamente'

    // Redirect to quote detail after a short delay
    setTimeout(() => {
      router.push(`/quotes/${response.id}`)
    }, 1500)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || 'Error al crear la cotización'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    // Load clients
    const clientsResponse = await get<Client[]>('/clients/')
    clients.value = clientsResponse || []

    // Load papers
    const papersResponse = await get<Paper[]>('/papers/')
    papers.value = papersResponse || []

    // Load finishes
    const finishesResponse = await get<Finish[]>('/finishes/')
    finishes.value = finishesResponse || []

    // Plotter finishes use the separate plotter pricing catalog.
    const plotterFinishesResponse = await get<Finish[]>('/finishes/?print_type=plotter')
    plotterFinishes.value = plotterFinishesResponse || []

    // Load pricing info
    await loadPricingInfo()

    // Add first item
    addItem()
  } catch (error) {
    console.error('Error loading data:', error)
    errorMessage.value = 'Error al cargar los datos iniciales'
  }
})
</script>

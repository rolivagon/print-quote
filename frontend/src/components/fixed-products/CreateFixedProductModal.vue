<template>
  <Teleport to="body">
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm" @click="closeModal"></div>

      <!-- Modal Content -->
      <div class="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <!-- Header -->
        <div class="mb-6 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Crear Producto Fijo</h2>
          <button
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="space-y-6">
          <!-- Product ID -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              ID del Producto <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.product_id"
              type="text"
              placeholder="Ej: roller-80x200-sintetico"
              class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:border-gray-700 dark:bg-gray-900"
            />
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Identificador único, sin espacios (ej: producto-nombre)
            </p>
          </div>

          <!-- Product Name -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Nombre del Producto <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="Ej: Roller 80x200 Sintético"
              class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:border-gray-700 dark:bg-gray-900"
            />
          </div>

          <!-- Client Selector (optional) -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Cliente Específico (opcional)
            </label>
            <select
              v-model="formData.client_id"
              class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:border-gray-700 dark:bg-gray-900"
            >
              <option :value="null">Producto Global (visible para todos)</option>
              <option v-for="client in clients" :key="client.id" :value="client.id">
                {{
                  client.client_type === 'individual'
                    ? `${client.first_name} ${client.last_name}`
                    : client.company_name
                }}
              </option>
            </select>
          </div>

          <!-- Quote Data Preview -->
          <div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
            <h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Datos de la Cotización Base
            </h4>
            <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <p><span class="font-medium">Tipo:</span> {{ printTypeLabel }}</p>
              <p><span class="font-medium">Cantidad ref:</span> {{ quoteData.quantity }}</p>
              <p>
                <span class="font-medium">Dimensiones:</span> {{ quoteData.width_cm }}x{{
                  quoteData.height_cm
                }}
                cm
              </p>
              <p><span class="font-medium">Papel:</span> {{ paperName }}</p>
              <p><span class="font-medium">Modo color:</span> {{ quoteData.color_mode }}</p>
            </div>
          </div>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="rounded-lg bg-error-50 p-3 text-sm text-error-700 dark:bg-error-500/10 dark:text-error-500"
          >
            {{ errorMessage }}
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              @click="closeModal"
              :disabled="saving"
              class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
            >
              Cancelar
            </button>
            <button
              @click="createProduct"
              :disabled="saving || !isValid"
              class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
            >
              <svg v-if="saving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
              <span>{{ saving ? 'Creando...' : 'Crear Producto' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Client, QuoteItem } from '@/types'

interface Props {
  modelValue: boolean
  quoteData: QuoteItem
  paperName: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  created: []
}>()

const { get, post } = useApi()

const clients = ref<Client[]>([])
const saving = ref(false)
const errorMessage = ref('')

const formData = ref({
  product_id: '',
  name: '',
  client_id: null as number | null,
})

const showModal = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const printTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    digital: 'Digital',
    offset: 'Offset',
    plotter: 'Plotter',
  }
  return labels[props.quoteData.print_type] || props.quoteData.print_type
})

const isValid = computed(() => {
  return formData.value.product_id.trim() !== '' && formData.value.name.trim() !== ''
})

const closeModal = () => {
  showModal.value = false
  errorMessage.value = ''
  formData.value = {
    product_id: '',
    name: '',
    client_id: null,
  }
}

const createProduct = async () => {
  if (!isValid.value) {
    errorMessage.value = 'Por favor completa todos los campos requeridos'
    return
  }

  saving.value = true
  errorMessage.value = ''

  try {
    // Construir el payload según el tipo de impresión
    let quoteDataPayload: any = {
      print_type: props.quoteData.print_type,
      quantity: props.quoteData.quantity,
      dimensions: {
        width_cm: props.quoteData.width_cm,
        height_cm: props.quoteData.height_cm,
      },
      finishes: props.quoteData.finishes || [],
      loss_percentage: props.quoteData.loss_percentage || 0,
    }

    // Agregar campos específicos según el tipo de impresión
    if (props.quoteData.print_type === 'digital') {
      quoteDataPayload = {
        ...quoteDataPayload,
        paper_id: props.quoteData.paper_id,
        color_mode: props.quoteData.color_mode,
        sheet_config: props.quoteData.sheet_config,
        geometry: {
          bleed_mm: 3,
          margin_mm: 5,
          gap_mm: 3,
          allow_rotate: true,
        },
      }
    } else if (props.quoteData.print_type === 'offset') {
      quoteDataPayload = {
        ...quoteDataPayload,
        paper_id: props.quoteData.paper_id,
        color_mode: props.quoteData.color_mode,
        sheet_config: props.quoteData.sheet_config,
        geometry: {
          bleed_mm: 3,
          margin_mm: 5,
          gap_mm: 3,
          allow_rotate: true,
        },
        num_designs: props.quoteData.num_designs || 1,
        merma_per_design: props.quoteData.merma_per_design || 0,
      }
    } else if (props.quoteData.print_type === 'plotter') {
      quoteDataPayload = {
        ...quoteDataPayload,
        material_type: props.paperName || 'sintetico',
        minimum_m2: 0.5,
      }
    }

    const payload = {
      product_id: formData.value.product_id,
      name: formData.value.name,
      client_id: formData.value.client_id,
      quote_data: quoteDataPayload,
    }

    await post('/fixed-products/from-quote', payload)

    emit('created')
    closeModal()
  } catch (err: any) {
    console.error('Error creating product:', err)
    errorMessage.value = err?.response?.data?.detail || err.message || 'Error al crear el producto'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const response = await get<Client[]>('/clients/')
    clients.value = response || []
  } catch (error) {
    console.error('Error loading clients:', error)
  }
})
</script>

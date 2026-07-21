<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Rangos de Precio</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Configurar precios por cantidad para este producto
        </p>
      </div>
    </div>

    <!-- Saved Ranges List -->
    <div v-if="savedRanges.length > 0" class="space-y-4">
      <div
        v-for="range in savedRanges"
        :key="range.id"
        class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300"> Rango Guardado </span>
          <div class="flex items-center gap-1">
            <button
              v-if="editingRangeId !== range.id"
              @click="startEdit(range)"
              class="inline-flex items-center gap-1 rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
              title="Editar"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              v-if="editingRangeId !== range.id"
              @click="deleteRange(range)"
              :disabled="deletingId === range.id"
              class="inline-flex items-center gap-1 rounded-lg p-2 text-error-500 hover:bg-error-50 hover:text-error-600 dark:hover:bg-error-500/10"
              title="Eliminar"
            >
              <svg
                v-if="deletingId === range.id"
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
              <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">Mín:</span>
            <span class="ml-1 font-medium">{{ range.min_qty }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Máx:</span>
            <span class="ml-1 font-medium">{{ range.max_qty || '∞' }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400">Precio:</span>
            <template v-if="editingRangeId === range.id">
              <div class="relative flex items-center gap-2">
                <span class="absolute left-2 text-gray-500 dark:text-gray-400 text-sm">$</span>
                <input
                  v-model="editingPrice"
                  type="number"
                  min="0"
                  step="0.01"
                  class="h-8 w-24 rounded-lg border border-gray-300 bg-transparent pl-6 pr-2 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
                  placeholder="0.00"
                  @keyup.enter="saveEditRange"
                  @keyup.esc="cancelEdit"
                />
                <button
                  @click="saveEditRange"
                  :disabled="updatingId === range.id"
                  class="inline-flex items-center justify-center rounded-lg p-1.5 text-success-500 hover:bg-success-50 dark:hover:bg-success-500/10"
                >
                  <svg
                    v-if="updatingId === range.id"
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
                  <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </button>
                <button
                  @click="cancelEdit"
                  :disabled="updatingId === range.id"
                  class="inline-flex items-center justify-center rounded-lg p-1.5 text-error-500 hover:bg-error-50 dark:hover:bg-error-500/10"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </template>
            <template v-else>
              <span class="ml-1 font-medium">{{ formatPrice(range.unit_price) }}</span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- New Range Form -->
    <div
      v-if="showNewRangeForm"
      class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]"
    >
      <div class="flex items-center justify-between mb-4">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Agregar Nuevo Rango</h4>
        <div class="flex items-center gap-2">
          <button
            @click="cancelNewRange"
            :disabled="saving"
            class="inline-flex items-center justify-center rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
          <button
            @click="saveNewRange"
            :disabled="saving"
            class="inline-flex items-center justify-center rounded-lg p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 disabled:opacity-50"
          >
            <svg v-if="saving" class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
            <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-400">
            Cantidad Mínima <span class="text-error-500">*</span>
          </label>
          <input
            v-model.number="newRange.min_qty"
            type="number"
            min="1"
            :disabled="newRange.min_qty <= 1"
            class="h-10 w-full rounded-lg border bg-gray-100 px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:bg-gray-800 dark:text-gray-400 cursor-not-allowed"
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-400">
            Cantidad Máxima
          </label>
          <input
            v-model.number="newRange.max_qty"
            type="number"
            :min="newRange.min_qty"
            placeholder="Sin límite"
            class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:border-gray-700 dark:bg-gray-900"
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-400">
            Precio Unitario <span class="text-error-500">*</span>
          </label>
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400"
              >$</span
            >
            <input
              v-model="newRange.unit_price"
              type="text"
              placeholder="0.00"
              class="h-10 w-full rounded-lg border border-gray-300 bg-transparent pl-8 pr-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:border-gray-700 dark:bg-gray-900"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="savedRanges.length === 0 && !showNewRangeForm"
      class="rounded-xl border border-gray-200 bg-white p-8 text-center dark:border-gray-800 dark:bg-white/[0.03]"
    >
      <p class="text-sm text-gray-500 dark:text-gray-400">No hay rangos de precio definidos</p>
    </div>

    <!-- Add Button -->
    <div v-if="!showNewRangeForm" class="flex justify-center">
      <button
        @click="startAddingRange"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        {{ savedRanges.length === 0 ? 'Agregar Primer Rango' : 'Agregar Rango' }}
      </button>
    </div>

    <!-- Messages -->
    <div
      v-if="message"
      :class="[
        'rounded-lg p-4 text-sm',
        messageType === 'success'
          ? 'bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-500'
          : 'bg-error-50 text-error-700 dark:bg-error-500/10 dark:text-error-500',
      ]"
    >
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useApi } from '@/composables/useApi'

interface Range {
  id: string
  min_qty: number
  max_qty: number | null
  unit_price: string
}

interface Props {
  productId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  saved: []
}>()

const { get, post, patch, del } = useApi()

// State
const ranges = ref<Range[]>([])
const showNewRangeForm = ref(false)
const saving = ref(false)
const deletingId = ref<string | null>(null)
const editingRangeId = ref<string | null>(null)
const editingPrice = ref('')
const updatingId = ref<string | null>(null)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const newRange = ref({
  min_qty: 1,
  max_qty: null as number | null,
  unit_price: '',
})

// Computed
const savedRanges = computed(() => ranges.value)

// Methods
const loadRanges = async () => {
  try {
    const response = await get<{
      ranges: Range[]
    }>(`/fixed-products/${props.productId}`)
    ranges.value = response.ranges || []
    resetNewRange()
  } catch (err) {
    showMessage('Error al cargar rangos', 'error')
  }
}

const resetNewRange = () => {
  const existingRanges = ranges.value
  let nextMinQty = 1

  if (existingRanges.length > 0) {
    const lastRange = existingRanges.reduce((max, range) => {
      const currentMax = range.max_qty ?? Infinity
      const maxSoFar = max.max_qty ?? Infinity
      return currentMax > maxSoFar ? range : max
    })

    if (lastRange.max_qty !== null && lastRange.max_qty !== undefined) {
      nextMinQty = lastRange.max_qty + 1
    } else {
      nextMinQty = lastRange.min_qty + 1
    }
  }

  newRange.value = {
    min_qty: nextMinQty,
    max_qty: null,
    unit_price: '',
  }
}

const startAddingRange = () => {
  showNewRangeForm.value = true
  resetNewRange()
}

const cancelNewRange = () => {
  showNewRangeForm.value = false
  resetNewRange()
}

const saveNewRange = async () => {
  if (!newRange.value.unit_price || parseFloat(newRange.value.unit_price) <= 0) {
    showMessage('El precio unitario es requerido', 'error')
    return
  }

  saving.value = true
  message.value = ''

  try {
    await post(`/fixed-products/${props.productId}/ranges`, {
      min_qty: newRange.value.min_qty,
      max_qty: newRange.value.max_qty,
      unit_price: newRange.value.unit_price,
    })

    showMessage('Rango guardado exitosamente', 'success')
    emit('saved')
    await loadRanges()
    showNewRangeForm.value = false
  } catch (err: any) {
    showMessage(err.message || 'Error al guardar rango', 'error')
  } finally {
    saving.value = false
  }
}

const deleteRange = async (range: Range) => {
  deletingId.value = range.id

  try {
    await del(`/fixed-products/${props.productId}/ranges/${range.id}`)
    showMessage('Rango eliminado', 'success')
    emit('saved')
    await loadRanges()
  } catch (err: any) {
    showMessage(err.message || 'Error al eliminar', 'error')
  } finally {
    deletingId.value = null
  }
}

const startEdit = (range: Range) => {
  editingRangeId.value = range.id
  editingPrice.value = range.unit_price
}

const cancelEdit = () => {
  editingRangeId.value = null
  editingPrice.value = ''
}

const saveEditRange = async () => {
  if (!editingRangeId.value) return

  const price = parseFloat(editingPrice.value)
  if (isNaN(price) || price <= 0) {
    showMessage('El precio debe ser mayor que 0', 'error')
    return
  }

  updatingId.value = editingRangeId.value

  try {
    await patch(`/fixed-products/${props.productId}/ranges/${editingRangeId.value}`, {
      unit_price: editingPrice.value,
    })

    showMessage('Precio actualizado', 'success')
    emit('saved')
    await loadRanges()
    editingRangeId.value = null
    editingPrice.value = ''
  } catch (err: any) {
    showMessage(err.message || 'Error al actualizar', 'error')
  } finally {
    updatingId.value = null
  }
}

const showMessage = (text: string, type: 'success' | 'error') => {
  message.value = text
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

const formatPrice = (price: string | number): string => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  if (isNaN(numPrice)) return '$0'
  return (
    '$' +
    numPrice.toLocaleString('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
  )
}

// Load on mount
watch(() => props.productId, loadRanges, { immediate: true })
</script>

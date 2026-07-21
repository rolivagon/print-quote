<template>
  <div class="space-y-6">
    <!-- Header with Target Name -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Rangos de Precios</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Configurar precios basados en cantidad para {{ targetName || 'este elemento' }}
        </p>
      </div>
    </div>

    <!-- Print Type Tabs with Unit Selector for Finishes -->
    <div class="border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="type in PRINT_TYPE_OPTIONS"
            :key="type.value"
            @click="switchPrintType(type.value)"
            :class="[
              activePrintType === type.value
                ? 'border-brand-500 text-brand-600 dark:border-brand-400 dark:text-brand-400'
                : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300',
              'whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium',
            ]"
          >
            {{ type.label }}
          </button>
        </nav>

        <!-- Unit selector for finishes - shown at print type level -->
        <div v-if="targetType === 'finish'" class="flex items-center gap-3 pb-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-400"> Unidad: </label>
          <select
            v-model="printTypeUnits[activePrintType]"
            class="h-9 rounded-lg border border-gray-300 bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
          >
            <option v-for="unit in UNIT_OPTIONS" :key="unit.value" :value="unit.value">
              {{ unit.label }}
            </option>
          </select>
        </div>
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
              title="Editar precio"
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
              title="Eliminar rango"
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
        <div class="grid grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">Mín:</span>
            <span class="ml-1 font-medium">{{ range.min_quantity }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Máx:</span>
            <span class="ml-1 font-medium">{{ range.max_quantity || '∞' }}</span>
          </div>
          <div v-if="targetType === 'finish'">
            <span class="text-gray-500 dark:text-gray-400">Unidad:</span>
            <span class="ml-1 font-medium">{{ formatUnit(range.unit) }}</span>
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
                  title="Guardar cambios"
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
                  title="Cancelar edición"
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

    <!-- New Range Form (only shown when no unsaved range exists) -->
    <div
      v-if="!currentRange && showNewRangeForm"
      class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]"
    >
      <div class="flex items-center justify-between mb-4">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Agregar Nuevo Rango</h4>
        <div class="flex items-center gap-2">
          <button
            @click="cancelNewRange"
            :disabled="saving"
            class="inline-flex items-center justify-center rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
            title="Cancelar"
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
            class="inline-flex items-center justify-center rounded-lg p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Guardar rango"
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

      <!-- Validation Errors -->
      <div
        v-if="showValidationErrors && currentErrors.length > 0"
        class="mb-4 rounded-lg bg-error-50 p-3 text-sm text-error-700 dark:bg-error-500/10 dark:text-error-500"
      >
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(error, idx) in currentErrors" :key="idx">{{ error }}</li>
        </ul>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-400">
            Cantidad Mínima <span class="text-error-500">*</span>
          </label>
          <input
            v-model.number="newRange.min_quantity"
            type="number"
            min="1"
            disabled
            :class="[
              'h-10 w-full rounded-lg border bg-gray-100 px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:bg-gray-800 dark:text-gray-400 cursor-not-allowed',
              getFieldErrorClass('min_quantity'),
            ]"
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-400">
            Cantidad Máxima
          </label>
          <input
            v-model.number="newRange.max_quantity"
            type="number"
            :min="newRange.min_quantity"
            placeholder="Sin límite"
            :class="[
              'h-10 w-full rounded-lg border bg-transparent px-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:bg-gray-900',
              getFieldErrorClass('max_quantity'),
            ]"
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
              :class="[
                'h-10 w-full rounded-lg border bg-transparent pl-8 pr-3 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:bg-gray-900',
                getFieldErrorClass('unit_price'),
              ]"
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
      <p class="text-sm text-gray-500 dark:text-gray-400">
        No hay rangos de precio definidos para {{ activePrintTypeLabel }}
      </p>
      <button
        @click="startAddingRange"
        class="mt-4 inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        Agregar Primer Rango
      </button>
    </div>

    <!-- Add Another Button (shown after successful save) -->
    <div v-if="savedRanges.length > 0 && !showNewRangeForm" class="flex justify-center">
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
        Agregar Otro Rango
      </button>
    </div>

    <!-- Success/Error Messages -->
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
import type { PrintType, PricingRange, Unit } from '@/types'
import {
  UNIT_OPTIONS,
  PRINT_TYPE_OPTIONS,
  PRINT_TYPES,
  getUnitLabel,
  getPrintTypeLabel,
} from '@/constants'

interface Props {
  targetType: 'paper' | 'finish'
  targetId: number
  targetName?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  saved: []
}>()

const { get, post, patch, del } = useApi()

// State
const activePrintType = ref<PrintType>('digital')
const allRanges = ref<PricingRange[]>([])
const savedRanges = computed(() =>
  allRanges.value.filter((r) => r.print_type === activePrintType.value),
)
const currentRange = ref<PricingRange | null>(null)
const showNewRangeForm = ref(false)
const saving = ref(false)
const deletingId = ref<number | null>(null)
const editingRangeId = ref<number | null>(null)
const editingPrice = ref('')
const updatingId = ref<number | null>(null)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const fieldErrors = ref<Record<string, string>>({})
const showValidationErrors = ref(false)

// Track unit per print type for finishes
const printTypeUnits = ref<Record<PrintType, Unit>>({
  digital: 'job',
  offset: 'job',
  plotter: 'job',
})

const newRange = ref<{
  min_quantity: number
  max_quantity: number | null
  unit_price: string
}>({
  min_quantity: 1,
  max_quantity: null,
  unit_price: '',
})

// Computed
const activePrintTypeLabel = computed(() => {
  return getPrintTypeLabel(activePrintType.value)
})

const currentErrors = computed(() => {
  const errors: string[] = []

  // Validate min_quantity
  if (!newRange.value.min_quantity || newRange.value.min_quantity < 1) {
    errors.push('La cantidad mínima debe ser al menos 1')
  }

  // Validate max_quantity
  if (newRange.value.max_quantity !== null && newRange.value.max_quantity !== undefined) {
    if (newRange.value.max_quantity < newRange.value.min_quantity) {
      errors.push('La cantidad máxima debe ser mayor o igual a la cantidad mínima')
    }
  }

  // Validate unit_price
  if (!newRange.value.unit_price || newRange.value.unit_price.trim() === '') {
    errors.push('El precio unitario es requerido')
  } else {
    const price = parseFloat(newRange.value.unit_price)
    if (isNaN(price) || price <= 0) {
      errors.push('El precio unitario debe ser mayor que 0')
    }
  }

  return errors
})

// Methods
const loadPricing = async () => {
  try {
    const endpoint =
      props.targetType === 'paper'
        ? `/papers/${props.targetId}/pricing`
        : `/finishes/${props.targetId}/pricing`

    const data = await get<
      Array<{
        id: number
        print_type: PrintType
        unit?: Unit
        min_quantity: number
        max_quantity: number | null
        unit_price: string | number
      }>
    >(endpoint)

    // Convert data to PricingRange format
    allRanges.value = data.map((item) => ({
      id: item.id,
      print_type: item.print_type,
      min_quantity: item.min_quantity,
      max_quantity: item.max_quantity,
      unit_price:
        typeof item.unit_price === 'number' ? item.unit_price.toFixed(2) : String(item.unit_price),
      ...(props.targetType === 'finish' && item.unit ? { unit: item.unit } : {}),
    }))

    // Initialize printTypeUnits based on existing ranges (for finishes)
    if (props.targetType === 'finish') {
      PRINT_TYPES.forEach((type) => {
        const rangesForType = allRanges.value.filter((r) => r.print_type === type)
        if (rangesForType.length > 0 && rangesForType[0].unit) {
          printTypeUnits.value[type] = rangesForType[0].unit
        }
      })
    }

    // Reset form state
    currentRange.value = null

    // If no ranges for active type, show form by default
    if (savedRanges.value.length === 0) {
      showNewRangeForm.value = true
    } else {
      showNewRangeForm.value = false
    }

    resetNewRange()
    fieldErrors.value = {}
    showValidationErrors.value = false
  } catch (err) {
    showMessage('Error al cargar datos de precios', 'error')
    console.error('Error loading pricing:', err)
  }
}

const resetNewRange = () => {
  // Calculate next min_quantity based on existing ranges
  const existingRanges = savedRanges.value
  let nextMinQuantity = 1

  if (existingRanges.length > 0) {
    // Find the range with the highest max_quantity
    const lastRange = existingRanges.reduce((max, range) => {
      const currentMax = range.max_quantity ?? Infinity
      const maxSoFar = max.max_quantity ?? Infinity
      return currentMax > maxSoFar ? range : max
    })

    // Next min_quantity is last range's max + 1
    // If last range has no max (Infinity), we can't add more ranges
    if (lastRange.max_quantity !== null && lastRange.max_quantity !== undefined) {
      nextMinQuantity = lastRange.max_quantity + 1
    } else {
      // If there's an open-ended range (no max), we shouldn't allow adding more
      // But for now, just set it to last min + 1 as a fallback
      nextMinQuantity = lastRange.min_quantity + 1
    }
  }

  newRange.value = {
    min_quantity: nextMinQuantity,
    max_quantity: null,
    unit_price: '',
  }
}

const switchPrintType = (type: PrintType) => {
  activePrintType.value = type

  // If no ranges for this new type, show form by default
  if (savedRanges.value.length === 0) {
    showNewRangeForm.value = true
  } else {
    showNewRangeForm.value = false
  }

  resetNewRange()
  fieldErrors.value = {}
  showValidationErrors.value = false
}

const startAddingRange = () => {
  showNewRangeForm.value = true
  resetNewRange()
  fieldErrors.value = {}
  showValidationErrors.value = false
}

const cancelNewRange = () => {
  showNewRangeForm.value = false
  resetNewRange()
  fieldErrors.value = {}
  showValidationErrors.value = false
}

const validateNewRange = (): boolean => {
  fieldErrors.value = {}
  let isValid = true

  if (!newRange.value.min_quantity || newRange.value.min_quantity < 1) {
    fieldErrors.value.min_quantity = 'Debe ser ≥ 1'
    isValid = false
  }

  if (newRange.value.max_quantity !== null && newRange.value.max_quantity !== undefined) {
    if (newRange.value.max_quantity < newRange.value.min_quantity) {
      fieldErrors.value.max_quantity = 'Debe ser ≥ mín'
      isValid = false
    }
  }

  if (!newRange.value.unit_price || newRange.value.unit_price.trim() === '') {
    fieldErrors.value.unit_price = 'Requerido'
    isValid = false
  } else {
    const price = parseFloat(newRange.value.unit_price)
    if (isNaN(price) || price <= 0) {
      fieldErrors.value.unit_price = 'Debe ser > 0'
      isValid = false
    }
  }

  return isValid
}

const getFieldErrorClass = (field: string): string => {
  if (fieldErrors.value[field]) {
    return 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
  }
  return 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90'
}

const checkOverlap = (): boolean => {
  const existingRanges = savedRanges.value

  for (const existing of existingRanges) {
    const max1 = existing.max_quantity ?? Infinity
    const max2 = newRange.value.max_quantity ?? Infinity

    if (newRange.value.min_quantity <= max1 && existing.min_quantity <= max2) {
      showMessage(
        `No se puede guardar: El rango ${newRange.value.min_quantity}-${newRange.value.max_quantity || '∞'} ` +
          `se superpone con el rango existente ${existing.min_quantity}-${existing.max_quantity || '∞'}`,
        'error',
      )
      return true
    }
  }

  return false
}

const saveNewRange = async () => {
  // Activar mostrar errores de validación
  showValidationErrors.value = true

  if (!validateNewRange()) {
    return
  }

  if (checkOverlap()) {
    return
  }

  saving.value = true
  message.value = ''

  try {
    const baseEndpoint = props.targetType === 'paper' ? '/papers' : '/finishes'

    const payload =
      props.targetType === 'paper'
        ? {
            print_type: activePrintType.value,
            min_quantity: newRange.value.min_quantity,
            max_quantity: newRange.value.max_quantity,
            unit_price: newRange.value.unit_price,
          }
        : {
            print_type: activePrintType.value,
            unit: printTypeUnits.value[activePrintType.value],
            min_quantity: newRange.value.min_quantity,
            max_quantity: newRange.value.max_quantity,
            unit_price: newRange.value.unit_price,
          }

    await post(`${baseEndpoint}/${props.targetId}/pricing`, payload)

    showMessage('¡Rango guardado exitosamente!', 'success')
    emit('saved')

    // Reload data
    await loadPricing()

    // Auto-open next form
    showNewRangeForm.value = true
    resetNewRange()
    showValidationErrors.value = false
  } catch (err: any) {
    showMessage(err.message || 'Error al guardar rango', 'error')
    console.error('Error saving range:', err)
  } finally {
    saving.value = false
  }
}

const deleteRange = async (range: PricingRange) => {
  if (!range.id) return

  deletingId.value = range.id

  try {
    const baseEndpoint = props.targetType === 'paper' ? '/papers' : '/finishes'
    await del(`${baseEndpoint}/pricing/${range.id}`)

    showMessage('¡Rango eliminado exitosamente!', 'success')
    emit('saved')

    await loadPricing()
  } catch (err: any) {
    showMessage(err.message || 'Error al eliminar rango', 'error')
    console.error('Error deleting range:', err)
  } finally {
    deletingId.value = null
  }
}

const startEdit = (range: PricingRange) => {
  if (!range.id) return
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
    const baseEndpoint = props.targetType === 'paper' ? '/papers' : '/finishes'
    await patch(`${baseEndpoint}/pricing/${editingRangeId.value}`, {
      unit_price: editingPrice.value,
    })

    showMessage('¡Precio actualizado exitosamente!', 'success')
    emit('saved')

    await loadPricing()
    editingRangeId.value = null
    editingPrice.value = ''
  } catch (err: any) {
    showMessage(err.message || 'Error al actualizar precio', 'error')
    console.error('Error updating price:', err)
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

// Format price in CLP format (Chilean Peso)
const formatPrice = (price: string | number): string => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  if (isNaN(numPrice)) return '$0'

  // Format with thousands separator (.) and no decimal places for CLP
  return (
    '$' +
    numPrice.toLocaleString('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
  )
}

// Format unit for display - usa el helper centralizado
const formatUnit = (unit: Unit | undefined): string => {
  return getUnitLabel(unit)
}

// Watch for targetId changes
watch(() => props.targetId, loadPricing, { immediate: true })
</script>

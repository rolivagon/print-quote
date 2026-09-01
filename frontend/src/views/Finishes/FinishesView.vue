<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Acabados</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{
              viewMode === 'list'
                ? 'Acabados'
                : viewMode === 'form'
                  ? editingFinish
                    ? 'Editar Acabado'
                    : 'Nuevo Acabado'
                  : 'Gestionar Precios'
            }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{
              viewMode === 'list'
                ? 'Gestionar acabados y sus precios'
                : viewMode === 'form'
                  ? 'Configurar detalles del acabado'
                  : `Establecer rangos de precio para ${selectedFinish?.name}`
            }}
          </p>
        </div>
        <div class="flex gap-3">
          <button
            v-if="viewMode !== 'list'"
            @click="goToList"
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
            Volver a la Lista
          </button>
          <button
            v-if="viewMode === 'list'"
            @click="goToForm()"
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
            Agregar Acabado
          </button>
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
        <div v-if="showPricingButton" class="mt-3">
          <button
            @click="goToPricing(lastCreatedFinishId!)"
            class="inline-flex items-center gap-2 rounded-lg bg-success-500 px-4 py-2 text-sm font-medium text-white hover:bg-success-600"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Configurar Precios Ahora
          </button>
        </div>
      </div>

      <!-- List View -->
      <div
        v-if="viewMode === 'list'"
        class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <!-- Search -->
        <div class="border-b border-gray-200 p-4 dark:border-gray-700">
          <div class="relative max-w-md">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Buscar acabados..."
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
        </div>

        <!-- Table -->
        <div class="max-w-full overflow-x-auto">
          <table class="min-w-full">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="px-5 py-3 text-left sm:px-6 w-1/3">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Nombre</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-1/2">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">
                    Descripción
                  </p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-48">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Acciones</p>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="finish in filteredFinishes"
                :key="finish.id"
                class="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td class="px-5 py-4 sm:px-6">
                  <div>
                    <p class="font-medium text-gray-800 text-theme-sm dark:text-white/90">
                      {{ finish.name }}
                    </p>
                    <p class="text-xs text-gray-400">ID: {{ finish.id }}</p>
                  </div>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <p class="text-gray-500 text-theme-sm dark:text-gray-400 truncate max-w-md">
                    {{ finish.description || '-' }}
                  </p>
                </td>
                <td class="px-5 py-4 sm:px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="goToPricing(finish.id)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10"
                      title="Gestionar precios"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </button>
                    <button
                      @click="goToForm(finish)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-warning-500 hover:bg-warning-50 dark:hover:bg-warning-500/10"
                      title="Editar acabado"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </button>
                    <button
                      @click="confirmDelete(finish)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-error-500 hover:bg-error-50 dark:hover:bg-error-500/10"
                      title="Eliminar acabado"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              <tr v-if="filteredFinishes.length === 0">
                <td colspan="3" class="px-5 py-8 text-center text-gray-500 dark:text-gray-400">
                  <p class="text-sm">No se encontraron acabados</p>
                  <p class="text-xs mt-1" v-if="searchQuery">Intenta ajustar tu búsqueda</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Form View -->
      <div
        v-if="viewMode === 'form'"
        class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <form @submit.prevent="saveFinish" class="space-y-6 max-w-2xl">
          <!-- Validation Errors -->
          <div
            v-if="formErrors.length > 0"
            class="rounded-lg bg-error-50 p-4 text-sm text-error-700 dark:bg-error-500/10 dark:text-error-500"
          >
            <p class="font-medium mb-2">Por favor corrige los siguientes errores:</p>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(error, idx) in formErrors" :key="idx">{{ error }}</li>
            </ul>
          </div>

          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Nombre del Acabado <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.name"
              type="text"
              required
              placeholder="ej., Laminado Mate"
              :class="[
                'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                formFieldErrors.name
                  ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                  : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
              ]"
              @blur="validateFormField('name')"
            />
            <p v-if="formFieldErrors.name" class="mt-1 text-xs text-error-500">
              {{ formFieldErrors.name }}
            </p>
          </div>

          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Descripción
            </label>
            <textarea
              v-model="formData.description"
              rows="3"
              placeholder="Ingresa descripción del acabado..."
              class="dark:bg-dark-900 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-3 text-sm text-gray-800 shadow-theme-xs placeholder:text-gray-400 focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800"
            ></textarea>
          </div>

          <div class="flex items-center gap-3 pt-4">
            <button
              type="submit"
              :disabled="saving || formErrors.length > 0"
              class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed"
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
              <span>{{ editingFinish ? 'Actualizar Acabado' : 'Crear Acabado' }}</span>
            </button>
            <button
              type="button"
              @click="goToList"
              class="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>

      <!-- Pricing View -->
      <div
        v-if="viewMode === 'pricing' && selectedFinish"
        class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              {{ selectedFinish.name }}
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ selectedFinish.description || 'Sin descripción' }}
            </p>
          </div>
          <button
            @click="goToForm(selectedFinish)"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
            Editar Detalles del Acabado
          </button>
        </div>

        <PricingManager
          target-type="finish"
          :target-id="selectedFinish.id"
          :target-name="selectedFinish.name"
          @saved="onPricingSaved"
        />
        <InternalCostManager target-type="finish" :target-id="selectedFinish.id" />
      </div>

      <!-- Delete Confirmation Modal -->
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      >
        <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Eliminar Acabado</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            ¿Estás seguro de que deseas eliminar <strong>{{ finishToDelete?.name }}</strong
            >? Esta acción no se puede deshacer y también eliminará todos los rangos de precios
            asociados.
          </p>
          <div class="mt-6 flex justify-end gap-3">
            <button
              @click="showDeleteModal = false"
              class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Cancelar
            </button>
            <button
              @click="deleteFinish"
              :disabled="deleting"
              class="inline-flex items-center gap-2 rounded-lg bg-error-500 px-4 py-2 text-sm font-medium text-white hover:bg-error-600 disabled:opacity-50"
            >
              <svg v-if="deleting" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
              <span>Eliminar</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import AdminLayout from '@/components/layout/AdminLayout.vue'
import PricingManager from '@/components/pricing/PricingManager.vue'
import InternalCostManager from '@/components/pricing/InternalCostManager.vue'
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Finish, CreateFinishRequest, UpdateFinishRequest } from '@/types'

type ViewMode = 'list' | 'form' | 'pricing'

const { get, post, patch, del } = useApi()

// State
const viewMode = ref<ViewMode>('list')
const finishes = ref<Finish[]>([])
const searchQuery = ref('')
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const successMessage = ref('')
const showPricingButton = ref(false)
const lastCreatedFinishId = ref<number | null>(null)

// Form state
const editingFinish = ref<Finish | null>(null)
const formData = ref<CreateFinishRequest>({
  name: '',
  description: '',
})

// Pricing state
const selectedFinish = ref<Finish | null>(null)

// Delete modal state
const showDeleteModal = ref(false)
const finishToDelete = ref<Finish | null>(null)

// Form validation state
const formFieldErrors = ref<Record<string, string>>({})
const touchedFields = ref<Set<string>>(new Set())
const formSubmitted = ref(false)

const formErrors = computed(() => {
  // Only show errors if form was submitted or fields were touched
  if (!formSubmitted.value && touchedFields.value.size === 0) {
    return []
  }

  const errors: string[] = []

  // Validate name
  const trimmedName = formData.value.name?.trim()
  if (!trimmedName) {
    errors.push('El nombre del acabado es requerido')
  } else if (trimmedName.length < 2) {
    errors.push('El nombre del acabado debe tener al menos 2 caracteres')
  }

  return errors
})

const validateFormField = (field: string) => {
  // Mark field as touched
  touchedFields.value.add(field)

  // Clear previous error for this field
  delete formFieldErrors.value[field]

  if (field === 'name') {
    const trimmedName = formData.value.name?.trim()
    if (!trimmedName) {
      formFieldErrors.value.name = 'El nombre del acabado es requerido'
    } else if (trimmedName.length < 2) {
      formFieldErrors.value.name = 'Debe tener al menos 2 caracteres'
    }
  }
}

// Computed
const filteredFinishes = computed(() => {
  if (!searchQuery.value) return finishes.value
  const query = searchQuery.value.toLowerCase()
  return finishes.value.filter(
    (finish) =>
      finish.name.toLowerCase().includes(query) ||
      (finish.description?.toLowerCase().includes(query) ?? false),
  )
})

// Methods
const loadFinishes = async () => {
  loading.value = true
  try {
    finishes.value = await get<Finish[]>('/finishes/')
  } catch (err) {
    console.error('Error loading finishes:', err)
  } finally {
    loading.value = false
  }
}

const goToList = () => {
  viewMode.value = 'list'
  editingFinish.value = null
  selectedFinish.value = null
  resetForm()
  clearMessages()
}

const goToForm = (finish?: Finish) => {
  // Reset validation state
  touchedFields.value.clear()
  formSubmitted.value = false
  formFieldErrors.value = {}

  if (finish) {
    editingFinish.value = finish
    formData.value = {
      name: finish.name,
      description: finish.description || '',
    }
  } else {
    editingFinish.value = null
    resetForm()
  }
  viewMode.value = 'form'
  clearMessages()
}

const goToPricing = async (finishId: number) => {
  const finish = finishes.value.find((f) => f.id === finishId)
  if (finish) {
    selectedFinish.value = finish
    viewMode.value = 'pricing'
    clearMessages()
  }
}

const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
  }
  formFieldErrors.value = {}
  touchedFields.value.clear()
  formSubmitted.value = false
}

const clearMessages = () => {
  successMessage.value = ''
  showPricingButton.value = false
  lastCreatedFinishId.value = null
}

const saveFinish = async () => {
  // Mark form as submitted to show all validation errors
  formSubmitted.value = true

  // Validate all fields first
  validateFormField('name')

  if (formErrors.value.length > 0) {
    return
  }

  saving.value = true
  clearMessages()

  try {
    // Prepare data with trimmed name
    const submitData = {
      ...formData.value,
      name: formData.value.name.trim(),
    }

    if (editingFinish.value) {
      // Update existing
      const updateData: UpdateFinishRequest = {}
      if (submitData.name !== editingFinish.value.name) updateData.name = submitData.name
      if (submitData.description !== editingFinish.value.description)
        updateData.description = submitData.description

      await patch(`/finishes/${editingFinish.value.id}`, updateData)
      successMessage.value = '¡Acabado actualizado exitosamente!'
      await loadFinishes()
      goToList()
    } else {
      // Create new
      const newFinish = await post<Finish>('/finishes/', submitData)
      successMessage.value = '¡Acabado creado exitosamente!'
      showPricingButton.value = true
      lastCreatedFinishId.value = newFinish.id
      await loadFinishes()
      resetForm()
    }
  } catch (err: any) {
    console.error('Error saving finish:', err)
    successMessage.value = err.message || 'Error al guardar el acabado. Por favor intenta de nuevo.'
  } finally {
    saving.value = false
  }
}

const confirmDelete = (finish: Finish) => {
  finishToDelete.value = finish
  showDeleteModal.value = true
}

const deleteFinish = async () => {
  if (!finishToDelete.value) return

  deleting.value = true
  try {
    await del(`/finishes/${finishToDelete.value.id}/`)
    showDeleteModal.value = false
    finishToDelete.value = null
    successMessage.value = '¡Acabado eliminado exitosamente!'
    await loadFinishes()
  } catch (err) {
    console.error('Error deleting finish:', err)
  } finally {
    deleting.value = false
  }
}

const onPricingSaved = () => {
  // Optional: handle post-save actions
}

// Load finishes on mount
onMounted(loadFinishes)
</script>

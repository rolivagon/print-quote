<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Usuarios</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{
              viewMode === 'list' ? 'Usuarios' : editingUser ? 'Editar Usuario' : 'Nuevo Usuario'
            }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{
              viewMode === 'list'
                ? 'Gestionar usuarios del sistema'
                : 'Configurar detalles del usuario'
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
            Agregar Usuario
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
              placeholder="Buscar usuarios..."
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
                <th class="px-5 py-3 text-left sm:px-6 w-1/4">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Nombre</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-1/3">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Email</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-24">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Rol</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-24">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Estado</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Creado</p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Acciones</p>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                class="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td class="px-5 py-4 sm:px-6">
                  <div class="flex items-center gap-3">
                    <div
                      class="h-10 w-10 rounded-full bg-brand-100 flex items-center justify-center dark:bg-brand-900/30"
                    >
                      <span class="text-sm font-medium text-brand-700 dark:text-brand-400">
                        {{ getInitials(user.name) }}
                      </span>
                    </div>
                    <div>
                      <p class="font-medium text-gray-800 text-theme-sm dark:text-white/90">
                        {{ user.name }}
                      </p>
                      <p class="text-xs text-gray-400">ID: {{ user.id }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <p class="text-gray-600 text-theme-sm dark:text-gray-400">{{ user.email }}</p>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      user.role === 'super_admin'
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                        : user.role === 'admin'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
                    ]"
                  >
                    {{
                      user.role === 'super_admin'
                        ? 'Super Admin'
                        : user.role === 'admin'
                          ? 'Administrador'
                          : 'Vendedor'
                    }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      user.is_active
                        ? 'bg-success-100 text-success-800 dark:bg-success-900/30 dark:text-success-400'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
                    ]"
                  >
                    {{ user.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <p class="text-gray-600 text-theme-sm dark:text-gray-400">
                    {{ formatDate(user.created_at) }}
                  </p>
                </td>
                <td class="px-5 py-4 sm:px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="goToForm(user)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-warning-500 hover:bg-warning-50 dark:hover:bg-warning-500/10"
                      title="Editar usuario"
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
                      v-if="canResetPasswords"
                      @click="openPasswordModal(user)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10"
                      title="Actualizar contraseña"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 15v2m-6 4h12a2 2 0 002-2v-7a2 2 0 00-2-2h-1V7a5 5 0 00-10 0v3H6a2 2 0 00-2 2v7a2 2 0 002 2zm8-11V7a2 2 0 10-4 0v3h4z"
                        />
                      </svg>
                    </button>
                    <button
                      v-if="user.id !== authStore.user?.id"
                      @click="confirmDelete(user)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-error-500 hover:bg-error-50 dark:hover:bg-error-500/10"
                      title="Eliminar usuario"
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
                    <span
                      v-else
                      class="inline-flex items-center justify-center rounded-lg p-2 text-gray-300 cursor-not-allowed"
                      title="No puedes eliminar tu propia cuenta"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </span>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="6" class="px-5 py-8 text-center text-gray-500 dark:text-gray-400">
                  <p class="text-sm">No se encontraron usuarios</p>
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
        <form @submit.prevent="saveUser" class="space-y-6 max-w-2xl">
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

          <!-- Name -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Nombre <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.name"
              type="text"
              required
              placeholder="ej., Juan Pérez"
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

          <!-- Email -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Email <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.email"
              type="email"
              required
              placeholder="ej., correo@ejemplo.com"
              :disabled="!!editingUser"
              :class="[
                'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                editingUser ? 'bg-gray-100 cursor-not-allowed dark:bg-gray-800' : '',
                formFieldErrors.email
                  ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                  : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
              ]"
              @blur="validateFormField('email')"
            />
            <p v-if="formFieldErrors.email" class="mt-1 text-xs text-error-500">
              {{ formFieldErrors.email }}
            </p>
            <p v-if="editingUser" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              El email no se puede modificar
            </p>
          </div>

          <!-- Role -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Rol <span class="text-error-500">*</span>
            </label>
            <select
              v-model="formData.role"
              required
              :class="[
                'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs focus:outline-hidden focus:ring-3 dark:bg-gray-900',
                'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
              ]"
            >
              <option v-for="role in availableRoles" :key="role.value" :value="role.value">
                {{ role.label }}
              </option>
            </select>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              El rol Super Admin solo puede ser asignado manualmente por la base de datos
            </p>
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
              <span>{{ editingUser ? 'Actualizar Usuario' : 'Crear Usuario' }}</span>
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

      <div
        v-if="showPasswordModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      >
        <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Actualizar contraseña</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Define una nueva contraseña para <strong>{{ passwordUser?.name }}</strong
            >.
          </p>
          <form class="mt-6 space-y-4" @submit.prevent="updatePassword">
            <div>
              <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                Nueva contraseña
              </label>
              <input
                v-model="newPassword"
                type="password"
                minlength="12"
                required
                class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                Confirmar contraseña
              </label>
              <input
                v-model="passwordConfirmation"
                type="password"
                minlength="12"
                required
                class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
              />
              <p v-if="passwordError || passwordMismatch" class="mt-1 text-xs text-error-500">
                {{ passwordError || 'Las contraseñas deben coincidir' }}
              </p>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button
                type="button"
                @click="closePasswordModal"
                class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="
                  resettingPassword || !newPassword || newPassword !== passwordConfirmation
                "
                class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span>Actualizar</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      >
        <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Eliminar Usuario</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            ¿Estás seguro de que deseas eliminar a <strong>{{ userToDelete?.name }}</strong
            >? Esta acción no se puede deshacer.
          </p>
          <div class="mt-6 flex justify-end gap-3">
            <button
              @click="showDeleteModal = false"
              class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Cancelar
            </button>
            <button
              @click="deleteUser"
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
import { useUserPasswordReset } from '@/composables/useUserPasswordReset'
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import type { User, CreateUserRequest, UpdateUserRequest, UserRole } from '@/types'

const authStore = useAuthStore()

type ViewMode = 'list' | 'form'

const { get, post, patch, del } = useApi()

// State
const viewMode = ref<ViewMode>('list')
const users = ref<User[]>([])
const searchQuery = ref('')
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const successMessage = ref('')

// Form state
const editingUser = ref<User | null>(null)
const formData = ref<CreateUserRequest>({
  name: '',
  email: '',
  role: 'vendedor',
})

// Available roles for creation (super_admin excluded)
const availableRoles: { value: UserRole; label: string }[] = [
  { value: 'admin', label: 'Administrador' },
  { value: 'vendedor', label: 'Vendedor' },
]

// Delete modal state
const showDeleteModal = ref(false)
const userToDelete = ref<User | null>(null)

// Form validation state
const formFieldErrors = ref<Record<string, string>>({})
const touchedFields = ref<Set<string>>(new Set())
const formSubmitted = ref(false)

// Get initials from name
const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// Format date
const formatDate = (dateString?: string): string => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formErrors = computed(() => {
  if (!formSubmitted.value && touchedFields.value.size === 0) {
    return []
  }

  const errors: string[] = []

  // Validate name
  if (!formData.value.name?.trim()) {
    errors.push('El nombre es requerido')
  }

  // Validate email
  if (!formData.value.email?.trim()) {
    errors.push('El email es requerido')
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.value.email)) {
      errors.push('El email no es válido')
    }
  }

  return errors
})

const validateFormField = (field: string) => {
  touchedFields.value.add(field)
  delete formFieldErrors.value[field]

  if (field === 'name') {
    if (!formData.value.name?.trim()) {
      formFieldErrors.value.name = 'El nombre es requerido'
    }
  }

  if (field === 'email') {
    if (!formData.value.email?.trim()) {
      formFieldErrors.value.email = 'El email es requerido'
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.value.email)) {
        formFieldErrors.value.email = 'El email no es válido'
      }
    }
  }
}

// Computed
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter((user) => {
    return user.name.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)
  })
})

const canResetPasswords = computed(() => authStore.user?.role === 'super_admin')
const {
  showPasswordModal,
  passwordUser,
  newPassword,
  passwordConfirmation,
  passwordError,
  resettingPassword,
  passwordMismatch,
  openPasswordModal,
  closePasswordModal,
  updatePassword: submitPasswordUpdate,
} = useUserPasswordReset((endpoint, payload) => post<void>(endpoint, payload), canResetPasswords)

// Methods
const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await get<User[]>('/users/')
  } catch (err) {
    console.error('Error loading users:', err)
  } finally {
    loading.value = false
  }
}

const goToList = () => {
  viewMode.value = 'list'
  editingUser.value = null
  resetForm()
  clearMessages()
}

const goToForm = (user?: User) => {
  touchedFields.value.clear()
  formSubmitted.value = false
  formFieldErrors.value = {}

  if (user) {
    editingUser.value = user
    formData.value = {
      name: user.name,
      email: user.email,
      role: user.role,
    }
  } else {
    editingUser.value = null
    resetForm()
  }
  viewMode.value = 'form'
  clearMessages()
}

const resetForm = () => {
  formData.value = {
    name: '',
    email: '',
    role: 'vendedor',
  }
  formFieldErrors.value = {}
  touchedFields.value.clear()
  formSubmitted.value = false
}

const clearMessages = () => {
  successMessage.value = ''
}

const saveUser = async () => {
  formSubmitted.value = true

  validateFormField('name')
  validateFormField('email')

  if (formErrors.value.length > 0) {
    return
  }

  saving.value = true
  clearMessages()

  try {
    if (editingUser.value) {
      const updateData: UpdateUserRequest = {}
      if (formData.value.name.trim() !== editingUser.value.name) {
        updateData.name = formData.value.name.trim()
      }
      if (formData.value.role !== editingUser.value.role) {
        updateData.role = formData.value.role
      }

      if (Object.keys(updateData).length > 0) {
        await patch(`/users/${editingUser.value.id}`, updateData)
      }
      successMessage.value = '¡Usuario actualizado exitosamente!'
      await loadUsers()
      goToList()
    } else {
      const createData: CreateUserRequest = {
        name: formData.value.name.trim(),
        email: formData.value.email.trim(),
        role: formData.value.role,
      }
      await post<User>('/users/', createData)
      successMessage.value = '¡Usuario creado exitosamente!'
      await loadUsers()
      resetForm()
    }
  } catch (err: any) {
    console.error('Error saving user:', err)
    successMessage.value = err.message || 'Error al guardar el usuario. Por favor intenta de nuevo.'
  } finally {
    saving.value = false
  }
}

const confirmDelete = (user: User) => {
  if (user.id === authStore.user?.id) {
    successMessage.value = 'No puedes eliminar tu propia cuenta'
    return
  }
  userToDelete.value = user
  showDeleteModal.value = true
}

const updatePassword = async () => {
  if (await submitPasswordUpdate()) {
    successMessage.value = 'Contraseña actualizada exitosamente'
  }
}

const deleteUser = async () => {
  if (!userToDelete.value) return

  deleting.value = true
  try {
    await del(`/users/${userToDelete.value.id}/`)
    showDeleteModal.value = false
    userToDelete.value = null
    successMessage.value = '¡Usuario eliminado exitosamente!'
    await loadUsers()
  } catch (err: any) {
    console.error('Error deleting user:', err)
    successMessage.value = err.response?.data?.detail || 'Error al eliminar el usuario'
  } finally {
    deleting.value = false
  }
}

// Load users on mount
onMounted(loadUsers)
</script>

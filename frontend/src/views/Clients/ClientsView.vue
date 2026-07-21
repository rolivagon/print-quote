<template>
  <AdminLayout>
    <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10 space-y-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <router-link to="/" class="hover:text-brand-500">Inicio</router-link>
        <span>/</span>
        <span class="text-gray-900 dark:text-white">Clientes</span>
      </div>

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{
              viewMode === 'list' ? 'Clientes' : editingClient ? 'Editar Cliente' : 'Nuevo Cliente'
            }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{
              viewMode === 'list'
                ? 'Gestionar clientes del sistema'
                : 'Configurar detalles del cliente'
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
            Agregar Cliente
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
              placeholder="Buscar clientes..."
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
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">
                    Nombre / Razón Social
                  </p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-24">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Tipo</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">RUT</p>
                </th>
                <th class="px-5 py-3 text-left sm:px-6 w-48">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Contacto</p>
                </th>
                <th class="px-5 py-3 text-right sm:px-6 w-32">
                  <p class="font-medium text-gray-500 text-theme-xs dark:text-gray-400">Acciones</p>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="client in filteredClients"
                :key="client.id"
                class="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
              >
                <td class="px-5 py-4 sm:px-6">
                  <div>
                    <p class="font-medium text-gray-800 text-theme-sm dark:text-white/90">
                      {{
                        client.client_type === 'individual'
                          ? `${client.first_name} ${client.last_name}`
                          : client.company_name
                      }}
                    </p>
                    <p class="text-xs text-gray-400">ID: {{ client.id }}</p>
                  </div>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <span
                    :class="[
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      client.client_type === 'individual'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                        : 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
                    ]"
                  >
                    {{ client.client_type === 'individual' ? 'Persona' : 'Empresa' }}
                  </span>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <p class="text-gray-600 text-theme-sm dark:text-gray-400 font-mono">
                    {{ client.tax_id }}
                  </p>
                </td>
                <td class="px-5 py-4 sm:px-6">
                  <div class="space-y-1">
                    <p
                      v-if="client.email"
                      class="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1"
                    >
                      <svg
                        class="h-3.5 w-3.5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                      </svg>
                      {{ client.email }}
                    </p>
                    <p
                      v-if="client.phone"
                      class="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1"
                    >
                      <svg
                        class="h-3.5 w-3.5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                        />
                      </svg>
                      {{ client.phone }}
                    </p>
                  </div>
                </td>
                <td class="px-5 py-4 sm:px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="goToForm(client)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-warning-500 hover:bg-warning-50 dark:hover:bg-warning-500/10"
                      title="Editar cliente"
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
                      @click="confirmDelete(client)"
                      class="inline-flex items-center justify-center rounded-lg p-2 text-error-500 hover:bg-error-50 dark:hover:bg-error-500/10"
                      title="Eliminar cliente"
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
              <tr v-if="filteredClients.length === 0">
                <td colspan="5" class="px-5 py-8 text-center text-gray-500 dark:text-gray-400">
                  <p class="text-sm">No se encontraron clientes</p>
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
        <form @submit.prevent="saveClient" class="space-y-6 max-w-2xl">
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

          <!-- Client Type Selection (only for new clients) -->
          <div v-if="!editingClient">
            <label class="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Tipo de Cliente <span class="text-error-500">*</span>
            </label>
            <div class="flex gap-4">
              <label
                :class="[
                  'flex-1 cursor-pointer rounded-lg border p-4 transition-colors',
                  formData.client_type === 'individual'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10'
                    : 'border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800/50',
                ]"
              >
                <input
                  v-model="formData.client_type"
                  type="radio"
                  value="individual"
                  class="sr-only"
                />
                <div class="flex items-center gap-3">
                  <div class="rounded-full bg-blue-100 p-2 dark:bg-blue-900/30">
                    <svg
                      class="h-5 w-5 text-blue-600 dark:text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p class="font-medium text-gray-900 dark:text-white">Persona</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Cliente individual</p>
                  </div>
                </div>
              </label>
              <label
                :class="[
                  'flex-1 cursor-pointer rounded-lg border p-4 transition-colors',
                  formData.client_type === 'company'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10'
                    : 'border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800/50',
                ]"
              >
                <input
                  v-model="formData.client_type"
                  type="radio"
                  value="company"
                  class="sr-only"
                />
                <div class="flex items-center gap-3">
                  <div class="rounded-full bg-purple-100 p-2 dark:bg-purple-900/30">
                    <svg
                      class="h-5 w-5 text-purple-600 dark:text-purple-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                      />
                    </svg>
                  </div>
                  <div>
                    <p class="font-medium text-gray-900 dark:text-white">Empresa</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Razón social</p>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Tax ID -->
          <div>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              RUT <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.tax_id"
              type="text"
              required
              placeholder="ej., 12.345.678-9"
              :disabled="!!editingClient"
              :class="[
                'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                editingClient ? 'bg-gray-100 cursor-not-allowed dark:bg-gray-800' : '',
                formFieldErrors.tax_id
                  ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                  : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
              ]"
              @blur="validateFormField('tax_id')"
              @input="formatRutInput"
            />
            <p v-if="formFieldErrors.tax_id" class="mt-1 text-xs text-error-500">
              {{ formFieldErrors.tax_id }}
            </p>
            <p v-if="editingClient" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              El RUT no se puede modificar
            </p>
          </div>

          <!-- Individual Client Fields -->
          <div v-if="formData.client_type === 'individual'" class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                Nombre <span class="text-error-500">*</span>
              </label>
              <input
                v-model="formData.first_name"
                type="text"
                required
                placeholder="ej., Juan"
                :class="[
                  'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                  formFieldErrors.first_name
                    ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                    : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
                ]"
                @blur="validateFormField('first_name')"
              />
              <p v-if="formFieldErrors.first_name" class="mt-1 text-xs text-error-500">
                {{ formFieldErrors.first_name }}
              </p>
            </div>
            <div>
              <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                Apellido <span class="text-error-500">*</span>
              </label>
              <input
                v-model="formData.last_name"
                type="text"
                required
                placeholder="ej., Pérez"
                :class="[
                  'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                  formFieldErrors.last_name
                    ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                    : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
                ]"
                @blur="validateFormField('last_name')"
              />
              <p v-if="formFieldErrors.last_name" class="mt-1 text-xs text-error-500">
                {{ formFieldErrors.last_name }}
              </p>
            </div>
          </div>

          <!-- Company Client Fields -->
          <div v-else>
            <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
              Razón Social <span class="text-error-500">*</span>
            </label>
            <input
              v-model="formData.company_name"
              type="text"
              required
              placeholder="ej., Empresa S.A."
              :class="[
                'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                formFieldErrors.company_name
                  ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                  : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
              ]"
              @blur="validateFormField('company_name')"
            />
            <p v-if="formFieldErrors.company_name" class="mt-1 text-xs text-error-500">
              {{ formFieldErrors.company_name }}
            </p>
          </div>

          <!-- Contact Information -->
          <div class="border-t border-gray-200 pt-6 dark:border-gray-700">
            <h3 class="mb-4 text-sm font-medium text-gray-900 dark:text-white">
              Información de Contacto
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                  Email
                </label>
                <input
                  v-model="formData.email"
                  type="email"
                  placeholder="ej., correo@ejemplo.com"
                  :class="[
                    'h-11 w-full rounded-lg border bg-transparent px-4 py-2.5 text-sm shadow-theme-xs placeholder:text-gray-400 focus:outline-hidden focus:ring-3 dark:bg-gray-900 dark:placeholder:text-white/30',
                    formFieldErrors.email
                      ? 'border-error-300 focus:border-error-500 focus:ring-error-500/10 text-error-700 dark:border-error-700 dark:text-error-400'
                      : 'border-gray-300 focus:border-brand-300 focus:ring-brand-500/10 text-gray-800 dark:border-gray-700 dark:text-white/90 dark:focus:border-brand-800',
                  ]"
                  @blur="validateFormField('email')"
                />
                <p v-if="formFieldErrors.email" class="mt-1 text-xs text-error-500">
                  {{ formFieldErrors.email }}
                </p>
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                  Teléfono
                </label>
                <div class="flex">
                  <span
                    class="inline-flex items-center px-4 rounded-l-lg border border-r-0 border-gray-300 bg-gray-100 text-gray-600 text-sm font-medium dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400"
                  >
                    +56
                  </span>
                  <input
                    v-model="phoneNumber"
                    type="tel"
                    placeholder="9 1234 5678"
                    class="flex-1 h-11 rounded-r-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 shadow-theme-xs placeholder:text-gray-400 focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800"
                  />
                </div>
              </div>
            </div>

            <div class="mt-4">
              <label class="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400">
                Dirección
              </label>
              <textarea
                v-model="formData.address"
                rows="2"
                placeholder="Ingresa la dirección del cliente..."
                class="dark:bg-dark-900 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-3 text-sm text-gray-800 shadow-theme-xs placeholder:text-gray-400 focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800"
              ></textarea>
            </div>
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
              <span>{{ editingClient ? 'Actualizar Cliente' : 'Crear Cliente' }}</span>
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

      <!-- Delete Confirmation Modal -->
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      >
        <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Eliminar Cliente</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            ¿Estás seguro de que deseas eliminar
            <strong>{{
              clientToDelete?.client_type === 'individual'
                ? `${clientToDelete?.first_name} ${clientToDelete?.last_name}`
                : clientToDelete?.company_name
            }}</strong
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
              @click="deleteClient"
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
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Client, CreateClientRequest, UpdateClientRequest, ClientType } from '@/types'

type ViewMode = 'list' | 'form'

const { get, post, patch, del } = useApi()

// State
const viewMode = ref<ViewMode>('list')
const clients = ref<Client[]>([])
const searchQuery = ref('')
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const successMessage = ref('')

// Form state
const editingClient = ref<Client | null>(null)
const formData = ref<CreateClientRequest>({
  tax_id: '',
  client_type: 'company',
  first_name: '',
  last_name: '',
  company_name: '',
  email: '',
  phone: '+56',
  address: '',
})

// Delete modal state
const showDeleteModal = ref(false)
const clientToDelete = ref<Client | null>(null)

// Form validation state
const formFieldErrors = ref<Record<string, string>>({})
const touchedFields = ref<Set<string>>(new Set())
const formSubmitted = ref(false)

// Chilean RUT validation
const validateRut = (rut: string): boolean => {
  // Remove dots and convert to uppercase
  const cleanRut = rut.replace(/\./g, '').toUpperCase()

  // Check format: 12345678K or 12345678-9
  const rutRegex = /^(\d{1,8})-?([\dkK])$/
  const match = cleanRut.match(rutRegex)

  if (!match) return false

  const body = match[1]
  const verifier = match[2].toUpperCase()

  // Calculate verifier digit
  let sum = 0
  let multiplier = 2

  for (let i = body.length - 1; i >= 0; i--) {
    sum += parseInt(body[i]) * multiplier
    multiplier = multiplier === 7 ? 2 : multiplier + 1
  }

  const expectedVerifier = 11 - (sum % 11)
  let verifierChar: string

  if (expectedVerifier === 11) {
    verifierChar = '0'
  } else if (expectedVerifier === 10) {
    verifierChar = 'K'
  } else {
    verifierChar = expectedVerifier.toString()
  }

  return verifier === verifierChar
}

// Format RUT with mask (XX.XXX.XXX-X)
const formatRutInput = (event: Event) => {
  const input = event.target as HTMLInputElement
  const value = input.value

  // Remove all formatting characters (dots, dashes, spaces)
  const cleanValue = value.replace(/[^\dkK]/g, '').toUpperCase()

  if (cleanValue.length === 0) {
    formData.value.tax_id = ''
    return
  }

  // Check if last character is K (verifier)
  const hasKAtEnd = cleanValue.endsWith('K')

  // Separate numeric body from verifier
  let numericPart = cleanValue.replace(/[kK]/g, '')
  let verifier = ''

  // If there's a K at the end, that's our verifier
  if (hasKAtEnd && numericPart.length >= 1) {
    verifier = 'K'
  } else if (numericPart.length > 8) {
    // More than 8 digits - last one is verifier
    verifier = numericPart.slice(-1)
    numericPart = numericPart.slice(0, 8)
  }

  // Limit body to 8 digits
  if (numericPart.length > 8) {
    numericPart = numericPart.slice(0, 8)
  }

  // Format body with dots
  let formatted = ''
  const len = numericPart.length

  if (len > 6) {
    formatted = `${numericPart.slice(0, len - 6)}.${numericPart.slice(len - 6, len - 3)}.${numericPart.slice(len - 3)}`
  } else if (len > 3) {
    formatted = `${numericPart.slice(0, len - 3)}.${numericPart.slice(len - 3)}`
  } else {
    formatted = numericPart
  }

  // Add verifier if present
  if (verifier) {
    formatted += `-${verifier}`
  }

  formData.value.tax_id = formatted
}

const formErrors = computed(() => {
  if (!formSubmitted.value && touchedFields.value.size === 0) {
    return []
  }

  const errors: string[] = []

  // Validate tax_id
  const trimmedTaxId = formData.value.tax_id?.trim()
  if (!trimmedTaxId) {
    errors.push('El RUT es requerido')
  } else if (trimmedTaxId.length < 5) {
    errors.push('El RUT debe tener al menos 5 caracteres')
  } else if (!validateRut(trimmedTaxId)) {
    errors.push('El RUT no es válido (formato: XX.XXX.XXX-X)')
  }

  // Validate based on client type
  if (formData.value.client_type === 'individual') {
    if (!formData.value.first_name?.trim()) {
      errors.push('El nombre es requerido')
    }
    if (!formData.value.last_name?.trim()) {
      errors.push('El apellido es requerido')
    }
  } else {
    if (!formData.value.company_name?.trim()) {
      errors.push('La razón social es requerida')
    }
  }

  return errors
})

const validateFormField = (field: string) => {
  touchedFields.value.add(field)
  delete formFieldErrors.value[field]

  if (field === 'tax_id') {
    const trimmedTaxId = formData.value.tax_id?.trim()
    if (!trimmedTaxId) {
      formFieldErrors.value.tax_id = 'El RUT es requerido'
    } else if (trimmedTaxId.length < 5) {
      formFieldErrors.value.tax_id = 'Debe tener al menos 5 caracteres'
    } else if (!validateRut(trimmedTaxId)) {
      formFieldErrors.value.tax_id = 'RUT inválido'
    }
  }

  if (field === 'first_name' && formData.value.client_type === 'individual') {
    if (!formData.value.first_name?.trim()) {
      formFieldErrors.value.first_name = 'El nombre es requerido'
    }
  }

  if (field === 'last_name' && formData.value.client_type === 'individual') {
    if (!formData.value.last_name?.trim()) {
      formFieldErrors.value.last_name = 'El apellido es requerido'
    }
  }

  if (field === 'company_name' && formData.value.client_type === 'company') {
    if (!formData.value.company_name?.trim()) {
      formFieldErrors.value.company_name = 'La razón social es requerida'
    }
  }

  if (field === 'email' && formData.value.email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.value.email)) {
      formFieldErrors.value.email = 'El email no es válido'
    }
  }
}

// Computed
const filteredClients = computed(() => {
  if (!searchQuery.value) return clients.value
  const query = searchQuery.value.toLowerCase()
  return clients.value.filter((client) => {
    const name =
      client.client_type === 'individual'
        ? `${client.first_name || ''} ${client.last_name || ''}`
        : client.company_name || ''
    return (
      name.toLowerCase().includes(query) ||
      client.tax_id.toLowerCase().includes(query) ||
      (client.email?.toLowerCase().includes(query) ?? false)
    )
  })
})

// Phone number without +56 prefix
const phoneNumber = computed({
  get: () => {
    const phone = formData.value.phone || ''
    if (phone.startsWith('+56')) {
      return phone.slice(3).trim()
    }
    return phone
  },
  set: (value: string) => {
    // Remove any non-numeric characters except spaces
    const cleanValue = value.replace(/[^\d\s]/g, '')
    formData.value.phone = `+56 ${cleanValue}`.trim()
  },
})

// Methods
const loadClients = async () => {
  loading.value = true
  try {
    clients.value = await get<Client[]>('/clients/')
  } catch (err) {
    console.error('Error loading clients:', err)
  } finally {
    loading.value = false
  }
}

const goToList = () => {
  viewMode.value = 'list'
  editingClient.value = null
  resetForm()
  clearMessages()
}

const goToForm = (client?: Client) => {
  touchedFields.value.clear()
  formSubmitted.value = false
  formFieldErrors.value = {}

  if (client) {
    editingClient.value = client
    // Normalize phone number - ensure it has +56 prefix
    let phone = client.phone || ''
    if (phone && !phone.startsWith('+56')) {
      phone = '+56 ' + phone.replace(/^\+?56\s?/, '')
    }
    formData.value = {
      tax_id: client.tax_id,
      client_type: client.client_type,
      first_name: client.first_name || '',
      last_name: client.last_name || '',
      company_name: client.company_name || '',
      email: client.email || '',
      phone: phone || '+56',
      address: client.address || '',
    }
  } else {
    editingClient.value = null
    resetForm()
  }
  viewMode.value = 'form'
  clearMessages()
}

const resetForm = () => {
  formData.value = {
    tax_id: '',
    client_type: 'company',
    first_name: '',
    last_name: '',
    company_name: '',
    email: '',
    phone: '+56',
    address: '',
  }
  formFieldErrors.value = {}
  touchedFields.value.clear()
  formSubmitted.value = false
}

const clearMessages = () => {
  successMessage.value = ''
}

const saveClient = async () => {
  formSubmitted.value = true

  validateFormField('tax_id')
  if (formData.value.client_type === 'individual') {
    validateFormField('first_name')
    validateFormField('last_name')
  } else {
    validateFormField('company_name')
  }
  if (formData.value.email) {
    validateFormField('email')
  }

  if (formErrors.value.length > 0) {
    return
  }

  saving.value = true
  clearMessages()

  try {
    const submitData = {
      ...formData.value,
      tax_id: formData.value.tax_id.trim(),
    }

    if (editingClient.value) {
      const updateData: UpdateClientRequest = {}
      if (submitData.client_type === 'individual') {
        if (submitData.first_name !== editingClient.value.first_name) {
          updateData.first_name = submitData.first_name?.trim() || ''
        }
        if (submitData.last_name !== editingClient.value.last_name) {
          updateData.last_name = submitData.last_name?.trim() || ''
        }
      } else {
        if (submitData.company_name !== editingClient.value.company_name) {
          updateData.company_name = submitData.company_name?.trim() || ''
        }
      }
      if (submitData.email !== editingClient.value.email) {
        updateData.email = submitData.email?.trim() || undefined
      }
      if (submitData.phone !== editingClient.value.phone) {
        updateData.phone = submitData.phone?.trim() || undefined
      }
      if (submitData.address !== editingClient.value.address) {
        updateData.address = submitData.address?.trim() || undefined
      }

      await patch(`/clients/${editingClient.value.id}/`, updateData)
      successMessage.value = '¡Cliente actualizado exitosamente!'
      await loadClients()
      goToList()
    } else {
      await post<Client>('/clients/', submitData)
      successMessage.value = '¡Cliente creado exitosamente!'
      await loadClients()
      resetForm()
    }
  } catch (err: any) {
    console.error('Error saving client:', err)
    successMessage.value = err.message || 'Error al guardar el cliente. Por favor intenta de nuevo.'
  } finally {
    saving.value = false
  }
}

const confirmDelete = (client: Client) => {
  clientToDelete.value = client
  showDeleteModal.value = true
}

const deleteClient = async () => {
  if (!clientToDelete.value) return

  deleting.value = true
  try {
    await del(`/clients/${clientToDelete.value.id}/`)
    showDeleteModal.value = false
    clientToDelete.value = null
    successMessage.value = '¡Cliente eliminado exitosamente!'
    await loadClients()
  } catch (err) {
    console.error('Error deleting client:', err)
  } finally {
    deleting.value = false
  }
}

// Load clients on mount
onMounted(loadClients)
</script>

<template>
  <aside
    :class="[
      'fixed mt-16 flex flex-col lg:mt-0 top-0 px-5 left-0 bg-white dark:bg-gray-900 dark:border-gray-800 text-gray-900 h-screen transition-all duration-300 ease-in-out z-99999 border-r border-gray-200',
      {
        'lg:w-[290px]': isExpanded || isMobileOpen || isHovered,
        'lg:w-[90px]': !isExpanded && !isHovered,
        'translate-x-0 w-[290px]': isMobileOpen,
        '-translate-x-full': !isMobileOpen,
        'lg:translate-x-0': true,
      },
    ]"
    @mouseenter="!isExpanded && (isHovered = true)"
    @mouseleave="isHovered = false"
  >
    <div :class="['py-8 flex', !isExpanded && !isHovered ? 'lg:justify-center' : 'justify-start']">
      <router-link to="/">
        <img
          v-if="isExpanded || isHovered || isMobileOpen"
          src="/images/logo/logo.png"
          alt="AemePrint"
          class="h-10 w-auto object-contain"
        />
        <img v-else src="/images/logo/logo.png" alt="AemePrint" class="h-8 w-auto object-contain" />
      </router-link>
    </div>
    <div class="flex flex-col overflow-y-auto duration-300 ease-linear no-scrollbar">
      <nav class="mb-6">
        <div class="flex flex-col gap-4">
          <div>
            <h2
              :class="[
                'mb-4 text-xs uppercase flex leading-[20px] text-gray-400',
                !isExpanded && !isHovered ? 'lg:justify-center' : 'justify-start',
              ]"
            >
              <template v-if="isExpanded || isHovered || isMobileOpen"> Gestión </template>
              <HorizontalDots v-else />
            </h2>
            <ul class="flex flex-col gap-4">
              <li v-for="item in menuItems" :key="item.name">
                <!-- Item con sub-menú -->
                <template v-if="item.children">
                  <button
                    @click="toggleSubmenu(item.name)"
                    :class="[
                      'menu-item group w-full',
                      {
                        'menu-item-active': isSubmenuActive(item),
                        'menu-item-inactive': !isSubmenuActive(item),
                      },
                    ]"
                  >
                    <span
                      :class="[
                        isSubmenuActive(item) ? 'menu-item-icon-active' : 'menu-item-icon-inactive',
                      ]"
                    >
                      <component :is="item.icon" />
                    </span>
                    <span
                      v-if="isExpanded || isHovered || isMobileOpen"
                      class="menu-item-text flex-1 text-left"
                      >{{ item.name }}</span
                    >
                    <span
                      v-if="isExpanded || isHovered || isMobileOpen"
                      :class="[
                        'transition-transform duration-200',
                        expandedSubmenu === item.name ? 'rotate-180' : '',
                      ]"
                    >
                      <ChevronDownIcon />
                    </span>
                  </button>
                  <!-- Sub-menú -->
                  <ul
                    v-if="
                      (isExpanded || isHovered || isMobileOpen) && expandedSubmenu === item.name
                    "
                    class="mt-2 ml-8 flex flex-col gap-1"
                  >
                    <li v-for="child in item.children" :key="child.name">
                      <router-link
                        :to="child.path"
                        :class="[
                          'block px-3 py-2 text-sm rounded-lg transition-colors',
                          isActive(child.path)
                            ? 'bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200',
                        ]"
                      >
                        {{ child.name }}
                      </router-link>
                    </li>
                  </ul>
                </template>
                <!-- Item normal -->
                <router-link
                  v-else
                  :to="item.path"
                  :class="[
                    'menu-item group',
                    {
                      'menu-item-active': isActive(item.path),
                      'menu-item-inactive': !isActive(item.path),
                    },
                  ]"
                >
                  <span
                    :class="[
                      isActive(item.path) ? 'menu-item-icon-active' : 'menu-item-icon-inactive',
                    ]"
                  >
                    <component :is="item.icon" />
                  </span>
                  <span v-if="isExpanded || isHovered || isMobileOpen" class="menu-item-text">{{
                    item.name
                  }}</span>
                </router-link>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  LayoutDashboardIcon,
  UserGroupIcon,
  UserCircleIcon,
  DocsIcon,
  BoxCubeIcon,
  QuoteIcon,
  ChevronDownIcon,
  HorizontalDots,
  BoxIcon,
} from '../../icons'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const { isExpanded, isMobileOpen, isHovered } = useSidebar()
const authStore = useAuthStore()

const expandedSubmenu = ref(null)

const toggleSubmenu = (name) => {
  expandedSubmenu.value = expandedSubmenu.value === name ? null : name
}

const allMenuItems = [
  {
    icon: LayoutDashboardIcon,
    name: 'Panel',
    path: '/',
    requiresAdmin: false,
  },
  {
    icon: UserGroupIcon,
    name: 'Usuarios',
    path: '/users',
    requiresAdmin: true,
  },
  {
    icon: UserCircleIcon,
    name: 'Clientes',
    path: '/clients',
    requiresAdmin: false,
  },
  {
    icon: QuoteIcon,
    name: 'Cotización',
    requiresAdmin: false,
    children: [
      { name: 'Listado', path: '/quotes' },
      { name: 'Cotizar', path: '/quotes/new' },
    ],
  },
  {
    icon: DocsIcon,
    name: 'Papeles',
    path: '/papers',
    requiresAdmin: true,
  },
  {
    icon: BoxCubeIcon,
    name: 'Acabados',
    path: '/finishes',
    requiresAdmin: true,
  },
  {
    icon: BoxIcon,
    name: 'Productos Fijos',
    path: '/fixed-products',
    requiresAdmin: true,
  },
]

const menuItems = computed(() => {
  return allMenuItems.filter((item) => {
    if (!item.requiresAdmin) return true
    return authStore.isAdmin
  })
})

const isActive = (path) => {
  // Para rutas como /quotes y /quotes/new
  if (path === '/quotes') {
    return route.path === '/quotes' || route.path === '/quotes/new'
  }
  return route.path === path
}

const isSubmenuActive = (item) => {
  if (!item.children) return false
  return item.children.some((child) => isActive(child.path))
}
</script>

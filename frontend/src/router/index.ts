import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { left: 0, top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'Ecommerce',
      component: () => import('../views/Ecommerce.vue'),
      meta: {
        title: 'eCommerce Dashboard',
        requiresAuth: true,
      },
    },
    {
      path: '/calendar',
      name: 'Calendar',
      component: () => import('../views/Others/Calendar.vue'),
      meta: {
        title: 'Calendar',
      },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Others/UserProfile.vue'),
      meta: {
        title: 'Profile',
      },
    },
    {
      path: '/form-elements',
      name: 'Form Elements',
      component: () => import('../views/Forms/FormElements.vue'),
      meta: {
        title: 'Form Elements',
      },
    },
    {
      path: '/basic-tables',
      name: 'Basic Tables',
      component: () => import('../views/Tables/BasicTables.vue'),
      meta: {
        title: 'Basic Tables',
      },
    },
    {
      path: '/line-chart',
      name: 'Line Chart',
      component: () => import('../views/Chart/LineChart/LineChart.vue'),
    },
    {
      path: '/bar-chart',
      name: 'Bar Chart',
      component: () => import('../views/Chart/BarChart/BarChart.vue'),
    },
    {
      path: '/alerts',
      name: 'Alerts',
      component: () => import('../views/UiElements/Alerts.vue'),
      meta: {
        title: 'Alerts',
      },
    },
    {
      path: '/avatars',
      name: 'Avatars',
      component: () => import('../views/UiElements/Avatars.vue'),
      meta: {
        title: 'Avatars',
      },
    },
    {
      path: '/badge',
      name: 'Badge',
      component: () => import('../views/UiElements/Badges.vue'),
      meta: {
        title: 'Badge',
      },
    },

    {
      path: '/buttons',
      name: 'Buttons',
      component: () => import('../views/UiElements/Buttons.vue'),
      meta: {
        title: 'Buttons',
      },
    },

    {
      path: '/images',
      name: 'Images',
      component: () => import('../views/UiElements/Images.vue'),
      meta: {
        title: 'Images',
      },
    },
    {
      path: '/videos',
      name: 'Videos',
      component: () => import('../views/UiElements/Videos.vue'),
      meta: {
        title: 'Videos',
      },
    },
    {
      path: '/blank',
      name: 'Blank',
      component: () => import('../views/Pages/BlankPage.vue'),
      meta: {
        title: 'Blank',
      },
    },

    {
      path: '/error-404',
      name: '404 Error',
      component: () => import('../views/Errors/FourZeroFour.vue'),
      meta: {
        title: '404 Error',
      },
    },

    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Auth/Signin.vue'),
      meta: {
        title: 'Login',
        requiresGuest: true,
      },
    },
    {
      path: '/signup',
      name: 'Signup',
      component: () => import('../views/Auth/Signup.vue'),
      meta: {
        title: 'Signup',
      },
    },
    {
      path: '/users',
      name: 'Users',
      component: () => import('../views/Users/UsersView.vue'),
      meta: {
        title: 'Users',
        requiresAuth: true,
        requiresAdmin: true,
      },
    },
    {
      path: '/clients',
      name: 'Clients',
      component: () => import('../views/Clients/ClientsView.vue'),
      meta: {
        title: 'Clients',
        requiresAuth: true,
      },
    },
    {
      path: '/papers',
      name: 'Papers',
      component: () => import('../views/Papers/PapersView.vue'),
      meta: {
        title: 'Papers',
        requiresAuth: true,
        requiresAdmin: true,
      },
    },
    {
      path: '/finishes',
      name: 'Finishes',
      component: () => import('../views/Finishes/FinishesView.vue'),
      meta: {
        title: 'Finishes',
        requiresAuth: true,
        requiresAdmin: true,
      },
    },
    {
      path: '/fixed-products',
      name: 'FixedProducts',
      component: () => import('../views/FixedProducts/FixedProductsView.vue'),
      meta: {
        title: 'Productos Fijos',
        requiresAuth: true,
        requiresAdmin: true,
      },
    },
    {
      path: '/quotes',
      name: 'QuotesList',
      component: () => import('../views/Quotes/QuotesListView.vue'),
      meta: {
        title: 'Cotizaciones',
        requiresAuth: true,
      },
    },
    {
      path: '/quotes/new',
      name: 'QuotesCreate',
      component: () => import('../views/Quotes/QuotesCreateView.vue'),
      meta: {
        title: 'Nueva Cotización',
        requiresAuth: true,
      },
    },
    {
      path: '/quotes/:id',
      name: 'QuotesDetail',
      component: () => import('../views/Quotes/QuotesDetailView.vue'),
      meta: {
        title: 'Detalle Cotización',
        requiresAuth: true,
      },
    },
  ],
})

export default router

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  await authStore.initialize()

  document.title = to.meta.title ? `${to.meta.title} | AemePrint` : 'AemePrint'

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
    return
  }

  if (to.meta.requiresAdmin && authStore.isAuthenticated) {
    if (!authStore.user) {
      await authStore.fetchCurrentUser()
    }
    if (!authStore.isAdmin) {
      next('/')
      return
    }
  }

  next()
})

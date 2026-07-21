import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { supabase } from '@/config/supabase'
import { API_CONFIG } from '@/config/api'

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  VENDEDOR = 'vendedor',
}

interface User {
  id: string
  name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)
  let initialization: Promise<void> | null = null

  const isAuthenticated = computed(() => token.value !== null)
  const isAdmin = computed(
    () => user.value?.role === UserRole.ADMIN || user.value?.role === UserRole.SUPER_ADMIN,
  )
  const isSuperAdmin = computed(() => user.value?.role === UserRole.SUPER_ADMIN)
  const isVendedor = computed(() => user.value?.role === UserRole.VENDEDOR)

  const applySession = (accessToken: string | null) => {
    token.value = accessToken
    if (!accessToken) {
      user.value = null
    }
  }

  const initialize = async () => {
    if (initialization) return initialization
    initialization = (async () => {
      const { data } = await supabase.auth.getSession()
      applySession(data.session?.access_token ?? null)
      supabase.auth.onAuthStateChange((_event, session) =>
        applySession(session?.access_token ?? null),
      )
      isInitialized.value = true
    })()
    return initialization
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (signInError || !data.session) {
        error.value = 'Correo o contraseña inválidos'
        return false
      }
      applySession(data.session.access_token)
      return await fetchCurrentUser()
    } finally {
      loading.value = false
    }
  }

  const signup = async (
    email: string,
    password: string,
    name: string,
  ): Promise<'signed_in' | 'confirmation_required' | false> => {
    loading.value = true
    error.value = null
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name } },
      })
      if (signUpError) {
        error.value = 'No fue posible crear la cuenta'
        return false
      }
      applySession(data.session?.access_token ?? null)
      return data.session ? 'signed_in' : 'confirmation_required'
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await supabase.auth.signOut()
    } finally {
      applySession(null)
    }
  }

  const fetchCurrentUser = async (): Promise<boolean> => {
    if (!token.value) return false
    const response = await fetch(`${API_CONFIG.BASE_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token.value}` },
    })
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) await logout()
      return false
    }
    user.value = await response.json()
    return true
  }

  return {
    token,
    user,
    loading,
    error,
    isInitialized,
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    isVendedor,
    initialize,
    login,
    signup,
    logout,
    fetchCurrentUser,
  }
})

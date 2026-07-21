import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()

  return {
    token: authStore.token,
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    login: authStore.login,
    signup: authStore.signup,
    logout: authStore.logout,
    fetchCurrentUser: authStore.fetchCurrentUser,
  }
}

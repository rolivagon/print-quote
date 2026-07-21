import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import { API_CONFIG } from '@/config/api'

export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const authStore = useAuthStore()

  const request = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
    loading.value = true
    error.value = null

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
      ...((options.headers as Record<string, string>) || {}),
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
        ...options,
        headers,
      })

      if (!response.ok) {
        // Handle 401 Unauthorized - redirect to login
        if (response.status === 401) {
          await authStore.logout()
          router.push('/login')
          throw new Error('Session expired. Please log in again.')
        }

        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      // Handle empty responses (e.g., DELETE)
      if (response.status === 204) {
        return undefined as T
      }

      return (await response.json()) as T
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    } finally {
      loading.value = false
    }
  }

  const get = <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' })
  const post = <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) })
  const patch = <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) })
  const del = <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' })

  return {
    loading,
    error,
    get,
    post,
    patch,
    del,
    request,
  }
}

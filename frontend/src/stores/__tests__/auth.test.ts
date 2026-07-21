import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

let authStateListener:
  | ((event: string, session: { access_token: string } | null) => void)
  | undefined

const auth = {
  getSession: vi.fn(),
  onAuthStateChange: vi.fn((listener) => {
    authStateListener = listener
    return { data: { subscription: { unsubscribe: vi.fn() } } }
  }),
  signInWithPassword: vi.fn(),
  signOut: vi.fn(),
  signUp: vi.fn(),
}

vi.mock('@/config/supabase', () => ({ supabase: { auth } }))

const { useAuthStore } = await import('@/stores/auth')

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    authStateListener = undefined
    vi.clearAllMocks()
  })

  it('restores a persisted session before route guards evaluate authentication', async () => {
    auth.getSession.mockResolvedValue({ data: { session: { access_token: 'restored-token' } } })
    const store = useAuthStore()

    await store.initialize()

    expect(store.isInitialized).toBe(true)
    expect(store.token).toBe('restored-token')
    expect(store.isAuthenticated).toBe(true)
  })

  it('uses the refreshed access token delivered by Supabase', async () => {
    auth.getSession.mockResolvedValue({ data: { session: { access_token: 'old-token' } } })
    const store = useAuthStore()
    await store.initialize()

    authStateListener?.('TOKEN_REFRESHED', { access_token: 'refreshed-token' })

    expect(store.token).toBe('refreshed-token')
  })

  it('clears local state even when remote sign-out fails', async () => {
    auth.getSession.mockResolvedValue({ data: { session: { access_token: 'session-token' } } })
    auth.signOut.mockRejectedValue(new Error('network unavailable'))
    const store = useAuthStore()
    await store.initialize()

    await expect(store.logout()).rejects.toThrow('network unavailable')
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('does not expose a supplied password in the login error state', async () => {
    const sentinelPassword = 'SENTINEL-PLAINTEXT-PASSWORD-DO-NOT-LOG'
    auth.signInWithPassword.mockResolvedValue({ data: {}, error: new Error('invalid credentials') })
    const store = useAuthStore()

    await store.login('user@example.com', sentinelPassword)

    expect(store.error).not.toContain(sentinelPassword)
  })
})

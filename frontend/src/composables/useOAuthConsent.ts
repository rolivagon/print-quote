import { computed, ref } from 'vue'

import type { supabase } from '@/config/supabase'

type OAuthApi = Pick<
  typeof supabase.auth.oauth,
  'getAuthorizationDetails' | 'approveAuthorization' | 'denyAuthorization'
>
type AuthorizationDetails = {
  authorization_id: string
  client: { name: string }
  user: { email: string }
  scope: string
}
type ConsentState = 'loading' | 'consent' | 'redirecting' | 'forbidden' | 'error'

export function useOAuthConsent(
  oauth: OAuthApi,
  verifyProfile: () => Promise<boolean>,
  navigate: (url: string) => void,
) {
  const state = ref<ConsentState>('loading')
  const details = ref<AuthorizationDetails | null>(null)
  const submitting = ref(false)
  const scopes = computed(() => details.value?.scope.split(' ').filter(Boolean) ?? [])

  const load = async (authorizationId: unknown) => {
    state.value = 'loading'
    details.value = null
    if (typeof authorizationId !== 'string' || !authorizationId) {
      state.value = 'error'
      return
    }
    if (!(await verifyProfile())) {
      state.value = 'forbidden'
      return
    }

    const { data, error } = await oauth.getAuthorizationDetails(authorizationId)
    if (error || !data) {
      state.value = 'error'
    } else if ('authorization_id' in data) {
      details.value = data
      state.value = 'consent'
    } else {
      // The user already approved this client, so Supabase returns the code directly.
      state.value = 'redirecting'
      navigate(data.redirect_url)
    }
  }

  const decide = async (decision: OAuthApi['approveAuthorization']) => {
    if (state.value !== 'consent' || !details.value || submitting.value) return
    submitting.value = true
    try {
      const { data, error } = await decision(details.value.authorization_id, {
        skipBrowserRedirect: true,
      })
      if (error || !data) {
        state.value = 'error'
        return
      }
      state.value = 'redirecting'
      navigate(data.redirect_url)
    } finally {
      submitting.value = false
    }
  }

  return {
    state,
    details,
    scopes,
    submitting,
    load,
    approve: () => decide(oauth.approveAuthorization),
    deny: () => decide(oauth.denyAuthorization),
  }
}

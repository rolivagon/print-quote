import { describe, expect, it, vi } from 'vitest'

import { useOAuthConsent } from '@/composables/useOAuthConsent'

const details = {
  authorization_id: 'auth-1',
  redirect_uri: 'https://chatgpt.com/callback',
  client: { id: 'client-1', name: 'ChatGPT', uri: '', logo_uri: '' },
  user: { id: 'user-1', email: 'seller@example.com' },
  scope: 'openid email',
}

const setup = (overrides: { profileOk?: boolean } = {}) => {
  const oauth = {
    getAuthorizationDetails: vi.fn().mockResolvedValue({ data: details, error: null }),
    approveAuthorization: vi
      .fn()
      .mockResolvedValue({ data: { redirect_url: 'https://client/cb?code=1' }, error: null }),
    denyAuthorization: vi
      .fn()
      .mockResolvedValue({
        data: { redirect_url: 'https://client/cb?error=access_denied' },
        error: null,
      }),
  }
  const verifyProfile = vi.fn().mockResolvedValue(overrides.profileOk ?? true)
  const navigate = vi.fn()
  const consent = useOAuthConsent(oauth, verifyProfile, navigate)
  return { oauth, verifyProfile, navigate, consent }
}

describe('useOAuthConsent', () => {
  it('shows the consent screen with client, user and scopes', async () => {
    const { consent, navigate } = setup()

    await consent.load('auth-1')

    expect(consent.state.value).toBe('consent')
    expect(consent.details.value?.client.name).toBe('ChatGPT')
    expect(consent.details.value?.user.email).toBe('seller@example.com')
    expect(consent.scopes.value).toEqual(['openid', 'email'])
    expect(navigate).not.toHaveBeenCalled()
  })

  it('redirects immediately when the client was already approved', async () => {
    const { consent, oauth, navigate } = setup()
    oauth.getAuthorizationDetails.mockResolvedValue({
      data: { redirect_url: 'https://client/cb?code=2' },
      error: null,
    })

    await consent.load('auth-1')

    expect(consent.state.value).toBe('redirecting')
    expect(navigate).toHaveBeenCalledWith('https://client/cb?code=2')
  })

  it('approves and returns to the client', async () => {
    const { consent, oauth, navigate } = setup()
    await consent.load('auth-1')

    await consent.approve()

    expect(oauth.approveAuthorization).toHaveBeenCalledWith('auth-1', { skipBrowserRedirect: true })
    expect(navigate).toHaveBeenCalledWith('https://client/cb?code=1')
  })

  it('denies and returns the error to the client', async () => {
    const { consent, oauth, navigate } = setup()
    await consent.load('auth-1')

    await consent.deny()

    expect(oauth.denyAuthorization).toHaveBeenCalledWith('auth-1', { skipBrowserRedirect: true })
    expect(navigate).toHaveBeenCalledWith('https://client/cb?error=access_denied')
  })

  it.each([undefined, '', ['auth-1']])('rejects a missing authorization id %j', async (id) => {
    const { consent, oauth } = setup()

    await consent.load(id)

    expect(consent.state.value).toBe('error')
    expect(oauth.getAuthorizationDetails).not.toHaveBeenCalled()
  })

  it('shows an error for an unknown or expired authorization', async () => {
    const { consent, oauth, navigate } = setup()
    oauth.getAuthorizationDetails.mockResolvedValue({ data: null, error: new Error('not found') })

    await consent.load('expired')
    await consent.approve()

    expect(consent.state.value).toBe('error')
    expect(oauth.approveAuthorization).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
  })

  it('denies access to an inactive or unknown profile without approving', async () => {
    const { consent, oauth, navigate } = setup({ profileOk: false })

    await consent.load('auth-1')
    await consent.approve()

    expect(consent.state.value).toBe('forbidden')
    expect(oauth.getAuthorizationDetails).not.toHaveBeenCalled()
    expect(oauth.approveAuthorization).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
  })
})

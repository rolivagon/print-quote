import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import { useUserPasswordReset } from '@/composables/useUserPasswordReset'
import type { User } from '@/types'

const user: User = {
  id: 'user-id',
  name: 'Test User',
  email: 'user@example.com',
  role: 'vendedor',
  is_active: true,
}

describe('useUserPasswordReset', () => {
  it('does not open for a non-superadmin', () => {
    const reset = useUserPasswordReset(vi.fn(), ref(false))

    reset.openPasswordModal(user)

    expect(reset.showPasswordModal.value).toBe(false)
    expect(reset.passwordUser.value).toBeNull()
  })

  it('clears entered values when cancelled', () => {
    const reset = useUserPasswordReset(vi.fn(), ref(true))
    reset.openPasswordModal(user)
    reset.newPassword.value = 'Updated-password-123'
    reset.passwordConfirmation.value = 'Updated-password-123'

    reset.closePasswordModal()

    expect(reset.showPasswordModal.value).toBe(false)
    expect(reset.passwordUser.value).toBeNull()
    expect(reset.newPassword.value).toBe('')
    expect(reset.passwordConfirmation.value).toBe('')
  })

  it('shows a mismatch without sending a request', async () => {
    const post = vi.fn()
    const reset = useUserPasswordReset(post, ref(true))
    reset.openPasswordModal(user)
    reset.newPassword.value = 'Updated-password-123'
    reset.passwordConfirmation.value = 'different-password-123'

    await expect(reset.updatePassword()).resolves.toBe(false)

    expect(reset.passwordMismatch.value).toBe(true)
    expect(reset.passwordError.value).toBe('Las contraseñas deben coincidir')
    expect(post).not.toHaveBeenCalled()
  })

  it('sends one password-only request and clears values on success', async () => {
    const post = vi.fn().mockResolvedValue(undefined)
    const reset = useUserPasswordReset(post, ref(true))
    reset.openPasswordModal(user)
    reset.newPassword.value = 'Updated-password-123'
    reset.passwordConfirmation.value = 'Updated-password-123'

    await expect(reset.updatePassword()).resolves.toBe(true)

    expect(post).toHaveBeenCalledOnce()
    expect(post).toHaveBeenCalledWith('/users/user-id/password/', {
      password: 'Updated-password-123',
    })
    expect(reset.newPassword.value).toBe('')
    expect(reset.passwordConfirmation.value).toBe('')
  })
})

import { computed, ref, type Ref } from 'vue'

import type { User, UserPasswordUpdateRequest } from '@/types'

type PasswordPost = (endpoint: string, payload: UserPasswordUpdateRequest) => Promise<void>

export function useUserPasswordReset(post: PasswordPost, canResetPasswords: Ref<boolean>) {
  const showPasswordModal = ref(false)
  const passwordUser = ref<User | null>(null)
  const newPassword = ref('')
  const passwordConfirmation = ref('')
  const passwordError = ref('')
  const resettingPassword = ref(false)
  const passwordMismatch = computed(
    () =>
      Boolean(newPassword.value) &&
      Boolean(passwordConfirmation.value) &&
      newPassword.value !== passwordConfirmation.value,
  )

  const clear = () => {
    passwordUser.value = null
    newPassword.value = ''
    passwordConfirmation.value = ''
    passwordError.value = ''
  }

  const openPasswordModal = (user: User) => {
    if (!canResetPasswords.value) return
    clear()
    passwordUser.value = user
    showPasswordModal.value = true
  }

  const closePasswordModal = () => {
    showPasswordModal.value = false
    clear()
  }

  const updatePassword = async (): Promise<boolean> => {
    if (!passwordUser.value) return false
    if (passwordMismatch.value) {
      passwordError.value = 'Las contraseñas deben coincidir'
      return false
    }

    resettingPassword.value = true
    passwordError.value = ''
    try {
      await post(`/users/${passwordUser.value.id}/password/`, { password: newPassword.value })
      closePasswordModal()
      return true
    } catch {
      passwordError.value = 'No fue posible actualizar la contraseña'
      return false
    } finally {
      resettingPassword.value = false
    }
  }

  return {
    showPasswordModal,
    passwordUser,
    newPassword,
    passwordConfirmation,
    passwordError,
    resettingPassword,
    passwordMismatch,
    openPasswordModal,
    closePasswordModal,
    updatePassword,
  }
}

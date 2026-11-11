import { describe, expect, it } from 'vitest'

import { safeReturnPath } from '@/router/returnPath'

describe('safeReturnPath', () => {
  it('keeps an internal path with its query', () => {
    expect(safeReturnPath('/oauth/consent?authorization_id=abc')).toBe(
      '/oauth/consent?authorization_id=abc',
    )
  })

  it.each([
    'https://evil.example/steal',
    '//evil.example/steal',
    '/\\evil.example',
    'oauth/consent',
    '',
    undefined,
    null,
    ['/clients'],
  ])('falls back to the dashboard for %j', (value) => {
    expect(safeReturnPath(value)).toBe('/')
  })
})

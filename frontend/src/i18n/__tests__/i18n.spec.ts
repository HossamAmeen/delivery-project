import { describe, expect, it } from 'vitest'

import { t } from '..'

describe('t()', () => {
  it('looks up nested keys and interpolates params', () => {
    expect(t('login.title')).toBe('Sign in')
    expect(t('login.rateLimitedSeconds', { seconds: 5 })).toBe(
      'Too many sign-in attempts. Please try again in 5 seconds.',
    )
  })

  it('returns the key for unknown or non-leaf keys', () => {
    expect(t('nope.missing')).toBe('nope.missing')
    expect(t('login')).toBe('login')
  })
})

import { describe, expect, it } from 'vitest'

import { ApiError, kindForStatus, parseRetryAfter, splitErrors } from '../errors'

describe('parseRetryAfter', () => {
  it('parses delta-seconds', () => {
    expect(parseRetryAfter('30')).toBe(30)
  })

  it('parses an HTTP date relative to now', () => {
    const now = Date.parse('2026-09-27T10:00:00Z')
    expect(parseRetryAfter('Sun, 27 Sep 2026 10:00:45 GMT', now)).toBe(45)
  })

  it('returns null for missing or invalid values', () => {
    expect(parseRetryAfter(null)).toBeNull()
    expect(parseRetryAfter('')).toBeNull()
    expect(parseRetryAfter('soon')).toBeNull()
  })
})

describe('splitErrors', () => {
  it('separates code from field errors', () => {
    expect(
      splitErrors({ code: 'VALIDATION_ERROR', username: ['Required.'], non_field_errors: 'x' }),
    ).toEqual({
      code: 'VALIDATION_ERROR',
      fieldErrors: { username: ['Required.'], non_field_errors: ['x'] },
    })
  })

  it('ignores non-object payloads and nested objects', () => {
    expect(splitErrors(null)).toEqual({ code: null, fieldErrors: {} })
    expect(splitErrors({ checks: { db: 'ok' } })).toEqual({ code: null, fieldErrors: {} })
  })
})

describe('kindForStatus / ApiError', () => {
  it.each([
    [0, 'network'],
    [400, 'validation'],
    [401, 'unauthorized'],
    [403, 'forbidden'],
    [404, 'not_found'],
    [409, 'conflict'],
    [429, 'rate_limited'],
    [500, 'server'],
    [503, 'server'],
    [418, 'unknown'],
  ])('maps %i to %s', (status, kind) => {
    expect(kindForStatus(status)).toBe(kind)
    expect(new ApiError({ status, message: 'm' }).kind).toBe(kind)
  })
})

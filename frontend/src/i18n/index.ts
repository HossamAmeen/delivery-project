import { en } from './en'

type Params = Record<string, string | number>

/**
 * Minimal translation helper: `t('login.title')`, `t('status.unexpected', { status })`.
 * One locale (English) until BLK-009; unknown keys return the key so gaps are visible.
 */
export function t(key: string, params: Params = {}): string {
  let node: unknown = en
  for (const part of key.split('.')) {
    if (node && typeof node === 'object' && part in node) {
      node = (node as Record<string, unknown>)[part]
    } else {
      return key
    }
  }
  if (typeof node !== 'string') return key
  return node.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  )
}

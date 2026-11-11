// Only same-origin paths are honored so the login page cannot be used as an open redirect.
export function safeReturnPath(value: unknown): string {
  if (typeof value !== 'string' || !value.startsWith('/') || /^\/[/\\]/.test(value)) return '/'
  return value
}

import { createClient } from '@supabase/supabase-js'

const configuredUrl = import.meta.env.VITE_SUPABASE_URL
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

if (!configuredUrl || !publishableKey) {
  throw new Error('VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY are required')
}

// Vite proxies this path to local Supabase, so remote tunnel visitors never use their own localhost.
const url = new URL(configuredUrl, window.location.origin).toString()

export const supabase = createClient(url, publishableKey)

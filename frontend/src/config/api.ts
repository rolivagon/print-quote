// Use the current origin by default. Vite proxies /api to the local backend in development.

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || '/api',
  TIMEOUT: 30000, // 30 seconds
}

// Helper to get full API URL
export const getApiUrl = (endpoint: string): string => {
  // If already has BASE_URL, don't duplicate
  if (endpoint.startsWith(API_CONFIG.BASE_URL)) {
    return endpoint
  }
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${API_CONFIG.BASE_URL}${cleanEndpoint}`
}

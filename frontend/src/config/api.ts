// API Configuration - Centralized for easy changes
// In development: use localhost:5001/api
// In production: use relative path /api (backend serves frontend)
const isProduction = import.meta.env.PROD

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || (isProduction ? '/api' : 'http://localhost:5001/api'),
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

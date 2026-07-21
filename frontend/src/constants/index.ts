// ============================================
// Constantes Centralizadas de la Aplicación
// ============================================

import type { ColorMode, PrintType, QuoteStatus, Unit } from '@/types'

// ============================================
// OPCIONES DE UNIDADES (para terminaciones/acabados)
// ============================================

export interface UnitOption {
  value: Unit
  label: string
  shortLabel: string
}

export const UNIT_OPTIONS: UnitOption[] = [
  { value: 'job', label: 'Por Trabajo', shortLabel: 'Trabajo' },
  { value: 'per_item', label: 'Por Artículo', shortLabel: 'Artículo' },
  { value: 'sheet', label: 'Por Hoja', shortLabel: 'Hoja' },
  { value: 'per_1000', label: 'Por 1000', shortLabel: '1000' },
  { value: 'sqm', label: 'Por m²', shortLabel: 'm²' },
]

// Helper para obtener label de unidad
export const getUnitLabel = (unit: Unit | undefined): string => {
  if (!unit) return '-'
  const option = UNIT_OPTIONS.find((opt) => opt.value === unit)
  return option?.label || unit
}

// Helper para obtener short label de unidad
export const getUnitShortLabel = (unit: Unit | undefined): string => {
  if (!unit) return '-'
  const option = UNIT_OPTIONS.find((opt) => opt.value === unit)
  return option?.shortLabel || unit
}

// Mapa de unidades para uso rápido
export const UNIT_LABELS: Record<Unit, string> = {
  job: 'Por Trabajo',
  per_item: 'Por Artículo',
  sheet: 'Por Hoja',
  per_1000: 'Por 1000',
  sqm: 'Por m²',
}

// ============================================
// OPCIONES DE TIPOS DE IMPRESIÓN
// ============================================

export interface PrintTypeOption {
  value: PrintType
  label: string
}

export const PRINT_TYPE_OPTIONS: PrintTypeOption[] = [
  { value: 'digital', label: 'Digital' },
  { value: 'offset', label: 'Offset' },
  { value: 'plotter', label: 'Plotter' },
]

// Array de valores para iteraciones
export const PRINT_TYPES: PrintType[] = ['digital', 'offset', 'plotter']

// Helper para obtener label de tipo de impresión
export const getPrintTypeLabel = (type: PrintType | undefined): string => {
  if (!type) return '-'
  const option = PRINT_TYPE_OPTIONS.find((opt) => opt.value === type)
  return option?.label || type
}

// Mapa de tipos de impresión para uso rápido
export const PRINT_TYPE_LABELS: Record<PrintType, string> = {
  digital: 'Digital',
  offset: 'Offset',
  plotter: 'Plotter',
}

// ============================================
// OPCIONES DE UI/TAMAÑOS
// ============================================

export type Size = 'xsmall' | 'small' | 'medium' | 'large' | 'xlarge' | 'xxlarge'

export const SIZE_OPTIONS: Size[] = ['xsmall', 'small', 'medium', 'large', 'xlarge', 'xxlarge']

// ============================================
// OPCIONES DE ESTADOS/STATUS
// ============================================

export type UserStatus = 'online' | 'offline' | 'busy' | 'none'

export const USER_STATUS_OPTIONS: { value: UserStatus; label: string }[] = [
  { value: 'online', label: 'En Línea' },
  { value: 'offline', label: 'Desconectado' },
  { value: 'busy', label: 'Ocupado' },
  { value: 'none', label: 'Ninguno' },
]

export const getUserStatusLabel = (status: UserStatus): string => {
  const option = USER_STATUS_OPTIONS.find((opt) => opt.value === status)
  return option?.label || status
}

// ============================================
// COLORES DEL TEMA
// ============================================

export type ThemeColor = 'primary' | 'success' | 'error' | 'warning' | 'info' | 'light' | 'dark'

export const THEME_COLORS: ThemeColor[] = [
  'primary',
  'success',
  'error',
  'warning',
  'info',
  'light',
  'dark',
]

// ============================================
// OPCIONES DE MODOS DE COLOR
// ============================================

export interface ColorModeOption {
  value: ColorMode
  label: string
  description: string
}

export const COLOR_MODE_OPTIONS: ColorModeOption[] = [
  { value: '4/0', label: '4/0', description: 'Color Frente' },
  { value: '4/4', label: '4/4', description: 'Color Ambos Lados' },
]

export const getColorModeLabel = (mode: ColorMode | undefined): string => {
  if (!mode) return '-'
  const option = COLOR_MODE_OPTIONS.find((opt) => opt.value === mode)
  return option ? `${option.label} (${option.description})` : mode
}

// Mapa de modos de color para uso rápido
export const COLOR_MODE_LABELS: Record<ColorMode, string> = {
  '4/0': '4/0 (Color Frente)',
  '4/4': '4/4 (Color Ambos Lados)',
}

// ============================================
// CONFIGURACIÓN DE PLIEGOS POR DEFECTO
// ============================================

export interface DefaultSheetConfig {
  usable_width_cm: number
  usable_height_cm: number
}

export const DEFAULT_SHEET_CONFIGS: Record<PrintType, DefaultSheetConfig> = {
  digital: { usable_width_cm: 31, usable_height_cm: 46 },
  offset: { usable_width_cm: 60, usable_height_cm: 46 },
  plotter: { usable_width_cm: 70, usable_height_cm: 50 },
}

// ============================================
// OPCIONES DE ESTADOS DE COTIZACIÓN
// ============================================

export interface QuoteStatusOption {
  value: QuoteStatus
  label: string
  color: 'primary' | 'warning' | 'success' | 'error'
}

export const QUOTE_STATUS_OPTIONS: QuoteStatusOption[] = [
  { value: 'draft', label: 'Borrador', color: 'primary' },
  { value: 'sent', label: 'Enviada', color: 'warning' },
  { value: 'approved', label: 'Aprobada', color: 'success' },
  { value: 'rejected', label: 'Rechazada', color: 'error' },
]

export const getQuoteStatusLabel = (status: QuoteStatus | undefined): string => {
  if (!status) return '-'
  const option = QUOTE_STATUS_OPTIONS.find((opt) => opt.value === status)
  return option?.label || status
}

export const getQuoteStatusColor = (status: QuoteStatus | undefined): string => {
  if (!status) return 'gray'
  const option = QUOTE_STATUS_OPTIONS.find((opt) => opt.value === status)
  const colorMap: Record<string, string> = {
    primary: 'blue',
    warning: 'yellow',
    success: 'green',
    error: 'red',
  }
  return option ? colorMap[option.color] : 'gray'
}

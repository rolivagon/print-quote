// Paper Types
export interface Paper {
  id: number
  name: string
  weight: number
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface CreatePaperRequest {
  name: string
  weight: number
  description?: string
}

export interface UpdatePaperRequest {
  name?: string
  weight?: number
  description?: string
}

// Paper Pricing Types
export interface PaperPricing {
  id: number
  paper_id: number
  print_type: PrintType
  min_quantity: number
  max_quantity: number | null
  unit_price: string
}

export interface CreatePaperPricingRequest {
  print_type: PrintType
  min_quantity: number
  max_quantity?: number
  unit_price: string
}

export interface UpdatePaperPricingRequest {
  print_type?: PrintType
  min_quantity?: number
  max_quantity?: number | null
  unit_price?: string
}

// Finish Types
export interface Finish {
  id: number
  name: string
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface CreateFinishRequest {
  name: string
  description?: string
}

export interface UpdateFinishRequest {
  name?: string
  description?: string
}

export interface FinishPricing {
  id: number
  finish_id: number
  print_type: PrintType
  unit: Unit
  min_quantity: number
  max_quantity: number | null
  unit_price: string
}

// Enums
export type PrintType = 'digital' | 'offset' | 'plotter'

export type Unit = 'sheet' | 'sqm' | 'per_1000' | 'job' | 'per_item'

// Generic Pricing Range for UI
export interface PricingRange {
  id?: number
  print_type: PrintType
  min_quantity: number
  max_quantity: number | null
  unit_price: string
  unit?: Unit
}

// Client Types
export type ClientType = 'individual' | 'company'

export interface Client {
  id: number
  tax_id: string
  client_type: ClientType
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface CreateClientRequest {
  tax_id: string
  client_type: ClientType
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
}

export interface UpdateClientRequest {
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
}

// User Role
export type UserRole = 'super_admin' | 'admin' | 'vendedor'

// User Types
export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface CreateUserRequest {
  name: string
  email: string
  role: UserRole
}

export interface UpdateUserRequest {
  name?: string
  is_active?: boolean
  role?: UserRole
}

export interface UserPasswordUpdateRequest {
  password: string
}

// API Response Types
export interface ApiError {
  detail: string
}

// Quote Types
export type QuoteStatus = 'draft' | 'sent' | 'approved' | 'rejected'

export type ColorMode = '4/0' | '4/4'

export interface SheetConfig {
  usable_width_cm: number
  usable_height_cm: number
}

export interface QuoteFinishItem {
  finish_id: number
  quantity: number
}

export interface QuoteItem {
  name: string
  description?: string
  print_type: PrintType
  quantity: number
  width_cm: number
  height_cm: number
  width?: number
  height?: number
  paper_id: number
  color_mode: ColorMode | ''
  sheet_config?: SheetConfig
  finishes: number[]
  loss_percentage: number
  num_designs?: number
  merma_per_design?: number
}

export interface QuoteItemResponse extends QuoteItem {
  id: number
  quote_id: number
  paper_unit_price: string
  pieces_per_sheet: number | null
  sheets_needed: number | null
  total_sheets_with_merma: number | null
  square_meters: string | null
  material_cost: string
  finishing_cost: string
  plates_cost: string
  run_cost: string
  fixed_costs: string
  paper_cost: string
  subtotal_before_losses: string
  subtotal_with_losses: string
  iva_amount: string
  total_final: string
  created_at: string
  width: number
  height: number
  calculation_details?: {
    specifications?: {
      paper?: { name?: string }
      finishes?: Array<{ id: number; name: string; calculated_cost: string }>
    }
  }
}

export interface Quote {
  id: number
  quote_number: string
  client_id: number
  seller_id: string
  status: QuoteStatus
  subtotal: string
  tax: string
  total: string
  created_at: string
  updated_at: string | null
  items?: QuoteItemResponse[]
  client?: Client
}

export interface QuoteCreateRequest {
  client_id: number
  items: QuoteItem[]
}

export interface QuoteUpdateStatusRequest {
  status: QuoteStatus
}

export interface QuoteFilters {
  status?: QuoteStatus
  client_id?: number
  skip?: number
  limit?: number
}

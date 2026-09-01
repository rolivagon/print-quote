import type { PrintType } from '@/types'

export const internalCostUnits = (targetType: 'paper' | 'finish', printType: PrintType) => {
  if (targetType === 'paper') return printType === 'plotter' ? ['sqm'] : ['sheet']
  return ['sheet']
}

export const defaultInternalCostUnit = (targetType: 'paper' | 'finish', printType: PrintType) =>
  targetType === 'paper' && printType === 'plotter' ? 'sqm' : 'sheet'

export const hasConfiguredCost = (value: string | number | null | undefined) =>
  value != null && value !== ''

export const createRequestVersion = () => {
  let version = 0
  return {
    next: () => ++version,
    isCurrent: (candidate: number) => candidate === version,
  }
}

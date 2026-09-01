import { describe, expect, it } from 'vitest'
import {
  createRequestVersion,
  defaultInternalCostUnit,
  hasConfiguredCost,
  internalCostUnits,
} from './internalCostRules'

describe('internal cost rules', () => {
  it('restricts paper units by technology', () => {
    expect(internalCostUnits('paper', 'digital')).toEqual(['sheet'])
    expect(internalCostUnits('paper', 'offset')).toEqual(['sheet'])
    expect(internalCostUnits('paper', 'plotter')).toEqual(['sqm'])
    expect(internalCostUnits('finish', 'plotter')).toEqual(['sheet'])
    expect(defaultInternalCostUnit('finish', 'plotter')).toBe('sheet')
  })

  it('keeps zero as a configured cost', () => {
    expect(hasConfiguredCost(0)).toBe(true)
    expect(hasConfiguredCost(null)).toBe(false)
  })

  it('ignores stale lifecycle requests after a target change', () => {
    const requests = createRequestVersion()
    const first = requests.next()
    const second = requests.next()

    expect(requests.isCurrent(first)).toBe(false)
    expect(requests.isCurrent(second)).toBe(true)
  })
})

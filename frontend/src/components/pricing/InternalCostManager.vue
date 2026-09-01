<template>
  <section
    class="mt-8 rounded-xl border border-amber-200 bg-amber-50/50 p-6 dark:border-amber-900 dark:bg-amber-500/5"
  >
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
      Costos internos de producción
    </h3>
    <p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
      Estos valores son administrativos y no cambian los precios de venta.
    </p>
    <div class="space-y-3">
      <div v-for="type in printTypes" :key="type" class="grid gap-3 md:grid-cols-4">
        <strong class="self-center capitalize">{{ type }}</strong>
        <select v-model="values[type].unit" class="rounded-lg border px-3 py-2 text-sm">
          <option v-for="unit in unitOptions(type)" :key="unit" :value="unit">{{ unit }}</option>
        </select>
        <input
          v-if="targetType === 'paper'"
          v-model="values[type].paper_cost"
          type="number"
          min="0"
          step="0.01"
          placeholder="Papel"
          class="rounded-lg border px-3 py-2 text-sm"
        />
        <input
          v-if="targetType === 'paper'"
          v-model="values[type].printing_cost"
          type="number"
          min="0"
          step="0.01"
          placeholder="Impresión"
          class="rounded-lg border px-3 py-2 text-sm"
        />
        <input
          v-else
          v-model="values[type].unit_cost"
          type="number"
          min="0"
          step="0.01"
          placeholder="Costo"
          class="rounded-lg border px-3 py-2 text-sm"
        />
      </div>
    </div>
    <button
      class="mt-4 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white"
      :disabled="saving"
      @click="save"
    >
      {{ saving ? 'Guardando…' : 'Guardar costos internos' }}
    </button>
    <p v-if="message" class="mt-3 text-sm">{{ message }}</p>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import type { FinishInternalCostInput, PaperInternalCostInput, PrintType } from '@/types'
import {
  createRequestVersion,
  defaultInternalCostUnit,
  hasConfiguredCost,
  internalCostUnits,
} from './internalCostRules'

type CostValue = Partial<PaperInternalCostInput & FinishInternalCostInput> & { unit: string }

const props = defineProps<{ targetType: 'paper' | 'finish'; targetId: number }>()
const { get, patch } = useApi()
const printTypes: PrintType[] = ['digital', 'offset', 'plotter']
const values = reactive<Record<PrintType, CostValue>>({
  digital: { unit: defaultInternalCostUnit(props.targetType, 'digital') },
  offset: { unit: defaultInternalCostUnit(props.targetType, 'offset') },
  plotter: { unit: defaultInternalCostUnit(props.targetType, 'plotter') },
})
const unitOptions = (type: PrintType) => internalCostUnits(props.targetType, type)
const saving = ref(false)
const message = ref('')
const requests = createRequestVersion()

const targetKey = () => `${props.targetType}:${props.targetId}`

const resetValues = () => {
  Object.assign(values, {
    digital: { unit: defaultInternalCostUnit(props.targetType, 'digital') },
    offset: { unit: defaultInternalCostUnit(props.targetType, 'offset') },
    plotter: { unit: defaultInternalCostUnit(props.targetType, 'plotter') },
  })
}

const load = async () => {
  const request = requests.next()
  resetValues()
  saving.value = false
  message.value = ''
  try {
    const resource = await get<{ internal_costs?: Array<CostValue & { print_type: PrintType }> }>(
      `/${props.targetType === 'paper' ? 'papers' : 'finishes'}/${props.targetId}`,
    )
    if (!requests.isCurrent(request)) return
    for (const cost of resource.internal_costs || []) values[cost.print_type] = { ...cost }
  } catch (error) {
    if (requests.isCurrent(request)) {
      message.value = error instanceof Error ? error.message : 'No se pudieron cargar los costos.'
    }
  }
}

const save = async () => {
  const savedTarget = targetKey()
  saving.value = true
  message.value = ''
  try {
    const internal_costs = printTypes
      .map((print_type) => ({ print_type, ...values[print_type] }))
      .filter((cost) =>
        props.targetType === 'paper'
          ? hasConfiguredCost(cost.paper_cost) || hasConfiguredCost(cost.printing_cost)
          : hasConfiguredCost(cost.unit_cost),
      )
    await patch(`/${props.targetType === 'paper' ? 'papers' : 'finishes'}/${props.targetId}`, {
      internal_costs,
    })
    if (savedTarget !== targetKey()) return
    message.value = 'Costos internos guardados.'
  } catch (error) {
    message.value = error instanceof Error ? error.message : 'No se pudieron guardar los costos.'
  } finally {
    if (savedTarget === targetKey()) saving.value = false
  }
}

watch(() => targetKey(), load, { immediate: true })
</script>

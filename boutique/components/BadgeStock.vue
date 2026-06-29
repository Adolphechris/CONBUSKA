<template>
  <span
    class="absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-medium"
    :class="badgeClass"
  >
    {{ message }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  stock: number
  seuil: number
}>()

const message = computed(() => {
  if (props.stock === 0) {
    return 'Rupture de stock'
  } else if (props.stock <= props.seuil) {
    return `Plus que ${props.stock} en stock`
  } else {
    return 'En stock'
  }
})

const badgeClass = computed(() => {
  if (props.stock === 0) {
    return 'bg-red-500 text-white'
  } else if (props.stock <= props.seuil) {
    return 'bg-orange-500 text-white'
  } else {
    return 'bg-green-500 text-white'
  }
})
</script>
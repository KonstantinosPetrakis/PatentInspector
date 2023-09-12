<script setup>
const props = defineProps({
    id: {
        required: true,
    },
});
</script>

<template>
    <div :id="id" class="accordion">
        <slot></slot>
    </div>
</template>

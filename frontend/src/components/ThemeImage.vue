<script setup>
import { ref, computed } from "vue";
import { getColorMode } from "../utils";

const props = defineProps({
    srcName: {
        type: String,
        required: true,
    },
    alt: {
        type: String,
        default: "",
    },
});

const colorMode = ref(getColorMode());

const src = computed(() => `/src/assets/images/${props.srcName}-${colorMode.value}.png`);

window.addEventListener(
    "themeChanged",
    () => (colorMode.value = getColorMode())
);
</script>

<template>
    <img :src="src" :alt="alt" class="img-fluid" />
</template>

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
    type: {
        type: String,
        default: "png",
    },
});

const colorMode = ref(getColorMode());

const src = computed(
    () =>
        new URL(
            `../assets/images/${props.srcName}-${colorMode.value}.${props.type}`,
            import.meta.url
        ).href
);

window.addEventListener(
    "themeChanged",
    () => (colorMode.value = getColorMode())
);
</script>

<template>
    <img :src="src" :alt="alt" class="img-fluid" />
</template>

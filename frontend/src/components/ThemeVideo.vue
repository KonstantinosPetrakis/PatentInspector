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

const src = computed(
    
    () => require(`../assets/videos/${props.srcName}-${colorMode.value}.webm`)
);

window.addEventListener(
    "themeChanged",
    () => (colorMode.value = getColorMode())
);
</script>

<template>
    <video :src="src" autoplay muted loop>
        <p v-if="alt">{{ alt }}</p>
    </video>
</template>

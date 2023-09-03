<script setup>
import { ref, watch, computed, onMounted } from "vue";

const color = ref(localStorage.getItem("color") || "light");
const icon = computed(() =>
    color.value === "light" ? "moon-fill" : "brightness-high-fill"
);

const setColor = (value) => {
    localStorage.setItem("color", value);
    document.querySelector("html").setAttribute("data-bs-theme", value);
};

const toggleColor = () =>
    (color.value = color.value === "light" ? "dark" : "light");

onMounted(() => setColor(color.value));
watch(color, setColor);

</script>

<template>
    <button class="btn no-effect-button" @click="toggleColor">
        <i :class="`bi bi-${icon}`"></i>
        <slot> </slot>
    </button>
</template>

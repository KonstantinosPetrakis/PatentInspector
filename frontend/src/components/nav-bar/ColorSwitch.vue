<script setup>
import { ref, watch, computed, onMounted } from "vue";
import { Popover } from "bootstrap";

const color = ref(localStorage.getItem("color") || "light");
const colorSwitch = ref(null);

const icon = computed(() =>
    color.value === "light" ? "moon-fill" : "brightness-high-fill"
);

const setColor = (value) => {
    localStorage.setItem("color", value);
    document.querySelector("html").setAttribute("data-bs-theme", value);
    window.dispatchEvent(new Event("themeChanged"));
};

const toggleColor = () =>
    (color.value = color.value === "light" ? "dark" : "light");

onMounted(() => {
    setColor(color.value);
    new Popover(colorSwitch.value, { trigger: "hover", placement: "bottom" });
});
watch(color, setColor);
</script>

<template>
    <button class="btn no-effect-button" @click="toggleColor">
        <i
            :class="`bi bi-${icon}`"
            ref="colorSwitch"
            data-bs-content="Change color scheme"
        ></i>
        <slot> </slot>
    </button>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

const movingContainerWrapper = ref(null);
const props = defineProps({
    alignment: {
        type: String,
        default: "left",
    },
    title: {
        type: String,
        default: "",
    },
});

const css = computed(() => {
    return {
        translateX: props.alignment == "left" ? "-90%" : "90%",
        align: props.alignment,
    };
});

const observer = new IntersectionObserver(
    (entries) => {
        if (entries[0].isIntersecting) entries[0].target.classList.add("seen");
    },
    { threshold: 0.3 }
);

onMounted(() =>
    // Wait for the element to be rendered before observing it
    setTimeout(() => observer.observe(movingContainerWrapper.value), 500)
);
onUnmounted(() => observer.disconnect());
</script>

<style>
.moving-container-wrapper .moving-container {
    opacity: 0;
    transform: translateX(v-bind("css.translateX"));
    float: v-bind("css.align");
}

.moving-container-wrapper.seen .moving-container {
    opacity: 1;
    transform: translateX(0);
    transition: opacity 0.5s ease-out, transform 0.5s ease-out;
}
</style>

<template>
    <div class="moving-container-wrapper" ref="movingContainerWrapper">
        <div class="moving-container col-lg-6 col-12">
            <h4 v-if="title" class="h4">{{ title }}</h4>
            <slot></slot>
        </div>
    </div>
</template>

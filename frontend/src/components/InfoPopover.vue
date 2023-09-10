<script setup>
import { onMounted, ref } from "vue";
import { Popover } from "bootstrap";

const props = defineProps(["message"]);
const popover = ref(null);

onMounted(
    () => new Popover(popover.value, { trigger: "hover", placement: "top" })
);
</script>

<style>
.bi-info-circle-fill:hover {
    cursor: pointer;
}
</style>

<template>
    <i
        ref="popover"
        class="ms-1 bi bi-info-circle-fill"
        :data-bs-content="message"
    ></i>
</template>

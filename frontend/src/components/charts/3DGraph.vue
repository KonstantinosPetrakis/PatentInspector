<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps(["data"]);
</script>

<template>
    {{ data }}
</template>
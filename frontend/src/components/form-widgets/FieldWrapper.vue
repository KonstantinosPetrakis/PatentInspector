<script setup>
import { ref } from "vue";

const props = defineProps({
    fieldLabel: {
        type: String,
        default: "",
    },
    fieldInfo: {
        type: String,
        default: "",
    },
});
</script>

<template>
    <div class="w-100 d-flex mt-3">
        <label>
            {{ fieldLabel }}
        </label>
        <div class="ms-auto" v-if="fieldInfo">
            <i class="bi bi-info-circle-fill"></i>
        </div>
    </div>

    <div class="mt-2"><slot></slot></div>
</template>

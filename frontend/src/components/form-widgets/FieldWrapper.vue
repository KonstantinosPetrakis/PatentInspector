<script setup>
import { onMounted } from 'vue';
import InfoPopover from '../InfoPopover.vue';

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
            <InfoPopover :message="fieldInfo" />
        </div>
    </div>

    <div class="mt-2"><slot></slot></div>
</template>

<script setup>
import { ref, watch } from "vue";
import FieldWrapper from "./FieldWrapper.vue";
import Slider from '@vueform/slider';

const props = defineProps(["minValue", "maxValue"]);
const emits = defineEmits(["update:minValue", "update:maxValue"]);

const value = ref([props.minValue, props.maxValue]);

watch(value, (newValue) => {
    emits("update:minValue", newValue[0]);
    emits("update:maxValue", newValue[1]);
});

// Set default values
value.value = [value.value[0] || 0, value.value[1] || 100];

</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <div class="mt-4 px-2">
            <Slider
            showTooltip="drag"
            v-model="value"
            v-bind="$attrs"
        />
        </div>
    </FieldWrapper>
</template>
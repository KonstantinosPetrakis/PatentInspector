<script setup>
import "@vueform/slider/themes/default.css";
import { ref, watch } from "vue";
import Slider from "@vueform/slider";
import FieldWrapper from "./FieldWrapper.vue";

const props = defineProps(["modelValue"]);
const emit = defineEmits(["update:modelValue"]);

// Defaults
const min = 0;
const max = 300;
const rangeValue = ref([min, max]);

watch(rangeValue, (value) => {
    if (value[0] == min && value[1] == max) emit("update:modelValue", null);
    else
        emit("update:modelValue", {
            lower: value[0] != min ? value[0] : null,
            upper: value[1] != max ? value[1] : null,
        });
});
</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <div class="mt-4 px-2">
            <Slider
                showTooltip="drag"
                v-model="rangeValue"
                v-bind="$attrs"
                :max="max"
            />
        </div>
    </FieldWrapper>
</template>

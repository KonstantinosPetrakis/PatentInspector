<script setup>
import "@vueform/slider/themes/default.css";
import { ref, watch } from "vue";
import Slider from "@vueform/slider";
import FieldWrapper from "./FieldWrapper.vue";

const props = defineProps(["modelValue"]);
const emit = defineEmits(["update:modelValue"]);

// Defaults
const rangeValue = ref([0, 100]);
emit("update:modelValue", { lower: 0, upper: 100 });

watch(rangeValue, (value) => {
    emit("update:modelValue", { lower: value[0], upper: value[1] });
});
</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <div class="mt-4 px-2">
            <Slider showTooltip="drag" v-model="rangeValue" v-bind="$attrs" />
        </div>
    </FieldWrapper>
</template>

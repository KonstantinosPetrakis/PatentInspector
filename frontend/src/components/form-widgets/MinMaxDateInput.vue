<script setup>
import { computed } from "vue";
import FieldWrapper from "./FieldWrapper.vue";

const props = defineProps(["modelValue"]);
const emit = defineEmits(["update:modelValue"]);

const value = computed({
    get: () => props.modelValue,
    set: (val) => emit("update:modelValue", val),
});

if (value.value == null) value.value = { lower: null, upper: null };
</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <div class="d-flex align-items-center">
            <div class="w-100">
                <input
                    type="date"
                    class="form-control"
                    :value="value?.lower"
                    @input="value = { ...value, lower: $event.target.value }"
                />
            </div>
            <div class="mx-2">-</div>
            <div class="w-100">
                <input
                    type="date"
                    class="form-control"
                    :value="value?.upper"
                    @input="value = { ...value, upper: $event.target.value }"
                />
            </div>
        </div>
    </FieldWrapper>
</template>

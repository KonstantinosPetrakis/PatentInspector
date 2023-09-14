<script setup>
import { computed } from "vue";
import FieldWrapper from "./FieldWrapper.vue";

const props = defineProps({
    modelValue: {
        required: true,
    },
    errors: {
        required: true,
    },
    fieldLabel: {
        type: String,
        required: true,
    },
    displayLabel: {
        type: Boolean,
        default: true,
    },
});
const emit = defineEmits(["update:modelValue", "update:errors"]);

const errors = computed({
    get: () => props.errors,
    set: (val) => emit("update:errors", val),
});

const value = computed({
    get: () => props.modelValue,
    set: (val) => {
        if (val.lower && val.upper && val.lower > val.upper)
            errors.value[props.fieldLabel] =
                "Lower date must be before upper date";
        else if (Object.hasOwn(errors.value, props.fieldLabel))
            delete errors.value[props.fieldLabel];
        emit("update:modelValue", val);
    },
});

const passedLabel = computed(() => props.displayLabel ? props.fieldLabel : "");

if (value.value == null) value.value = { lower: null, upper: null };
</script>

<template>
    <FieldWrapper v-bind="$attrs" :field-label="passedLabel">
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

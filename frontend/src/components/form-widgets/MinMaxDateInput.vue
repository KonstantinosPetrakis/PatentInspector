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
    get: () => {
        if (props.modelValue == null) return { lower: null, upper: null };
        return props.modelValue;
    },
    set: (val) => {
        if (val.lower && val.upper && val.lower > val.upper)
            errors.value[props.fieldLabel] =
                "Lower date must be before upper date";
        else if (Object.hasOwn(errors.value, props.fieldLabel))
            delete errors.value[props.fieldLabel];
        
        // Set empty dates to null so they're more concise.
        if (!val.lower) val.lower = null;
        if (!val.upper) val.upper = null;
        if (val.lower == null && val.upper == null) val = null;
        emit("update:modelValue", val);
    },
});

const passedLabel = computed(() => props.displayLabel ? props.fieldLabel : "");

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

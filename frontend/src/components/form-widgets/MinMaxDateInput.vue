<script setup>
import FieldWrapper from "./FieldWrapper.vue";

const props = defineProps(["min", "max"]);
const emit = defineEmits(["update:min"], ["update:max"]);
</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <div class="d-flex align-items-center">
            <div class="w-100">
                <input
                    type="date"
                    class="form-control"
                    :value="min"
                    @input="$emit('update:min', $event.target.value)"
                />
            </div>
            <div class="mx-2">-</div>
            <div class="w-100">
                <input
                    type="date"
                    class="form-control"
                    :value="max"
                    @input="$emit('update:max', $event.target.value)"
                />
            </div>
        </div>
    </FieldWrapper>
</template>

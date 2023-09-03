<script setup>
import MultiSelect from "vue-multiselect";
import FieldWrapper from "./FieldWrapper.vue";

</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <MultiSelect
            :allow-empty="true"
            v-bind="$attrs"
        >
        </MultiSelect>
    </FieldWrapper>
</template>

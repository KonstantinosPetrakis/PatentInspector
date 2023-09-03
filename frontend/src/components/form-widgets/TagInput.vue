<script setup>
import MultiSelect from "vue-multiselect";
import FieldWrapper from "./FieldWrapper.vue";

</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <MultiSelect
            :allow-empty="true"
            :multiple="true"
            :taggable="true"
            :showNoOptions="false"
            :close-on-select="false"
            placeholder="Add keywords"
            v-bind="$attrs"
        />
    </FieldWrapper>
</template>

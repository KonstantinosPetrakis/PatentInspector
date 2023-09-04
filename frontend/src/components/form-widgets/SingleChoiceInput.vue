<script setup>
import MultiSelect from "vue-multiselect";
import FieldWrapper from "./FieldWrapper.vue";
</script>

<template>
    <FieldWrapper v-bind="$attrs">
        <MultiSelect :allow-empty="true" v-bind="$attrs">
            <!-- This is required to pass down all slots -->
            <template v-for="(_, slot) of $slots" v-slot:[slot]="scope">
                <slot :name="slot" v-bind="scope"> </slot>
            </template>
        </MultiSelect>
    </FieldWrapper>
</template>

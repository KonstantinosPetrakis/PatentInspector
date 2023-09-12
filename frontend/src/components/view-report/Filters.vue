<script setup>
import { computed } from "vue";
import CopyTable from "../CopyTable.vue";

const props = defineProps(["filters"]);

const filtersAsTable = computed(() => {
    const table = [["Filter", "Value"]];
    for (const [key, value] of Object.entries(props.filters)) {
        table.push([key, value]);
    }
    return table;
});
</script>

<template>
    <CopyTable :data="filtersAsTable" />
</template>

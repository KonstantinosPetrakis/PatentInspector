<script setup>
import { computed } from "vue";
import TableLine from "../../charts/TableLine.vue";

const props = defineProps(["timeseries"]);

const timeSeries = computed(() => [
    {
        title: "Applications per year",
        data: props.timeseries.applications_per_year,
    },
    {
        title: "Granted patents per year",
        data: props.timeseries.granted_per_year,
    },
    {
        title: "Granted patents per type",
        data: props.timeseries.granted_per_type_year,
    },
    {
        title: "Granted patents per office",
        data: props.timeseries.granted_per_office_per_year,
    },
    {
        title: "PCT protected patents per year",
        data: props.timeseries.pct_protected_per_year,
    },
    {
        title: "Granted patents per CPC",
        data: props.timeseries.granted_per_cpc_year,
    },
    {
        title: "Citations made per year",
        data: props.timeseries.citations_made_per_year,
    },
    {
        title: "Citations received per year",
        data: props.timeseries.citations_received_per_year,
    },
]);
</script>

<template>
    <div class="row">
        <TableLine
            v-for="item in timeSeries"
            class="col-lg-6 col-12 m-0 p-0"
            :title="item.title"
            :data="item.data"
        />
    </div>
</template>

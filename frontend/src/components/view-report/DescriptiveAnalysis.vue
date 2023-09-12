<script setup>
import CopyTable from "../CopyTable.vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";
import TimeSeries from "./descriptive-analysis/TimeSeries.vue";
import Entity from "./descriptive-analysis/Entity.vue";

const props = defineProps(["results"]);
</script>

<template>
    <Tabs
        :links="[
            { title: 'Basic statistical measures' },
            { title: 'Variables over time' },
            { title: 'Information for each entity' },
        ]"
    >
        <TabItem>
            <CopyTable :data="results.statistics" />
        </TabItem>
        <TabItem>
            <TimeSeries :timeseries="results.timeseries" />
        </TabItem>
        <TabItem>
            <Entity :entity="results.entity" />
        </TabItem>
    </Tabs>
</template>

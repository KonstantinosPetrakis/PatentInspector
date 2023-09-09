<script setup>
import { computed } from "vue";

import { Line } from "vue-chartjs";
import CopyTable from "../CopyTable.vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";
import { colors } from "../../utils";

const props = defineProps(["title", "data"]);

// The label and value column indices of the data
const labelIndex = computed(() => props.data[0].indexOf("Year"));
const valueIndex = computed(() => props.data[0].indexOf("Count"));

// Whether we are showing a single line or multiple lines
const singleLine = computed(() => props.data[0].length === 2);

// The index of the column we are grouping by for multiple lines
const groupingIndex = computed(() => {
    if (singleLine.value) return null;
    for (let [i, value] of props.data[0].entries()) {
        if (!["Year", "Count"].includes(value)) return i;
    }
});

// The labels for the x-axis
const labels = computed(() => props.data.slice(1).map((row) => row[labelIndex.value]));

// The data reformed as array of objects with x and y properties put into a list of datasets with labels.
const datasets = computed(() => {
    if (singleLine.value) {
        const data = [];
        for (let row of props.data.slice(1)) {
            data.push({
                x: row[labelIndex.value],
                y: row[valueIndex.value],
            });
        }
        return [{ label: null, data }];
    } else {
        const data = {};
        for (let row of props.data.slice(1)) {
            const label = row[groupingIndex.value];
            if (!data[label]) data[label] = [];
            data[label].push({
                x: row[labelIndex.value],
                y: row[valueIndex.value],
            });
        }
        return Object.entries(data).map(([label, data]) => {
            return { label, data };
        });
    }
});

const chartOptions = computed(() => {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            legend: {
                display: !singleLine.value,
            },
            title: {
                display: true,
                text: props.title,
            },
        },
    };
});

const chartData = computed(() => {
    return {
        labels: labels.value,
        datasets: datasets.value.map((dataset, i) => {
            return {
                label: dataset.label,
                data: dataset.data,
                borderColor: colors[i],
                backgroundColor: colors[i],
            };
        }),
    };
});
</script>

<template>
    <div>
        <Tabs :links="[{ title: 'Chart' }, { title: 'Table' }]">
            <TabItem>
                <Line :options="chartOptions" :data="chartData" />
            </TabItem>
            <TabItem>
                <CopyTable :data="data" />
            </TabItem>
        </Tabs>
    </div>
</template>

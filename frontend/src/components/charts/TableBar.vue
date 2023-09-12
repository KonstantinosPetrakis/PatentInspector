<script setup>
import { computed } from "vue";

import { Bar } from "vue-chartjs";
import CopyTable from "../CopyTable.vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";
import { colors } from "../../utils";

const props = defineProps(["title", "data"]);

const chartOptions = computed(() => {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            legend: {
                display: false,
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
        labels: props.data
            .slice(1)
            .map((val) =>
                val[0].length > 30 ? val[0].slice(0, 30) + "..." : val[0]
            ),
        datasets: [
            {
                data: props.data.slice(1).map((val) => val[1]),
                backgroundColor: colors[0],
                borderColor: "black",
                borderWidth: 1,
                indexAxis: "y",
                maxBarThickness: 40,
            },
        ],
    };
});
</script>

<template>
    <div>
        <Tabs :links="[{ title: 'Chart' }, { title: 'Table' }]">
            <TabItem>
                <Bar :options="chartOptions" :data="chartData" />
            </TabItem>
            <TabItem>
                <CopyTable :data="data" />
            </TabItem>
        </Tabs>
    </div>
</template>

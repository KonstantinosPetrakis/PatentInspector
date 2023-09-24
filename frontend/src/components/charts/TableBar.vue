<script setup>
import { computed, ref } from "vue";

import { Bar } from "vue-chartjs";
import CopyTable from "../CopyTable.vue";
import InfoPopover from "../InfoPopover.vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";
import { colors } from "../../utils";

const props = defineProps(["title", "data", "info"]);
const emit = defineEmits(["click"]);

const chart = ref(null);

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
        onClick: (evt) => {
            const res = chart.value.chart.getElementsAtEventForMode(
                evt,
                "nearest",
                { intersect: true },
                true
            );
            // If didn't click on a bar, `res` will be an empty array
            if (res.length === 0) return;

            const index = res[0].index;
            const label = props.data[index + 1][0];
            emit("click", label);
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
    <div class="d-flex flex-column">
        <div v-if="info" class="ms-auto my-0 py-0">
            <InfoPopover :message="info" />
        </div>
        <Tabs :links="[{ title: 'Chart' }, { title: 'Table' }]">
            <TabItem>
                <Bar :options="chartOptions" :data="chartData" ref="chart" />
            </TabItem>
            <TabItem>
                <CopyTable :data="data" />
            </TabItem>
        </Tabs>
    </div>
</template>

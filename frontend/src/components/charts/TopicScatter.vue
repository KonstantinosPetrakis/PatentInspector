<script setup>
import { computed, onMounted } from "vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";
import CopyTable from "../CopyTable.vue";
import { Scatter } from "vue-chartjs";
import { colors } from "../../utils";

const props = defineProps(["topics"]);

const averageShare = computed(() => 1 / props.topics.length);
const maxShare = computed(() => Math.max(...props.topics.map((t) => t.ratio)));
const minShare = computed(() => Math.min(...props.topics.map((t) => t.ratio)));
const maxDiffFromAverageShare = computed(() =>
    Math.max(
        Math.abs(minShare.value - averageShare.value),
        Math.abs(maxShare.value - averageShare.value)
    )
);
// x = averageShare centered
const shareAxisMin = computed(
    () => averageShare.value - maxDiffFromAverageShare.value
);
const shareAxisMax = computed(
    () => averageShare.value + maxDiffFromAverageShare.value
);

const maxCagr = computed(() => Math.max(...props.topics.map((t) => t.cagr)));
const minCagr = computed(() => Math.min(...props.topics.map((t) => t.cagr)));
const maxAbsCagr = computed(() =>
    Math.max(Math.abs(minCagr.value), Math.abs(maxCagr.value))
);
// y = 0 centered
const cagrAxisMin = computed(() => -maxAbsCagr.value);
const cagrAxisMax = computed(() => maxAbsCagr.value);

const labels = computed(() => topics.value.map((t) => t.label));

const topics = computed(() => {
    for (const [i, topic] of props.topics.entries()) {
        topic.label = `Topic ${i + 1}: ${topic.words.join(", ")}`;
        if (topic.ratio < averageShare.value)
            topic.class = topic.cagr > 0 ? "emerging" : "declining";
        else topic.class = topic.cagr > 0 ? "dominant" : "saturated";
    }
    return props.topics;
});

const topicsTable = computed(() => {
    const results = [["Topic", "Share", "CAGR", "Class"]];
    for (let topic of topics.value)
        results.push([topic.label, topic.ratio, topic.cagr, topic.class]);
    return results;
});

const chartData = computed(() => {
    return {
        labels: labels.value,
        datasets: [
            {
                data: topics.value,
                backgroundColor: colors,
            },
        ],
    };
});

const chartOptions = computed(() => {
    return {
        plugins: {
            legend: {
                display: false,
            },
        },
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                title: {
                    display: true,
                    text: "Share",
                },

                min: shareAxisMin.value,
                max: shareAxisMax.value,
            },
            y: {
                title: {
                    display: true,
                    text: "CAGR",
                },
                min: cagrAxisMin.value,
                max: cagrAxisMax.value,
            },
        },
        layout: {
            padding: 5,
        },
        parsing: {
            xAxisKey: "ratio",
            yAxisKey: "cagr",
        },
        clip: false,
        annotations: {
            emerging: {
                type: "box",
                xMax: averageShare.value,
                yMin: 0,
                backgroundColor: "rgba(250, 250, 3, 0.25)",
                label: {
                    drawTime: "afterDraw",
                    display: true,
                    content: "Emerging Topics",
                    position: {
                        x: "center",
                        y: "start",
                    },
                },
            },
            dominant: {
                type: "box",
                xMin: averageShare.value,
                yMin: 0,
                backgroundColor: "rgba(250, 106, 3, 0.25)",
                label: {
                    drawTime: "afterDraw",
                    display: true,
                    content: "Dominant Topics",
                    position: {
                        x: "center",
                        y: "start",
                    },
                },
            },
            declining: {
                type: "box",
                xMax: averageShare.value,
                yMax: 0,
                backgroundColor: "rgba(52, 58, 59, 0.25)",
                label: {
                    drawTime: "afterDraw",
                    display: true,
                    content: "Declining Topics",
                    position: {
                        x: "center",
                        y: "start",
                    },
                },
            },
            saturated: {
                type: "box",
                xMin: averageShare.value,
                yMax: 0,
                backgroundColor: "rgba(130, 157, 129, 0.25)",
                label: {
                    drawTime: "afterDraw",
                    display: true,
                    content: "Saturated Topics",
                    position: {
                        x: "center",
                        y: "start",
                    },
                },
            },
        },
        animation: false
    };
});
</script>

<template>
    <div class="row">
        <div class="col-lg-6 col-12">
            <Tabs :links="[{ title: 'Chart' }, { title: 'Table' }]">
                <TabItem>
                    <Scatter :options="chartOptions" :data="chartData" />
                </TabItem>
                <TabItem>
                    <CopyTable :data="topicsTable" />
                </TabItem>
            </Tabs>
        </div>
    </div>
</template>

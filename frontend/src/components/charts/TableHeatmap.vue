<script setup>
import "leaflet/dist/leaflet.css";
import "leaflet/dist/leaflet.js";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw/dist/leaflet.draw.js";
import HeatmapOverlay from "leaflet-heatmap/leaflet-heatmap.js"

import { onMounted, computed } from "vue";
import CopyTable from "../CopyTable.vue";
import Tabs from "../Tabs.vue";
import TabItem from "../TabItem.vue";

const props = defineProps(["title", "data"]);

const id = `heatmap-${Number.parseInt(Math.random() * 10000000)}`;
const max = computed(() => Math.max(...props.data.slice(1).map((d) => d[3])));

const transformedData = computed(() =>
    props.data.slice(1).map((d) => {
        return { lat: d[0], lng: d[1], count: d[3] };
    })
);

onMounted(() => {
    const map = L.map(id).setView([30, -20], 2.4);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    var heatmapLayer = new HeatmapOverlay({
        radius: 5,
        scaleRadius: true,
        useLocalExtrema: false,
        latField: "lat",
        lngField: "lng",
        valueField: "count",
    });

    heatmapLayer.addTo(map);

    heatmapLayer.setData({
        max: max.value,
        data: transformedData.value,
    });

    // Invalidate the size of the map every time intersection observer fires
    new IntersectionObserver(() => map.invalidateSize()).observe(
        document.getElementById(id)
    );
});
</script>

<template>
    <div>
        <Tabs :links="[{ title: 'Chart' }, { title: 'Table' }]">
            <TabItem>
                <div :id="id"></div>
            </TabItem>
            <TabItem>
                <CopyTable :data="data" />
            </TabItem>
        </Tabs>
    </div>
</template>

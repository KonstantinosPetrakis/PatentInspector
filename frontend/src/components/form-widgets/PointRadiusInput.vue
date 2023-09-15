<script setup>
import FieldWrapper from "./FieldWrapper.vue";
import { onMounted, computed, onUnmounted } from "vue";

const props = defineProps(["modelValue", "fieldLabel"]);
const emit = defineEmits(["update:modelValue"]);

const value = computed({
    get: () => props.modelValue,
    set: (val) => emit("update:modelValue", val),
});

const id = props.fieldLabel.replace(/\s+/g, "-").toLowerCase();
let observer;

onMounted(() => {
    const map = L.map(id).setView([30, -20], 2.2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // FeatureGroup is to store editable layers
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Add controls
    var drawControl = new L.Control.Draw({
        draw: {
            polygon: false,
            marker: false,
            polyline: false,
            rectangle: false,
            circlemarker: false,
        },
        edit: {
            featureGroup: drawnItems,
        },
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (e) => {
        const circle = e.layer;
        const circleCoords = circle.getLatLng();
        const circleRadius = circle.getRadius();
        // clear old circle
        drawnItems.clearLayers();
        // Add new circle
        drawnItems.addLayer(circle);
        value.value = {
            lat: circleCoords.lat,
            lng: circleCoords.lng,
            radius: circleRadius,
        };
    });

    // When a circle is deleted clear the hidden input field
    map.on(L.Draw.Event.DELETED, () => (value.value = null));

    // Invalidate the size of the map every time intersection observer fires
    observer = new IntersectionObserver(() => map.invalidateSize()).observe(
        document.querySelector(`#${id}`)
    );
});

onUnmounted(() => {
    if (observer) observer.disconnect();
});
</script>

<template>
    <FieldWrapper v-bind="$attrs" :field-label="fieldLabel">
        <div :id="id"></div>
    </FieldWrapper>
</template>

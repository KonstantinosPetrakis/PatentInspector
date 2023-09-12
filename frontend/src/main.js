import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap";
import "bootstrap-icons/font/bootstrap-icons.css";
import "leaflet/dist/leaflet.css";
import "leaflet/dist/leaflet.js";
import "heatmap.js";
import HeatmapOverlay from "leaflet-heatmap/leaflet-heatmap.js";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw/dist/leaflet.draw.js";
import annotationPlugin from 'chartjs-plugin-annotation';
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables);
Chart.register(annotationPlugin);

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import config from "./config.json";

const app = createApp(App);

app.provide("HeatmapOverlay", HeatmapOverlay);

app.use(router);
app.mount("#app");

export const apiUrl = config.API_URL;

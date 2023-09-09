import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap";
import "bootstrap-icons/font/bootstrap-icons.css";

import { Chart, registerables } from 'chart.js'
Chart.register(...registerables);

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import config from "./config.json";

const app = createApp(App);
app.use(router);
app.mount("#app");

export const apiUrl = config.API_URL;

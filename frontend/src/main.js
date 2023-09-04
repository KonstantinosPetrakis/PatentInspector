import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap";
import "bootstrap-icons/font/bootstrap-icons.css";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import config from "./config.json";

const app = createApp(App);

export const apiUrl = config.API_URL;

app.provide("apiUrl", apiUrl);

app.use(router);

app.mount("#app");

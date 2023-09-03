import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap";
import "bootstrap-icons/font/bootstrap-icons.css";
import "vue-multiselect/dist/vue-multiselect.css";
import "@vueform/slider/themes/default.css";

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

const app = createApp(App);

app.provide("apiUrl", "http://localhost:8000/api");

app.use(router);

app.mount("#app");

<script setup>
import { RouterView } from "vue-router";
import Navbar from "./components/nav-bar/Navbar.vue";
import FooterVue from "./components/Footer.vue";
</script>

<template>
    <header>
        <Navbar />
    </header>
    <main>
        <RouterView />
    </main>
    <footer class="mt-auto">
        <FooterVue />
    </footer>
</template>

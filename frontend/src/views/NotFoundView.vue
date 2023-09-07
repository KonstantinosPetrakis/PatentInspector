<script setup>
import { RouterLink } from "vue-router";
</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentAnalyzer</h1>
        <h3 class="h3 text-center">The requested resource was not found!</h3>
        <div class="text-center">
            <RouterLink class="btn btn-secondary" :to="{ name: 'home' }">
                Go to home page
            </RouterLink>
        </div>
    </div>
</template>

<script setup>
import { isLoggedIn } from "../utils";
import { RouterLink } from "vue-router";

const loggedIn = isLoggedIn();
const email = localStorage.getItem("email");
</script>

<template>
    <div class="container">
        <template v-if="loggedIn">
            <h1 class="h1 text-center">PatentAnalyzer</h1>
            <p class="text-center h5">
                Welcome back {{ email }}, what would you like to do?
            </p>
            <div class="d-flex justify-content-center mt-4">
                <RouterLink class="btn btn-outline-secondary mx-2" :to="{'name': 'createReport'}">
                    Create new report
                </RouterLink>
                <RouterLink class="btn btn-outline-secondary mx-2" :to="{'name': 'listReports'}">
                    See all reports
                </RouterLink>
            </div>
        </template>

        <template v-else> You're not logged in! </template>
    </div>
</template>

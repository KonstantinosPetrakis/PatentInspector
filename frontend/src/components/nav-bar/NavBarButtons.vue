<script setup>
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";
import { isLoggedIn, logOut } from "../../utils";
import ColorSwitch from "./ColorSwitch.vue";

const props = defineProps({
    useSeparator: {
        type: Boolean,
        default: false,
    },
    useText: {
        type: Boolean,
        default: false,
    },
});

const cssVars = computed(() => {
    return {
        "--border-left": props.useSeparator ? "2px solid" : "none",
        "--margin-right": props.useSeparator ? "10px" : "0",
    };
});

const loggedIn = ref(isLoggedIn());
window.addEventListener("logIn", () => (loggedIn.value = true));
window.addEventListener("logOut", () => (loggedIn.value = false));
</script>

<style>
.color-switch::before {
    content: "";
    margin-right: var(--margin-right);
    border-left: var(--border-left);
}
</style>

<template>
    <div
        class="d-flex justify-content-center align-items-start"
        :style="cssVars"
    >
        <template v-if="loggedIn">
            <RouterLink
                class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                :to="{ name: 'createReport' }"
            >
                <i class="bi bi-file-earmark-plus-fill"></i>
                <template v-if="useText"> Create report </template>
            </RouterLink>

            <RouterLink
                class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                :to="{ name: 'listReports' }"
            >
                <i class="bi bi-archive-fill"></i>
                <template v-if="useText"> View reports </template>
            </RouterLink>

            <RouterLink
                class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                :to="{ name: 'settings' }"
            >
                <i class="bi bi-gear-fill"></i>
                <template v-if="useText"> Settings </template>
            </RouterLink>

            <button
                class="btn fs-5 mx-0 mx-md-2 p-0 text-center"
                @click="logOut"
            >
                <i class="bi bi-door-closed-fill w-100"></i>
                <template v-if="useText"> Logout </template>
            </button>
        </template>

        <template v-else>
            <RouterLink
                class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                :to="{ name: 'login' }"
            >
                <i class="bi bi-door-open-fill"></i>
                <template v-if="useText"> Login </template>
            </RouterLink>

            <RouterLink
                class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                :to="{ name: 'register' }"
            >
                <i class="bi bi-pen-fill"></i>
                <template v-if="useText"> Register </template>
            </RouterLink>
        </template>

        <color-switch
            class="color-switch fs-5 mx-0 mx-md-2 p-0 text-start d-inline"
        >
            <span v-if="useText" class="fs-5"> Color</span>
        </color-switch>
    </div>
</template>

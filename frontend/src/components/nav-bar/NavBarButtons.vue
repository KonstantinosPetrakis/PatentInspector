<script setup>
import { computed, ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { isLoggedIn, logOut } from "../../utils";
import { Popover } from "bootstrap";
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
const createReport = ref(null);
const viewReports = ref(null);
const settings = ref(null);
const logout = ref(null);
const register = ref(null);
const login = ref(null);

window.addEventListener("logIn", () => (loggedIn.value = true));
window.addEventListener("logOut", () => (loggedIn.value = false));

onMounted(() => {
    for (let pop of [
        createReport,
        viewReports,
        settings,
        logout,
        register,
        login,
    ])
        new Popover(pop.value, { trigger: "hover", placement: "bottom" });
});
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
        <div v-show="loggedIn">
            <div class="d-flex flex-md-row flex-column">
                <RouterLink
                    class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                    :to="{ name: 'createReport' }"
                >
                    <i
                        class="bi bi-file-earmark-plus-fill"
                        ref="createReport"
                        data-bs-content="Create a new report"
                    ></i>
                    <template v-if="useText"> Create report </template>
                </RouterLink>

                <RouterLink
                    class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                    :to="{ name: 'listReports' }"
                >
                    <i
                        class="bi bi-archive-fill"
                        ref="viewReports"
                        data-bs-content="View reports"
                    ></i>
                    <template v-if="useText"> View reports </template>
                </RouterLink>

                <RouterLink
                    class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                    :to="{ name: 'settings' }"
                >
                    <i
                        class="bi bi-gear-fill"
                        ref="settings"
                        data-bs-content="Settings"
                    ></i>
                    <template v-if="useText"> Settings </template>
                </RouterLink>

                <button
                    class="btn fs-5 mx-0 mx-md-2 p-0 text-start"
                    @click="logOut"
                >
                    <i
                        class="bi bi-door-closed-fill m-0 p-0"
                        ref="logout"
                        data-bs-content="Logout"
                    ></i>
                    <template v-if="useText"> Logout </template>
                </button>
            </div>
        </div>

        <div v-show="!loggedIn">
            <div class="d-flex flex-md-row flex-column">
                <RouterLink
                    class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                    :to="{ name: 'login' }"
                >
                    <i
                        class="bi bi-door-open-fill"
                        ref="login"
                        data-bs-content="Login"
                    ></i>
                    <template v-if="useText"> Login </template>
                </RouterLink>

                <RouterLink
                    class="text-decoration-none text-body fs-5 mx-0 mx-md-2"
                    :to="{ name: 'register' }"
                >
                    <i
                        class="bi bi-pen-fill"
                        ref="register"
                        data-bs-content="Register"
                    ></i>
                    <template v-if="useText"> Register </template>
                </RouterLink>
            </div>
        </div>

        <color-switch
            class="color-switch fs-5 mx-0 mx-md-2 p-0 text-start d-inline"
        >
            <span v-if="useText" class="fs-5"> Color</span>
        </color-switch>
    </div>
</template>

<script setup>
import { watch } from "vue";
import NavBarButtons from "./NavBarButtons.vue";
import { useRoute } from "vue-router";

const route = useRoute();
watch(
    () => route.name,
    () => document.getElementById("offcanvas-close").click()
);
</script>

<template>
    <nav class="d-flex align-items-center px-2 bg-secondary-subtle">
        <div>
            <h1 class="h2">
                <RouterLink
                    class="text-decoration-none text-body"
                    :to="{ name: 'home' }"
                >
                    PatentInspector
                </RouterLink>
            </h1>
            <p>A tool for easy and open-source patent analysis.</p>
        </div>

        <div class="ms-auto desktop-buttons d-none d-md-block">
            <nav-bar-buttons :use-separator="true"> </nav-bar-buttons>
        </div>

        <div class="ms-auto mobile-buttons d-block d-md-none">
            <button
                class="btn"
                data-bs-toggle="offcanvas"
                href="#offcanvas-buttons"
            >
                <i class="bi bi-list fs-1"></i>
            </button>
            <div
                class="offcanvas offcanvas-start"
                tabindex="-1"
                id="offcanvas-buttons"
            >
                <div class="offcanvas-header">
                    <h5 class="offcanvas-title">Menu</h5>
                    <button
                        id="offcanvas-close"
                        type="button"
                        class="btn-close"
                        data-bs-dismiss="offcanvas"
                        aria-label="Close"
                    ></button>
                </div>
                <div class="offcanvas-body">
                    <nav-bar-buttons
                        :use-text="true"
                        class="d-flex flex-column align-items-start"
                    >
                    </nav-bar-buttons>
                </div>
            </div>
        </div>
    </nav>
</template>

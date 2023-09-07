<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";

const props = defineProps(["page", "totalItems", "itemsPerPage", "urlName"]);

const page = computed(() => +props.page || 1);

const totalItems = computed(() => +props.totalItems || 0);

const totalPages = computed(() =>
    Math.ceil(totalItems.value / props.itemsPerPage)
);
const hasNext = computed(() => page.value < totalPages.value);

const hasPrevious = computed(() => page.value > 1);

const pagesBefore = computed(() => {
    const pages = [];
    for (let i = page.value - 1; i > page.value - 3 && i > 0; i--)
        pages.push(i);

    pages.sort();
    return pages;
});

const pagesAfter = computed(() => {
    const pages = [];
    for (
        let i = page.value + 1;
        i < page.value + 3 && i <= totalPages.value;
        i++
    )
        pages.push(i);

    return pages;
});
</script>

<template>
    <nav class="d-flex align-items-center my-2">
        <ul class="pagination m-0">
            <li :class="`page-item ${hasPrevious ? '' : 'disabled'}`">
                <RouterLink
                    class="page-link"
                    :to="{ name: urlName, params: { page: page - 1 } }"
                >
                    Previous
                </RouterLink>
            </li>
            <li class="page-item" v-for="pageBefore of pagesBefore">
                <RouterLink
                    class="page-link"
                    :to="{ name: urlName, params: { page: pageBefore } }"
                >
                    {{ pageBefore }}
                </RouterLink>
            </li>
            <li class="page-item active">
                <RouterLink class="page-link" to="#">
                    {{ page }}
                </RouterLink>
            </li>
            <li class="page-item" v-for="pageAfter of pagesAfter">
                <RouterLink
                    class="page-link"
                    :to="{ name: urlName, params: { page: pageAfter } }"
                >
                    {{ pageAfter }}
                </RouterLink>
            </li>
            <li :class="`page-item ${hasNext ? '' : 'disabled'}`">
                <RouterLink
                    class="page-link"
                    :to="{ name: urlName, params: { page: page + 1 } }"
                >
                    Next
                </RouterLink>
            </li>
        </ul>
        <div class="ms-2">
            Showing {{ totalItems }} results in {{ totalPages }} pages
        </div>
    </nav>
    <div></div>
</template>

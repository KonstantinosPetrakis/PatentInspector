<script setup>
import { onMounted, watch, ref } from "vue";
import { authFetch } from "../../utils";
import CopyTable from "../CopyTable.vue";
import Pagination from "../Pagination.vue";

const patentsPerPage = 10;
const props = defineProps(["id", "page"]);
const patents = ref();
const loading = ref(true);

const getPatents = async () => {
    loading.value = true;
    const response = await authFetch(
        `/report/${props.id}/get_patents?page=${props.page}&page_size=${patentsPerPage}`
    );
    if (!response.ok) router.replace({ name: "notFound" });
    const responseData = await response.json();
    patents.value = responseData;
    loading.value = false;
};

const downloadExcel = async () => {
    const response = await authFetch(
        `/report/${props.id}/download_patents_excel`
    );
    const data = await response.blob();
    const file = window.URL.createObjectURL(data);
    window.location.assign(file);
};

watch(() => props.page, getPatents);

onMounted(getPatents);
</script>

<template>
    <div>
        <div v-if="loading">
            <p class="fs-5">Patents are getting loaded...</p>
            <div class="spinner-border"></div>
        </div>
        <div v-else>
            <div class="d-flex align-items-center">
                <button class="btn btn-secondary m-1" @click="downloadExcel">
                    Download Excel
                </button>
                <p class="ms-1 mb-0">
                    The excel file contains more information that table below.
                </p>
            </div>
            <CopyTable :data="patents.results" />
            <Pagination
                :page="page"
                :total-items="patents.count"
                :items-per-page="patentsPerPage"
                urlName="report"
                :use-query="true"
            />
        </div>
    </div>
</template>

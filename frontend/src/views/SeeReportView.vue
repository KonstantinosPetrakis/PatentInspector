<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import {
    authFetch,
    reportToSubmittedFilters,
    dateTimeToString,
} from "../utils";
import CopyTable from "../components/CopyTable.vue";

const router = useRouter();
const props = defineProps(["id"]);
const data = ref();

const filtersAsTable = computed(() => {
    if (!data.value) return [null, null];
    
    const table = [["Filter", "Value"]];
    for (const [key, value] of Object.entries(data.value.filters)) {
        table.push([key, value]);
    }
    return table;
});

const getData = async () => {
    const response = await authFetch(`/report/${props.id}`);
    if (!response.ok) router.replace({ name: "notFound" });

    const responseData = await response.json();
    const dataCopy = JSON.parse(JSON.stringify(responseData));
    responseData.filters = reportToSubmittedFilters(dataCopy);
    data.value = responseData;
};

onMounted(getData);
</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentAnalyzer</h1>
        <h4 class="h4 text-center">Report #{{ data?.id }}</h4>

        <div class="text-center">
            <span class="badge text-bg-secondary fs-6 m-2">
                Created: {{ dateTimeToString(data?.datetimeCreated) }}
            </span>
            <span class="badge text-bg-secondary fs-6 m-2">
                Analysis Started:
                {{ dateTimeToString(data?.datetimeAnalysisStarted) }}
            </span>
            <span class="badge text-bg-secondary fs-6 m-2">
                Analysis Ended:
                {{ dateTimeToString(data?.datetimeAnalysisEnded) }}
            </span>
        </div>
        <div>
            <!-- Must add in-page tabs here -->
            <CopyTable :data="filtersAsTable" />
        </div>
    </div>
</template>

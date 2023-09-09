<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import {
    authFetch,
    reportToSubmittedFilters,
    dateTimeToString,
} from "../utils";
import CopyTable from "../components/CopyTable.vue";
import Tabs from "../components/Tabs.vue";
import TabItem from "../components/TabItem.vue";
import TableLine from "../components/charts/TableLine.vue";
import TableBar from "../components/charts/TableBar.vue";
import TableHeatmap from "../components/charts/TableHeatmap.vue";

const router = useRouter();
const props = defineProps(["id"]);
const data = ref();
const loading = ref(true);

const filtersAsTable = computed(() => {
    if (!data.value) return [null, null];

    const table = [["Filter", "Value"]];
    for (const [key, value] of Object.entries(data.value.filters)) {
        table.push([key, value]);
    }
    return table;
});

const patentCount = computed(() => {
    if (!data.value || !data.value.results) return "N/A";
    return data.value.results.patentsCount;
});

const getData = async () => {
    const response = await authFetch(`/report/${props.id}`);
    if (!response.ok) router.replace({ name: "notFound" });

    const responseData = await response.json();
    const dataCopy = JSON.parse(JSON.stringify(responseData));
    responseData.filters = reportToSubmittedFilters(dataCopy);
    data.value = responseData;
    loading.value = false;
};

const timeSeries = computed(() => {
    if (!data.value || !data.value.results) return [];
    return [
        {
            title: "Applications per year",
            data: data.value.results.timeseries.applicationsPerYear,
        },
        {
            title: "Granted patents per year",
            data: data.value.results.timeseries.grantedPerYear,
        },
        {
            title: "Granted patents per type",
            data: data.value.results.timeseries.grantedPerTypeYear,
        },
        {
            title: "Granted patents per office",
            data: data.value.results.timeseries.grantedPerOfficePerYear,
        },
        {
            title: "PCT protected patents per year",
            data: data.value.results.timeseries.pctProtectedPerYear,
        },
        {
            title: "Granted patents per CPC",
            data: data.value.results.timeseries.grantedPerCPCYear,
        },
        {
            title: "Citations made per year",
            data: data.value.results.timeseries.citationsMadePerYear,
        },
        {
            title: "Citations received per year",
            data: data.value.results.timeseries.citationsReceivedPerYear,
        },
    ];
});

const entity = computed(() => {
    if (!data.value || !data.value.results) return [];
    return {
        patent: [
            {
                title: "PCT Distribution",
                data: data.value.results.entity.patent.pct,
            },
            {
                title: "Type Distribution",
                data: data.value.results.entity.patent.type,
            },
            {
                title: "Patent Office Distribution",
                data: data.value.results.entity.patent.office,
            },
        ],
        cpc: [
            {
                title: "CPC Section Distribution",
                data: data.value.results.entity.cpc.section,
            },
            {
                title: "Top 5 CPC Classes",
                data: data.value.results.entity.cpc.top5Classes,
            },
            {
                title: "Top 5 CPC Subclasses",
                data: data.value.results.entity.cpc.top5Subclasses,
            },
            {
                title: "Top 5 CPC groups",
                data: data.value.results.entity.cpc.top5Groups,
            },
        ],
    };
});

onMounted(getData);
</script>

<template>
    <div class="container">
        <div v-if="loading">
            <div class="text-center mt-5">
                <h1 class="h1">Loading Report...</h1>
                <p class="fs-5">Please standby.</p>
                <div class="spinner-border"></div>
            </div>
        </div>
        <div v-else-if="!data || !data?.results">
            <h1 class="h1 text-center">PatentAnalyzer</h1>
            <h4 class="h4 text-center">Report #{{ data?.id }}</h4>
            <div class="text-center">
                {{ data }}
                The report hasn't been generated yet. Please check back later.
            </div>
        </div>
        <div v-else-if="data.results.error">
            <h1 class="h1 text-center">PatentAnalyzer</h1>
            <h4 class="h4 text-center">Report #{{ data?.id }}</h4>
            <div class="alert alert-danger">
                <h4 class="alert-heading">
                    An error occurred while processing the report.
                </h4>
                <p>
                    {{ data.results.error }}
                </p>
            </div>
        </div>
        <div v-else>
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
                <span class="badge text-bg-secondary fs-6 m-2">
                    Patents Analyzed:
                    {{ patentCount }}
                </span>
            </div>
            <div>
                <Tabs
                    :links="[
                        {
                            title: 'Descriptive Analysis',
                            info: 'How can the data be profiled?',
                        },
                        {
                            title: 'Thematic Analysis',
                            info: 'What are the primary topics of the data?',
                        },
                        {
                            title: 'Network Analysis',
                            info: 'What are the primary interconnections between the data?',
                        },
                        {
                            title: 'Patents',
                            info: 'View or download the filtered patents.',
                        },
                        {
                            title: 'Filters',
                            info: 'View the filters used to generate this report.',
                        },
                    ]"
                >
                    <TabItem>
                        <Tabs
                            :links="[
                                { title: 'Basic statistical measures' },
                                { title: 'Variables over time' },
                                { title: 'Information for each entity' },
                            ]"
                        >
                            <TabItem>
                                <CopyTable :data="data.results.statistics" />
                            </TabItem>
                            <TabItem>
                                <div class="row">
                                    <TableLine
                                        v-for="item in timeSeries"
                                        class="col-lg-6 col-12 m-0 p-0"
                                        :title="item.title"
                                        :data="item.data"
                                    />
                                </div>
                            </TabItem>
                            <TabItem>
                                <Tabs
                                    :links="[
                                        { title: 'Patent' },
                                        { title: 'Inventor' },
                                        { title: 'Assignee' },
                                        { title: 'CPC' },
                                    ]"
                                >
                                    <TabItem>
                                        <div class="row">
                                            <TableBar
                                                v-for="item in entity.patent"
                                                :title="item.title"
                                                :data="item.data"
                                                class="col-lg-6 col-12"
                                            />
                                        </div>
                                    </TabItem>
                                    <TabItem>
                                        <div class="row">
                                            <TableBar
                                                class="col-lg-6 col-12"
                                                title="10 most productive inventors"
                                                :data="
                                                    data.results.entity.inventor
                                                        .top10
                                                "
                                            />
                                            <TableHeatmap
                                                class="col-12"
                                                title="Inventor Location Distribution"
                                                :data="
                                                    data.results.entity.inventor
                                                        .locations
                                                "
                                            />
                                        </div>
                                    </TabItem>
                                    <TabItem>
                                        <div class="row">
                                            <TableBar
                                                class="col-lg-6 col-12"
                                                title="10 most prominent assignees"
                                                :data="
                                                    data.results.entity
                                                        .assignees.top10
                                                "
                                            />
                                            <TableBar
                                                class="col-lg-6 col-12"
                                                title="Assignee Types"
                                                :data="
                                                    data.results.entity
                                                        .assignees.type
                                                "
                                            />
                                            <TableHeatmap
                                                class="col-12"
                                                title="Assignee Location Distribution"
                                                :data="
                                                    data.results.entity
                                                        .assignees.locations
                                                "
                                            />
                                        </div>
                                    </TabItem>
                                    <TabItem>
                                        <div class="row">
                                            <TableBar
                                                v-for="item in entity.cpc"
                                                :title="item.title"
                                                :data="item.data"
                                                class="col-lg-6 col-12"
                                            />
                                        </div>
                                    </TabItem>
                                </Tabs>
                            </TabItem>
                        </Tabs>
                    </TabItem>
                    <TabItem> Thematic Analysis </TabItem>
                    <TabItem> Network Analysis </TabItem>
                    <TabItem> Patents </TabItem>
                    <TabItem>
                        <CopyTable :data="filtersAsTable" />
                    </TabItem>
                </Tabs>
            </div>
        </div>
    </div>
</template>

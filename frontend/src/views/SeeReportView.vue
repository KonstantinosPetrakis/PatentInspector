<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import {
    authFetch,
    reportToSubmittedFilters,
    dateTimeToString,
} from "../utils";

import Tabs from "../components/Tabs.vue";
import TabItem from "../components/TabItem.vue";
import DescriptiveAnalysis from "../components/view-report/DescriptiveAnalysis.vue";
import Filters from "../components/view-report/Filters.vue";
import Patents from "../components/view-report/Patents.vue";
import NetworkAnalysis from "../components/view-report/NetworkAnalysis.vue";
import ThematicAnalysis from "../components/ThematicAnalysis.vue";

const router = useRouter();
const props = defineProps(["id", "page"]);
const data = ref();
const loading = ref(true);

const getData = async () => {
    const response = await authFetch(`/report/${props.id}`);
    if (!response.ok) router.replace({ name: "notFound" });

    const responseData = await response.json();
    const dataCopy = JSON.parse(JSON.stringify(responseData));
    responseData.filters = reportToSubmittedFilters(dataCopy);
    data.value = responseData;
};

onMounted(async () => {
    await getData();
    loading.value = false;
});
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
        <div v-else-if="data.status == 'waiting_for_analysis'">
            <h1 class="h1 text-center">PatentAnalyzer</h1>
            <h4 class="h4 text-center">Report #{{ data?.id }}</h4>
            <div class="text-center">
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
                    Created: {{ dateTimeToString(data?.datetime_created) }}
                </span>
                <span class="badge text-bg-secondary fs-6 m-2">
                    Analysis Started:
                    {{ dateTimeToString(data?.datetime_analysis_started) }}
                </span>
                <span class="badge text-bg-secondary fs-6 m-2">
                    Analysis Ended:
                    {{ dateTimeToString(data?.datetime_analysis_ended) }}
                </span>
                <span class="badge text-bg-secondary fs-6 m-2">
                    Patents Analyzed:
                    {{ data.results.patents_count }}
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
                        <DescriptiveAnalysis :results="data.results" />
                    </TabItem>
                    <TabItem>
                        <ThematicAnalysis
                            :topicModeling="data.results.topic_modeling"
                            :status="data.status"
                            :id="id"
                        />
                    </TabItem>
                    <TabItem>
                        <NetworkAnalysis :citations="data.results.citations" />
                    </TabItem>
                    <TabItem>
                        <Patents :id="id" :page="page" />
                    </TabItem>
                    <TabItem>
                        <Filters :filters="data.filters" />
                    </TabItem>
                </Tabs>
            </div>
        </div>
    </div>
</template>

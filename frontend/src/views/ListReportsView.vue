<script setup>
import { onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { authFetch, dateTimeToString } from "../utils";
import Pagination from "../components/Pagination.vue";

const props = defineProps(["page"]);

const reportsPerPage = 10;
const reports = ref([]);
const messages = ref([]);

const updateData = async () => {
    const response = await authFetch(
        `/report?page_size=${reportsPerPage}&page=${props.page}`
    );

    reports.value = await response.json();
};

const deleteReport = async (id) => {
    if (!confirm("Are you sure you want to delete this report?")) return;

    const response = await authFetch(`/report/${id}`, {
        method: "DELETE",
    });

    if (response.ok) {
        reports.value.results = reports.value.results.filter(
            (report) => report.id !== id
        );
        messages.value.push({
            type: "success",
            text: "Report deleted successfully.",
        });
    } else {
        messages.value.push({
            type: "danger",
            text: "Failed to delete report.",
        });
    }
};

onMounted(updateData);
watch(() => props.page, updateData);


</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentAnalyzer</h1>
        <h4 class="h4 text-center">All Reports</h4>
        <p class="fs-5 text-center">
            Showing {{ reports.count }} report(s) in total.
        </p>
        <div class="table-responsive">
            <div
                v-for="message of messages"
                :class="`alert alert-${message.type} alert-dismissible`"
            >
                {{ message.text }}
                <button
                    type="button"
                    class="btn-close"
                    data-bs-dismiss="alert"
                ></button>
            </div>
            <table class="table table-striped mt-5">
                <thead>
                    <th class="text-center">Inspect</th>
                    <th class="text-center">Created</th>
                    <th class="text-center">Analysis started</th>
                    <th class="text-center">Analysis finished</th>
                    <th class="text-center">Delete</th>
                </thead>
                <tbody class="align-middle">
                    <tr v-for="report of reports.results">
                        <td class="text-center">
                            <router-link
                                :to="{
                                    name: 'report',
                                    params: { id: report.id },
                                }"
                            >
                                <button class="btn btn-secondary">
                                    Inspect
                                </button>
                            </router-link>
                        </td>
                        <td class="text-center">
                            {{ dateTimeToString(report.datetime_created) }}
                        </td>
                        <td class="text-center">
                            {{
                                dateTimeToString(report.datetime_analysis_started)
                            }}
                        </td>
                        <td class="text-center">
                            {{ dateTimeToString(report.datetime_analysis_ended) }}
                        </td>
                        <td class="text-center">
                            <button
                                class="btn btn-danger"
                                @click="deleteReport(report.id)"
                            >
                                Delete
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <Pagination
            :page="page"
            :total-items="reports.count"
            :items-per-page="reportsPerPage"
            urlName="listReports"
        />
    </div>
</template>

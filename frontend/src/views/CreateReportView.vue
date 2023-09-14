<script setup>
import { ref, reactive, toRaw } from "vue";
import Accordion from "../components/Accordion.vue";
import AccordionItem from "../components/AccordionItem.vue";
import MinMaxDateInput from "../components/form-widgets/MinMaxDateInput.vue";
import SingleChoiceInput from "../components/form-widgets/SingleChoiceInput.vue";
import TagInput from "../components/form-widgets/TagInput.vue";
import MinMaxIntInput from "../components/form-widgets/MinMaxIntInput.vue";
import TaggingAsyncInput from "../components/form-widgets/TaggingAsyncInput.vue";
import PointRadiusInput from "../components/form-widgets/PointRadiusInput.vue";
import { authFetch } from "../utils";
import router from "../router";

const messages = ref([]);
const errors = reactive({});
const patentKeywordOptions = ref([]);

const data = reactive({
    patent_office: null,
    patent_type: null,
    patent_keywords: [],
    patent_keywords_logic: { id: "&", label: "All keywords" },
    patent_application_filed_date: null,
    patent_granted_date: null,
    patent_figures_count: null,
    patent_claims_count: null,
    patent_sheets_count: null,
    patent_withdrawn: null,
    cpc_section: [],
    cpc_class: [],
    cpc_subclass: [],
    cpc_group: [],
    pct_application_date: null,
    pct_granted: null,
    inventor_first_name: null,
    inventor_last_name: null,
    inventor_location: null,
    assignee_first_name: null,
    assignee_last_name: null,
    assignee_organization: null,
    assignee_location: null,
});

const optionObjectToArray = (obj) => {
    if (!obj || obj.length === 0) return obj;

    if (Array.isArray(obj)) {
        const key = Object.keys(obj[0])[0];
        return obj.map((obj) => obj[key]);
    }

    const key = Object.keys(obj)[0];
    return obj[key];
};

const processCpcData = (obj) => {
    const key = Object.keys(obj)[0];
    return `${obj[key]} - ${obj.title}`;
};

const addTagToKeywordOptions = (tag) => {
    patentKeywordOptions.value.push(tag);
    data.patent_keywords.push(tag);
};

const createReport = async () => {
    if (Object.keys(errors).length) {
        window.scrollTo({ top: 0, behavior: "smooth" });
        return;
    }

    const reportData = toRaw(data);
    for (let key of [
        "patent_keywords_logic",
        "cpc_section",
        "cpc_class",
        "cpc_subclass",
        "cpc_group",
    ])
        reportData[key] = optionObjectToArray(reportData[key]);

    const response = await authFetch("/report", {
        method: "POST",
        body: JSON.stringify(reportData),
    });

    if (response.ok) router.push({ name: "listReports" });
    else {
        messages.value = [
            { type: "danger", message: "Failed to create report." },
        ];
        console.error(await response.json());
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
};
</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentAnalyzer</h1>
        <h4 class="h4 text-center">Create Report</h4>
        <p>
            Try to keep your your search specific. Broad sets will take longer
            to analyze and the analysis might be denied from the server if the
            resulted set exceeds a certain size (online version).
        </p>
        <form class="border shadow">
            <div class="messages m-2">
                <div
                    v-for="message of messages"
                    :class="`alert p-3 alert-${message.type}`"
                >
                    {{ message.message }}
                </div>
                <div v-if="Object.keys(errors).length">
                    <b> Please correct these errors: </b>
                    <div
                        v-for="(error, field) of errors"
                        class="alert alert-danger p-3"
                    >
                        {{ field }}: {{ error }}
                    </div>
                </div>
            </div>
            <Accordion id="form-accordion">
                <AccordionItem title="Main fields" active>
                    <SingleChoiceInput
                        field-label="Patent Office"
                        field-info="The patent office that granted the patent."
                        v-model="data.patent_office"
                        :options="['US']"
                    />
                    <SingleChoiceInput
                        field-label="Patent Type"
                        field-info="The type of the patent, utility is the most common."
                        v-model="data.patent_type"
                        :options="[
                            'utility',
                            'design',
                            'plant',
                            'reissue',
                            'defensive publication',
                        ]"
                    />
                    <TagInput
                        field-label="Patent Keywords"
                        field-info="Keywords that appear in the patent's title or abstract."
                        v-model="data.patent_keywords"
                        :options="patentKeywordOptions"
                        @tag="addTagToKeywordOptions"
                    />
                    <SingleChoiceInput
                        field-label="Patent Keywords Combination Logic"
                        field-info="Should all keywords appear in the patent or at least one of them?"
                        v-model="data.patent_keywords_logic"
                        :options="[
                            { id: '&', label: 'All keywords' },
                            { id: '|', label: 'At least 1 keyword' },
                        ]"
                        track-by="id"
                        label="label"
                    />
                    <MinMaxDateInput
                        field-label="Application Filed Date"
                        field-info="The range of dates the patent application was filed."
                        v-model="data.patent_application_filed_date"
                        v-model:errors="errors"
                    />
                    <MinMaxDateInput
                        field-label="Patent Granted Date"
                        field-info="The range of dates the patent was granted."
                        v-model="data.patent_granted_date"
                        v-model:errors="errors"
                    />
                    <MinMaxIntInput
                        field-label="Figure Count"
                        v-model="data.patent_figures_count"
                    />
                    <MinMaxIntInput
                        field-label="Claims Count"
                        v-model="data.patent_claims_count"
                    />
                    <MinMaxIntInput
                        field-label="Sheets Count"
                        v-model="data.patent_sheets_count"
                    />
                    <SingleChoiceInput
                        field-label="Withdrawn"
                        v-model="data.patent_withdrawn"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="CPC fields">
                    <TaggingAsyncInput
                        field-label="CPC Sections"
                        v-model="data.cpc_section"
                        :fetch-before="true"
                        url="/cpc/sections"
                        :customLabel="processCpcData"
                        track-by="section"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Classes"
                        v-model="data.cpc_class"
                        :fetch-before="true"
                        url="/cpc/classes"
                        :customLabel="processCpcData"
                        track-by="_class"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Subclasses"
                        v-model="data.cpc_subclass"
                        url="/cpc/subclasses"
                        :customLabel="processCpcData"
                        track-by="subclass"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Groups"
                        v-model="data.cpc_group"
                        url="/cpc/groups"
                        :customLabel="processCpcData"
                        track-by="group"
                        label="title"
                    />
                </AccordionItem>
                <AccordionItem title="PCT fields">
                    <MinMaxDateInput
                        field-label="Application Filed Date"
                        v-model="data.pct_application_date"
                        v-model:errors="errors"
                    />
                    <SingleChoiceInput
                        field-label="Granted"
                        v-model="data.pct_granted"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="Inventor fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="data.inventor_first_name"
                        url="/inventors"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="data.inventor_last_name"
                        url="/inventors"
                        query-param="last_name"
                    />
                    <PointRadiusInput
                        field-label="Inventor Location"
                        field-info="The location of the inventor.
                        Select the circle from the menu on the left click on the
                        map to set the center and drag to set the radius."
                        v-model="data.inventor_location"
                    />
                </AccordionItem>
                <AccordionItem title="Assignee fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="data.assignee_first_name"
                        url="/assignees"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="data.assignee_last_name"
                        url="/assignees"
                        query-param="last_name"
                    />
                    <TaggingAsyncInput
                        field-label="Organization"
                        v-model="data.assignee_organization"
                        url="/assignees"
                        query-param="organization"
                    />
                    <PointRadiusInput
                        field-label="Assignee Location"
                        field-info="The location of the assignee.
                        Select the circle from the menu on the left click on the
                        map to set the center and drag to set the radius."
                        v-model="data.assignee_location"
                    />
                </AccordionItem>
            </Accordion>
            <button
                class="btn btn-outline-secondary m-2 py-2"
                @click.prevent="createReport"
            >
                Create Report
            </button>
        </form>
    </div>
</template>

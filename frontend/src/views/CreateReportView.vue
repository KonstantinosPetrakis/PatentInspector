<script setup>
import "vue-multiselect/dist/vue-multiselect.css";
import "@vueform/slider/themes/default.css";
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

const messages = ref([]);
const patentKeywordOptions = ref([]);

const data = reactive({
    patentOffice: null,
    patentType: null,
    patentKeywords: [],
    patentKeywordsLogic: { id: "&", label: "All keywords" },
    patentApplicationFiledDate: null,
    patentGrantedDate: null,
    patentFiguresCount: null,
    patentClaimsCount: null,
    patentSheetsCount: null,
    patentWithdrawn: null,
    cpcSection: [],
    cpcClass: [],
    cpcSubclass: [],
    cpcGroup: [],
    pctApplicationDate: null,
    pctGranted: null,
    inventorFirstName: null,
    inventorLastName: null,
    inventorLocation: null,
    assigneeFirstName: null,
    assigneeLastName: null,
    assigneeOrganization: null,
    assigneeLocation: null,
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
    data.patentKeywords.push(tag);
};

const createReport = async () => {
    const reportData = toRaw(data);
    for (let key of [
        "patentKeywordsLogic",
        "cpcSection",
        "cpcClass",
        "cpcSubclass",
        "cpcGroup",
    ])
        reportData[key] = optionObjectToArray(reportData[key]);

    const response = await authFetch("/report", {
        method: "POST",
        body: JSON.stringify(reportData),
    });

    if (response.ok)
        messages.value = [
            { type: "success", message: "Report created successfully." },
        ];
    else {
        messages.value = [
            { type: "danger", message: "Failed to create report." },
        ];
        console.error(await response.json());
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
            <div class="messages">
                <div
                    v-for="message of messages"
                    :class="`alert m-2 p-3 alert-${message.type}`"
                >
                    {{ message.message }}
                </div>
            </div>
            <Accordion id="form-accordion">
                <AccordionItem title="Main fields" active>
                    <SingleChoiceInput
                        field-label="Patent Office"
                        field-info="The patent office that granted the patent."
                        v-model="data.patentOffice"
                        :options="['US']"
                    />
                    <SingleChoiceInput
                        field-label="Patent Type"
                        field-info="The type of the patent, utility is the most common."
                        v-model="data.patentType"
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
                        v-model="data.patentKeywords"
                        :options="patentKeywordOptions"
                        @tag="addTagToKeywordOptions"
                    />
                    <SingleChoiceInput
                        field-label="Patent Keywords Combination Logic"
                        field-info="Should all keywords appear in the patent or at least one of them?"
                        v-model="data.patentKeywordsLogic"
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
                        v-model="data.patentApplicationFiledDate"
                    />
                    <MinMaxDateInput
                        field-label="Patent Granted Date"
                        field-info="The range of dates the patent was granted."
                        v-model="data.patentGrantedDate"
                    />
                    <MinMaxIntInput
                        field-label="Figure Count"
                        v-model="data.patentFiguresCount"
                    />
                    <MinMaxIntInput
                        field-label="Claims Count"
                        v-model="data.patentClaimsCount"
                    />
                    <MinMaxIntInput
                        field-label="Sheets Count"
                        v-model="data.patentSheetsCount"
                    />
                    <SingleChoiceInput
                        field-label="Withdrawn"
                        v-model="data.patentWithdrawn"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="CPC fields">
                    <TaggingAsyncInput
                        field-label="CPC Sections"
                        v-model="data.cpcSection"
                        :fetch-before="true"
                        url="/cpc/sections"
                        :customLabel="processCpcData"
                        track-by="section"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Classes"
                        v-model="data.cpcClass"
                        :fetch-before="true"
                        url="/cpc/classes"
                        :customLabel="processCpcData"
                        track-by="Class"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Subclasses"
                        v-model="data.cpcSubclass"
                        url="/cpc/subclasses"
                        :customLabel="processCpcData"
                        track-by="subclass"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Groups"
                        v-model="data.cpcGroup"
                        url="/cpc/groups"
                        :customLabel="processCpcData"
                        track-by="group"
                        label="title"
                    />
                </AccordionItem>
                <AccordionItem title="PCT fields">
                    <MinMaxDateInput
                        field-label="Application Filed Date"
                        v-model="data.pctApplicationDate"
                    />
                    <SingleChoiceInput
                        field-label="Granted"
                        v-model="data.pctGranted"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="Inventor fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="data.inventorFirstName"
                        url="/inventors"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="data.inventorLastName"
                        url="/inventors"
                        query-param="last_name"
                    />
                    <PointRadiusInput
                        field-label="Inventor Location"
                        field-info="The location of the inventor.
                        Select the circle from the menu on the left click on the
                        map to set the center and drag to set the radius."
                        v-model="data.inventorLocation"
                    />
                </AccordionItem>
                <AccordionItem title="Assignee fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="data.assigneeFirstName"
                        url="/assignees"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="data.assigneeLastName"
                        url="/assignees"
                        query-param="last_name"
                    />
                    <TaggingAsyncInput
                        field-label="Organization"
                        v-model="data.assigneeOrganization"
                        url="/assignees"
                        query-param="organization"
                    />
                    <PointRadiusInput
                        field-label="Assignee Location"
                        field-info="The location of the assignee.
                        Select the circle from the menu on the left click on the
                        map to set the center and drag to set the radius."
                        v-model="data.assigneeLocation"
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

<script setup>
import "vue-multiselect/dist/vue-multiselect.css";
import "@vueform/slider/themes/default.css";
import { ref } from "vue";
import Accordion from "../components/Accordion.vue";
import AccordionItem from "../components/AccordionItem.vue";
import MinMaxDateInput from "../components/form-widgets/MinMaxDateInput.vue";
import SingleChoiceInput from "../components/form-widgets/SingleChoiceInput.vue";
import TagInput from "../components/form-widgets/TagInput.vue";
import MinMaxIntInput from "../components/form-widgets/MinMaxIntInput.vue";
import TaggingAsyncInput from "../components/form-widgets/TaggingAsyncInput.vue";
import PointRadiusInput from "../components/form-widgets/PointRadiusInput.vue";

const addTagToKeywordOptions = (tag) => {
    patentKeywordOptions.value.push(tag);
    patentKeywords.value.push(tag);
};

const processCpcData = (obj) => {
    const key = Object.keys(obj)[0];
    return `${obj[key]} - ${obj.title}`;
};

const patentOffice = ref(null);
const patentType = ref(null);
const patentKeywords = ref([]);
const patentKeywordOptions = ref([]);
const patentKeywordsLogic = ref({ id: "&", label: "All keywords" });
const patentApplicationFiledDateMin = ref(null);
const patentApplicationFiledDateMax = ref(null);
const patentGrantedDateMin = ref(null);
const patentGrantedDateMax = ref(null);
const patentFigureCountMin = ref(null);
const patentFigureCountMax = ref(null);
const patentClaimsCountMin = ref(null);
const patentClaimsCountMax = ref(null);
const patentSheetsCountMin = ref(null);
const patentSheetsCountMax = ref(null);
const patentWithdrawn = ref(null);
const cpcSection = ref([]);
const cpcClass = ref([]);
const cpcSubclass = ref([]);
const cpcGroup = ref([]);
const pctApplicationFiledDateMin = ref(null);
const pctApplicationFiledDateMax = ref(null);
const pctGranted = ref(null);
const inventorFirstName = ref(null);
const inventorLastName = ref(null);
const inventorLocation = ref(null);
const assigneeFirstName = ref(null);
const assigneeLastName = ref(null);
const assigneeOrganization = ref(null);
const assigneeLocation = ref(null);

const createReport = () => {
    console.log({
        patentOffice: patentOffice.value,
        patentType: patentType.value,
        patentKeywords: patentKeywords.value,
        patentKeywordsLogic: patentKeywordsLogic.value,
        patentApplicationFiledDateMin: patentApplicationFiledDateMin.value,
        patentApplicationFiledDateMax: patentApplicationFiledDateMax.value,
        patentGrantedDateMin: patentGrantedDateMin.value,
        patentGrantedDateMax: patentGrantedDateMax.value,
        patentFigureCountMin: patentFigureCountMin.value,
        patentFigureCountMax: patentFigureCountMax.value,
        patentClaimsCountMin: patentClaimsCountMin.value,
        patentClaimsCountMax: patentClaimsCountMax.value,
        patentSheetsCountMin: patentSheetsCountMin.value,
        patentSheetsCountMax: patentSheetsCountMax.value,
        patentWithdrawn: patentWithdrawn.value,
        cpcSection: cpcSection.value,
        cpcClass: cpcClass.value,
        cpcSubclass: cpcSubclass.value,
        cpcGroup: cpcGroup.value,
        pctApplicationFiledDateMin: pctApplicationFiledDateMin.value,
        pctApplicationFiledDateMax: pctApplicationFiledDateMax.value,
        pctGranted: pctGranted.value,
        inventorFirstName: inventorFirstName.value,
        inventorLastName: inventorLastName.value,
        inventorLocation: inventorLocation.value,
        assigneeFirstName: assigneeFirstName.value,
        assigneeLastName: assigneeLastName.value,
        assigneeOrganization: assigneeOrganization.value,
        assigneeLocation: assigneeLocation.value,
    });
};
</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentAnalyzer</h1>
        <h4 class="h4 text-center">Create Report</h4>
        <form class="border shadow">
            <Accordion id="form-accordion">
                <AccordionItem title="Main fields" active>
                    <SingleChoiceInput
                        field-label="Patent Office"
                        v-model="patentOffice"
                        :options="['USPTO']"
                    />
                    <SingleChoiceInput
                        field-label="Patent Type"
                        v-model="patentType"
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
                        v-model="patentKeywords"
                        :options="patentKeywordOptions"
                        @tag="addTagToKeywordOptions"
                    />
                    <SingleChoiceInput
                        field-label="Patent Keywords Combination Logic"
                        v-model="patentKeywordsLogic"
                        :options="[
                            { id: '&', label: 'All keywords' },
                            { id: '|', label: 'At least 1 keyword' },
                        ]"
                        track-by="id"
                        label="label"
                    />
                    <MinMaxDateInput
                        field-label="Application Filed Date"
                        v-model:min="patentApplicationFiledDateMin"
                        v-model:max="patentApplicationFiledDateMax"
                    />
                    <MinMaxDateInput
                        field-label="Patent Granted Date"
                        v-model:min="patentGrantedDateMin"
                        v-model:max="patentGrantedDateMax"
                    />
                    <MinMaxIntInput
                        field-label="Figure Count"
                        v-model:minValue="patentFigureCountMin"
                        v-model:maxValue="patentFigureCountMax"
                    />
                    <MinMaxIntInput
                        field-label="Claims Count"
                        v-model:minValue="patentClaimsCountMin"
                        v-model:maxValue="patentClaimsCountMax"
                    />
                    <MinMaxIntInput
                        field-label="Sheets Count"
                        v-model:minValue="patentSheetsCountMin"
                        v-model:maxValue="patentSheetsCountMax"
                    />
                    <SingleChoiceInput
                        field-label="Withdrawn"
                        v-model="patentWithdrawn"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="CPC fields">
                    <TaggingAsyncInput
                        field-label="CPC Sections"
                        v-model="cpcSection"
                        :fetch-before="true"
                        url="/cpc/sections"
                        :customLabel="processCpcData"
                        track-by="section"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Classes"
                        v-model="cpcClass"
                        :fetch-before="true"
                        url="/cpc/classes"
                        :customLabel="processCpcData"
                        track-by="_class"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Subclasses"
                        v-model="cpcSubclass"
                        url="/cpc/subclasses"
                        :customLabel="processCpcData"
                        track-by="subclass"
                        label="title"
                    />
                    <TaggingAsyncInput
                        field-label="CPC Groups"
                        v-model="cpcGroup"
                        url="/cpc/groups"
                        :customLabel="processCpcData"
                        track-by="group"
                        label="title"
                    />
                </AccordionItem>
                <AccordionItem title="PCT fields">
                    <MinMaxDateInput
                        field-label="Application Filed Date"
                        v-model:min="pctApplicationFiledDateMin"
                        v-model:max="pctApplicationFiledDateMax"
                    />
                    <SingleChoiceInput
                        field-label="Granted"
                        v-model="pctGranted"
                        :options="['yes', 'no']"
                    />
                </AccordionItem>
                <AccordionItem title="Inventor fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="inventorFirstName"
                        url="/inventors"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="inventorLastName"
                        url="/inventors"
                        query-param="last_name"
                    />
                    <PointRadiusInput
                        field-label="Inventor Location"
                        v-model="inventorLocation"
                    />
                </AccordionItem>
                <AccordionItem title="Assignee fields">
                    <TaggingAsyncInput
                        field-label="First Name"
                        v-model="assigneeFirstName"
                        url="/assignees"
                        query-param="first_name"
                    />
                    <TaggingAsyncInput
                        field-label="Last Name"
                        v-model="assigneeLastName"
                        url="/assignees"
                        query-param="last_name"
                    />
                    <TaggingAsyncInput
                        field-label="Organization"
                        v-model="assigneeOrganization"
                        url="/assignees"
                        query-param="organization"
                    />
                    <PointRadiusInput
                        field-label="Assignee Location"
                        v-model="assigneeLocation"
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

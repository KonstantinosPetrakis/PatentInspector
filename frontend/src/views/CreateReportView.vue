<script setup>
import { ref } from "vue";
import Accordion from "../components/Accordion.vue";
import AccordionItem from "../components/AccordionItem.vue";
import MinMaxDateInput from "../components/form-widgets/MinMaxDateInput.vue";
import SingleChoiceInput from "../components/form-widgets/SingleChoiceInput.vue";
import TagInput from "../components/form-widgets/TagInput.vue";
import MinMaxIntInput from "../components/form-widgets/MinMaxIntInput.vue";

const addTagToKeywordOptions = (tag) => {
    patentKeywordOptions.value.push(tag);
    patentKeywords.value.push(tag);
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
const cpcSection = ref(null);
const cpcClass = ref(null);
const cpcSubclass = ref(null);
const cpcMainGroup = ref(null);
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
                    Cpc fields...
                </AccordionItem>
                <AccordionItem title="PCT fields">
                    PCT fields...
                </AccordionItem>
                <AccordionItem title="Inventor fields">
                    Inventor fields...
                </AccordionItem>
                <AccordionItem title="Assignee fields">
                    Assignee fields...
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

<script setup>
import { reactive, ref, computed, onMounted } from "vue";
import SingleChoiceInput from "./form-widgets/SingleChoiceInput.vue";
import MinMaxDateInput from "./form-widgets/MinMaxDateInput.vue";
import TableBar from "./charts/TableBar.vue";
import InfoPopover from "./InfoPopover.vue";
import TopicScatter from "./charts/TopicScatter.vue";
import Accordion from "./Accordion.vue";
import AccordionItem from "./AccordionItem.vue";

import { authFetch, dateToString } from "../utils";

const props = defineProps(["topicModeling", "status", "id"]);
const data = reactive({
    n_words: null,
    n_topics: null,
    method: null,
    cagr_dates: null,
});

const errors = reactive({});

const waitingForTopicAnalysis = ref(
    props.status == "waiting_for_topic_analysis"
);

const topicsAsTables = computed(() => {
    const tables = [];

    for (let topic of props.topicModeling.topics) {
        const table = [["Word", "Weight"]];
        for (let i = 0; i < topic.words.length; i++) {
            table.push([topic.words[i], topic.weights[i]]);
        }
        tables.push(table);
    }

    return tables;
});

const submitTopicAnalysis = async () => {
    if (Object.keys(errors).length) return;

    const response = await authFetch(`/report/${props.id}/topic_analysis`, {
        method: "POST",
        body: JSON.stringify({
            n_words: data.n_words,
            n_topics: data.n_topics,
            method: data.method,
            start_date: data.cagr_dates.lower,
            end_date: data.cagr_dates.upper,
        }),
    });

    if (response.ok) waitingForTopicAnalysis.value = true;
};

onMounted(() => {
    data.n_words = props.topicModeling.n_words;
    data.n_topics = props.topicModeling.n_topics;
    data.method = props.topicModeling.method;
    data.cagr_dates = {
        lower: props.topicModeling.start_date,
        upper: props.topicModeling.end_date,
    };
});
</script>

<style>
.small-input {
    width: 5rem;
}
</style>

<template>
    <div class="row">
        <div v-if="waitingForTopicAnalysis">
            <div class="alert alert-info">
                <h4 class="alert-heading">
                    Topic analysis execution is in progress.
                </h4>
                <p>You can come later to observe the results.</p>
            </div>
        </div>
        <div v-else>
            <p>
                Extracted <b> {{ topicModeling.n_topics }} </b> topics from the
                corpus using the <b> {{ topicModeling.method }} </b> model.
                Showing <b> {{ topicModeling.n_words }} </b> words per topic.
            </p>
            <p>
                The dates used for the CAGR calculation utilized in the topic
                classification are the following:
                <b> {{ dateToString(topicModeling.start_date, "N/A") }} </b> -
                <b> {{ dateToString(topicModeling.end_date, "N/A") }} </b>.
            </p>
            <p>
                Coherence score: <b> {{ topicModeling.coherence }} </b>
                <InfoPopover
                    message="Coherence score is used to measure
                    how interpretable the topics are to humans."
                />
            </p>
            <div class="row m-0 p-1">
                <p>
                    You can conduct a new topic analysis within the same report
                    by filling out the form below:
                </p>
                <Accordion id="thematic-analysis-form">
                    <AccordionItem
                        class="col-lg-6 col-12"
                        title="Topic Analysis Form"
                        :active="false"
                    >
                        <form>
                            <div v-if="Object.keys(errors).length">
                                <div
                                    v-for="(error, field) of errors"
                                    class="alert alert-danger p-2"
                                >
                                    {{ field }}: {{ error }}
                                </div>
                            </div>
                            <label class="d-flex align-items-center">
                                Method
                                <div class="ms-2">
                                    <SingleChoiceInput
                                        v-model="data.method"
                                        :options="['NMF', 'LDA']"
                                    />
                                </div>
                            </label>
                            <label class="d-flex align-items-center my-2">
                                Number of topics
                                <input
                                    class="ms-3 small-input form-control"
                                    type="number"
                                    v-model="data.n_topics"
                                />
                            </label>
                            <label class="d-flex align-items-center my-2">
                                Number of words per topic
                                <input
                                    class="ms-3 small-input form-control"
                                    type="number"
                                    v-model="data.n_words"
                                />
                            </label>
                            <label class="d-flex align-items-center my-2">
                                Dates for classification
                                <div class="ms-2">
                                    <MinMaxDateInput
                                        v-model="data.cagr_dates"
                                        field-label="Classification Dates"
                                        :display-label="false"
                                        :errors="errors"
                                    />
                                </div>
                            </label>
                            <button
                                class="btn btn-secondary"
                                @click.prevent="submitTopicAnalysis"
                            >
                                Submit
                            </button>
                        </form>
                    </AccordionItem>
                </Accordion>
            </div>
            <h6 class="text-center col-12 col-lg-6 mt-3">
                Topic classification
            </h6>
            <TopicScatter :topics="props.topicModeling.topics" />
            <h6 class="text-center mt-3">Topics</h6>
            <div class="row">
                <TableBar
                    v-for="(topic, i) of topicsAsTables"
                    :title="`Topic ${i + 1}`"
                    :data="topic"
                    class="col-lg-6 col-12 m-0 p-0"
                />
            </div>
        </div>
    </div>
</template>

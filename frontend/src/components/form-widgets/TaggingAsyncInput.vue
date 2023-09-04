<script setup>
import { ref, onMounted } from "vue";
import { debounce } from "lodash";
import MultiSelect from "vue-multiselect";
import FieldWrapper from "./FieldWrapper.vue";
import { authFetch, getCompleteUrl } from "../../utils";

const props = defineProps({
    fetchBefore: {
        type: Boolean,
        default: false,
    },
    url: {
        type: String,
        required: true,
    },
    queryParam: {
        type: String,
        default: "q",
    },
});

const options = ref([]);
const searching = ref(false);
const url = getCompleteUrl(props.url);

const onSearch = debounce(async (query) => {
    if (!props.fetchBefore && query) {
        searching.value = true;
        const urlWithParams = new URL(url);
        urlWithParams.searchParams.set(props.queryParam, query);
        const response = await authFetch(urlWithParams.toString());
        const data = await response.json();
        options.value = data.results;
        searching.value = false;
    }
}, 500);

onMounted(async () => {
    if (props.fetchBefore) {
        const response = await authFetch(url);
        options.value = await response.json();
    }
});
</script>

<template>
    <!-- 
        empty tag-placeholder doesn't include the 'press enter to add new tag' msg 
        @tag null does nothing when a new tag is added, so we don't include new tags
    -->
    <FieldWrapper v-bind="$attrs">
        <MultiSelect
            @search-change="onSearch"
            :internal-search="fetchBefore"
            :loading="searching"
            :options="options"
            :multiple="true"
            :close-on-select="false"
            :clear-on-select="false"
            v-bind="$attrs"
        >
            <!-- This is required to pass down all slots -->
            <template v-for="(_, slot) of $slots" v-slot:[slot]="scope">
                <slot :name="slot" v-bind="scope"> </slot>
            </template>
        </MultiSelect>
    </FieldWrapper>
</template>

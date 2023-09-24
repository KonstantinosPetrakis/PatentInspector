<script setup>
import { computed } from "vue";
import Tabs from "../../Tabs.vue";
import TabItem from "../../TabItem.vue";
import TableBar from "../../charts/TableBar.vue";
import TableHeatmap from "../../charts/TableHeatmap.vue";
import { queryGooglePatents } from "../../../utils";

const props = defineProps(["entity"]);

const computedEntities = computed(() => {
    return {
        patent: [
            {
                title: "PCT Distribution",
                data: props.entity.patent.pct,
            },
            {
                title: "Type Distribution",
                data: props.entity.patent.type,
            },
            {
                title: "Patent Office Distribution",
                data: props.entity.patent.office,
            },
        ],
        cpc: [
            {
                title: "CPC Section Distribution",
                data: props.entity.cpc.section,
            },
            {
                title: "Top 5 CPC Classes",
                data: props.entity.cpc.top5_classes,
            },
            {
                title: "Top 5 CPC Subclasses",
                data: props.entity.cpc.top5_subclasses,
                info: "Click on a bar to search for patents under a CPC subclass on Google Patents",
                click: (name) => queryGooglePatents(`q=${findCPC(name)}`),
            },
            {
                title: "Top 5 CPC groups",
                data: props.entity.cpc.top5_groups,
                info: "Click on a bar to search for patents under a CPC group on Google Patents",
                click: (name) => queryGooglePatents(`q=${findCPC(name)}`),
            },
        ],
    };
});

const findCPC = (label) => label.split("-")[0].trim();
</script>

<template>
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
                    v-for="item in computedEntities.patent"
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
                    :data="entity.inventor.top10"
                    info="Click on a bar to search for an inventor's patents on Google Patents"
                    @click="(name) => queryGooglePatents(`inventor=${name}`)"
                />
                <TableHeatmap
                    class="col-12"
                    title="Inventor Location Distribution"
                    :data="entity.inventor.locations"
                />
            </div>
        </TabItem>
        <TabItem>
            <div class="row">
                <TableBar
                    class="col-lg-6 col-12"
                    title="10 most prominent assignees"
                    :data="entity.assignees.top10"
                    info="Click on an assignee's name bar to search for their patents on Google Patents"
                    @click="(name) => queryGooglePatents(`assignee=${name}`)"
                />
                <TableBar
                    class="col-lg-6 col-12"
                    title="Assignee Types"
                    :data="entity.assignees.type"
                />
                <TableHeatmap
                    class="col-12"
                    title="Assignee Location Distribution"
                    :data="entity.assignees.locations"
                />
            </div>
        </TabItem>
        <TabItem>
            <div class="row">
                <TableBar
                    v-for="item in computedEntities.cpc"
                    :title="item.title"
                    :data="item.data"
                    :info="item?.info"
                    @click="item?.click"
                    class="col-lg-6 col-12"
                />
            </div>
        </TabItem>
    </Tabs>
</template>

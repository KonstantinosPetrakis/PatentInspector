<script setup>
import TableBar from "../charts/TableBar.vue";
import Graph3D from "../charts/Graph3D.vue";
import { sendToGooglePatents } from "../../utils";

const props = defineProps(["citations"]);

const findPatentCode = (label) => label.split("-")[0].trim();
</script>

<template>
    <div class="row">
        <TableBar
            title="Most cited patents locally"
            :data="citations.most_cited_local"
            class="col-lg-6 col-12"
            info="Click on a bar to view the patent on Google Patents"
            @click="(name) => sendToGooglePatents(findPatentCode(name))"
        />
        <TableBar
            title="Most cited patents globally"
            :data="citations.most_cited_global"
            class="col-lg-6 col-12"
            info="Click on a bar to view the patent on Google Patents"
            @click="(name) => sendToGooglePatents(findPatentCode(name))"
        />
        <Graph3D class="col-12" :data="citations.graph" />
    </div>
</template>

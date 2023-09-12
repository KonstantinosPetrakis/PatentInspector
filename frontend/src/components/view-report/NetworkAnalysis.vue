<script setup>
import TableBar from "../charts/TableBar.vue";
import Graph3D from "../charts/Graph3D.vue";

const props = defineProps(["citations"]);
</script>

<template>
    <div class="row">
        <TableBar
            title="Most cited patents locally"
            :data="citations.most_cited_local"
            class="col-lg-6 col-12"
        />
        <TableBar
            title="Most cited patents globally"
            :data="citations.most_cited_global"
            class="col-lg-6 col-12"
        />
        <Graph3D class="col-12" :data="citations.graph" />
    </div>
</template>

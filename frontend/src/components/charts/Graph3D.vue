<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { getColorMode } from "../../utils";
import ForceGraph3D from "3d-force-graph";

const props = defineProps(["data"]);
const shouldCreateGraph = ref(false);
const graphElement = ref(null);
const colorMode = ref(getColorMode());
let mutationObserver, resizeObserver, graph;

const darkMode = computed(() => colorMode.value === "dark");

const colors = computed(() => {
    return {
        body: darkMode.value ? "#fff" : "#000",
        background: darkMode.value ? "#212529" : "#fff",
        link: darkMode.value ? "#fff" : "#000",
        node: "#d45087",
    };
});

const graphData = computed(() => {
    const nodes = {};
    const edges = [];

    for (let citation of props.data) {
        const citingNode = {
            id: citation.citing_patent_id,
            code: citation.citing_patent_code,
            title: citation.citing_patent__title,
            granted_date: citation.citing_patent__granted_date,
        };

        const citedNode = {
            id: citation.cited_patent_id,
            code: citation.cited_patent_code,
            title: citation.cited_patent__title,
            granted_date: citation.cited_patent__granted_date,
        };

        nodes[citingNode.id] = citingNode;
        nodes[citedNode.id] = citedNode;
        edges.push({ source: citingNode.id, target: citedNode.id });
    }

    return { nodes, edges };
});

const nodeLabel = (node) => `
    <span style="color: ${colors.value.body}">
        ${node.code} - ${node.title} - ${node.granted_date}
    </span>`;

const nodeOnClick = (node) =>
    window.open(`https://patents.google.com/?oq=${node.code}`);

const createGraph = () => {
    if (mutationObserver) mutationObserver.disconnect();
    if (resizeObserver) resizeObserver.disconnect();

    const { nodes, edges } = graphData.value;

    graph = ForceGraph3D({ controlType: "orbit" })(graphElement.value)
        .graphData({ nodes: Object.values(nodes), links: edges })
        .nodeLabel(nodeLabel)
        .linkDirectionalArrowLength(3.5)
        .linkDirectionalArrowRelPos(1)
        .linkCurvature(0.25)
        .width(graphElement.value.offsetWidth)
        .height(window.screen.height * 0.8)
        .backgroundColor(colors.value.background)
        .linkColor(() => colors.value.link)
        .nodeColor(() => colors.value.node)
        .onNodeClick(nodeOnClick)
        .warmupTicks(30)
        .cooldownTicks(0)
        .enableNodeDrag(false)
        .pauseAnimation();

    mutationObserver = new IntersectionObserver((entries) => {
        if (!entries[0].isIntersecting) graph.pauseAnimation();
        else graph.resumeAnimation();
    }).observe(graphElement.value);

    resizeObserver = new ResizeObserver(() =>
        graph.width(graphElement.value.offsetWidth)
    ).observe(graphElement.value);
};

watch(shouldCreateGraph, (value) => {
    if (value) createGraph();
});

window.addEventListener("themeChanged", () => {
    colorMode.value = getColorMode();
    if (graph) {
        graph
            .backgroundColor(colors.value.background)
            .backgroundColor(colors.value.background)
            .linkColor(() => colors.value.link)
            .nodeColor(() => colors.value.node);
    }
});

onMounted(() => (shouldCreateGraph.value = props.data.length < 5000));
</script>

<template>
    <div>
        <div class="mt-5" v-show="shouldCreateGraph">
            <div ref="graphElement"></div>
        </div>
        <div class="mt-5" v-show="!shouldCreateGraph">
            <p>
                The citation graph consist of {{ data.length }} citations and it
                would need a lot of processing power to be drawn. This could
                lead to an unresponsive page, some PCs might handle it. If you
                want to try you can click on the button below. Although a graph
                of this size is not so easy to interpret/understand.
            </p>
            <button class="btn btn-secondary" @click="shouldCreateGraph = true">
                Create graph
            </button>
        </div>
    </div>
</template>

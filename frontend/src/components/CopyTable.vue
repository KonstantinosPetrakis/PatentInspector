<script setup>
import { ref } from "vue";
import { createAlert } from "../utils";

const props = defineProps(["data"]);
const table = ref(null);

const formatCell = (c) =>
    typeof c === "number" && parseInt(c) !== c ? c.toFixed(2) : c;

const copyTable = () => {
    let text = "";
    for (const row of props.data) {
        for (const cell of row) text += cell + "\t";
        text += "\n";
    }
    navigator.clipboard.writeText(text);
    createAlert("success", "Table copied to clipboard");
};
</script>

<style>
table .cell {
    max-height: 10rem;
    overflow-y: auto;
    overflow-x: hidden;
}
</style>

<template>
    <div>
        <div class="border p-1">
            <button class="btn btn-secondary my-1" @click="copyTable">
                <i class="bi bi-clipboard"></i>
            </button>
        </div>
        <div class="table-responsive">
            <table class="border border-1 table table-striped align-middle" ref="table">
                <thead>
                    <th v-for="head of data[0]">
                        {{ head }}
                    </th>
                </thead>
                <tbody>
                    <tr v-for="index in data.length" :key="index">
                        <td v-for="cell of data[index]">
                            <div class="cell">
                                {{ formatCell(cell) }}
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

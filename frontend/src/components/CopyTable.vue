<script setup>
import { ref } from "vue";

const props = defineProps(["data"]);
const table = ref(null);

const copyTable = () => {
    let text = "";
    for (const row of table.value.rows) {
        for (const cell of row.cells) text += cell.innerText + "\t";
        text += "\n";
    }
    navigator.clipboard.writeText(text);
};
</script>

<template>
    <div>
        <div>
            <button class="btn btn-secondary my-1" @click="copyTable">
                <i class="bi bi-clipboard"></i>
            </button>
        </div>
        <div class="table-responsive">
            <table class="border border-1 table table-striped" ref="table">
                <thead>
                    <th v-for="head of data[0]">
                        {{ head }}
                    </th>
                </thead>
                <tbody>
                    <tr v-for="index in data.length" :key="index">
                        <td v-for="cell of data[index]">
                            {{ cell }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

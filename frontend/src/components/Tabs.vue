<script setup>
import { ref, watch, onMounted } from "vue";
import InfoPopover from "./InfoPopover.vue";

const props = defineProps(["links"]);
const tabItems = ref(null);
const activeTab = ref(0);

const showItems = () => {
    for (let tabItem of tabItems.value.children)
        tabItem.classList.remove("active");
    tabItems.value.children[activeTab.value].classList.add("active");
};

watch(activeTab, showItems);
onMounted(() => showItems());

</script>

<template>
    <nav>
        <ul class="nav nav-tabs my-3">
            <li class="nav-item" v-for="(link, i) of links">
                <button
                    :class="`nav-link ${i == activeTab ? 'active' : ''}`"
                    @click="activeTab = i"
                >
                    {{ link.title }}
                    <InfoPopover v-if="link.info" :message="link.info" />
                </button>
            </li>
        </ul>
    </nav>
    <div class="tab-items" ref="tabItems">
        <slot> </slot>
    </div>
</template>

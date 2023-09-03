<script setup>
import { ref, onMounted } from "vue";

const props = defineProps({
    title: {
        type: String,
        required: true,
    },
    active: {
        type: Boolean,
        default: false,
    },
});

const element = ref(null);

const id = props.title.toLowerCase().replace(/\s/g, "-");
const parentId = ref("");

onMounted(() => (parentId.value = element.value.parentElement.id));
</script>

<template>
    <div class="accordion-item m-2" ref="element">
        <h2 class="accordion-header">
            <!-- 
                The @click.prevent, prevents the hash to be appended to the URL and
                make the vue router go crazy.
            -->
            <button
                :class="`accordion-button ${active ? '' : 'collapsed'} bg-secondary-subtle`"
                data-bs-toggle="collapse"
                :data-bs-target="`#${id}`"
                :aria-expanded="active"
                @click.prevent
            >
                {{ title }}
            </button>
        </h2>
        <div
            :id="id"
            :class="`accordion-collapse collapse ${active ? 'show' : ''}`"
            :data-bs-parent="`#${parentId}`"
        >
            <div class="accordion-body">
                <slot></slot>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from "vue";

const props = defineProps({
    length: {
        type: Number,
        default: 8,
    },
    modelValue: {
        type: String,
        required: true,
    },
});

const emit = defineEmits(["update:modelValue"]);

const otpElement = ref(null);
const charArray = reactive(Array(props.length).fill(""));

watch(charArray, () => emit("update:modelValue", charArray.join("")));
watch(
    () => props.modelValue,
    (value) => (charArray.value = value.split())
);

const focusNext = (i) => {
    if (i < props.length - 1) otpElement.value.children[i + 1].focus();
};

const focusPrev = (i) => {
    if (i > 0) otpElement.value.children[i - 1].focus();
};

const onInput = (e, i) => {
    if (!e.target.value.length) {
        onDelete(e, i);
        return;
    }
    const value = e.target.value.slice(-1).toLowerCase();
    charArray[i] = value;
    e.target.value = value;
    focusNext(i);
};

const onPaste = (e) => {
    const value = e.clipboardData.getData("text");
    for (let i = 0; i < value.length && i < props.length; i++)
        charArray[i] = value[i];
    focusNext(props.length - 2);
};

const onDelete = (e, i) => {
    charArray[i] = "";
    focusPrev(i);
};

const clear = () => {
    charArray.fill("");
    otpElement.value.children[0].focus();
};

onMounted(() => otpElement.value.children[0].focus());
</script>

<style>
.otp-input input {
    text-align: center;
    width: 3rem;
    height: 3rem;
    margin: 0.2rem;
    padding: 0;
    font-size: 2rem;
}

@media (max-width: 576px) {
    .otp-input input {
        width: 1.5rem;
        height: 1.5rem;
        font-size: 1.25rem;
    }
}
</style>

<template>
    <div class="d-flex">
        <div class="d-flex otp-input" ref="otpElement">
            <input
                class="form-control"
                type="text"
                v-for="(val, i) in charArray"
                :key="i"
                :value="val"
                @input="(e) => onInput(e, i)"
                @paste.prevent="(e) => onPaste(e)"
                @keydown.prevent.delete="(e) => onDelete(e, i)"
                @keydown.right="() => focusNext(i)"
                @keydown.left="() => focusPrev(i)"
            />
        </div>
        <button class="ms-2 btn btn-secondary" @click.prevent="clear">
            Clear
        </button>
    </div>
</template>

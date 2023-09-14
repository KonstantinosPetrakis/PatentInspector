<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const emailElement = ref(null);
const email = ref("");
const errors = ref([]);
const router = useRouter();

const requestResetPassword = () => {};

onMounted(() => emailElement.value.focus());
</script>

<template>
    <form
        class="d-flex flex-column align-items-center mt-4 mx-auto col-lg-6 col-12 border rounded shadow p-2 text-center"
    >
        <h2 class="h2">PatentAnalyzer</h2>
        <p>
            Enter your email address bellow and we will send you an
            one-time-password to reset your password.
        </p>
        <div
            v-for="error of errors"
            class="alert alert-danger alert-dismissible"
        >
            {{ error }}
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="alert"
            ></button>
        </div>
        <label>
            Email
            <input
                class="form-control"
                type="email"
                v-model="email"
                ref="emailElement"
            />
        </label>
        <button
            class="btn btn-secondary btn mt-2"
            @click.prevent="requestResetPassword"
        >
            Request reset password
        </button>
    </form>
</template>

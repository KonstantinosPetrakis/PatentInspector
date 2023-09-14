<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import VOtpInput from "vue3-otp-input";

const token = ref("");
const newPassword = ref("");
const confirmNewPassword = ref("");
const errors = ref([]);
const router = useRouter();

const resetPassword = () => {};
</script>

<template>
    <form
        class="d-flex flex-column align-items-center mt-4 mx-auto col-lg-6 col-12 border rounded shadow p-2 text-center"
    >
        <h2 class="h2">PatentAnalyzer</h2>
        <p>
            Enter the one-time-password you received in your email and a new
            password to reset your password.
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
        <label class="my-2">
            One Time Password
            <VOtpInput
                class="otp-input"
                value=""
                :should-auto-focus="true"
                v-model="token"
                :num-inputs="8"
                input-type="letter-numeric"
                separator="&nbsp-&nbsp"
            />
        </label>
        <label class="my-2">
            New Password
            <input
                class="form-control"
                type="password"
                v-model="newPassword"
                placeholder="mynewpassword123"
            />
        </label>
        <label class="my-2">
            Confirm New Password
            <input
                class="form-control"
                type="password"
                input-type="text"
                v-model="confirmNewPassword"
                placeholder="mynewpassword123"
            />
        </label>
        <button class="btn btn-secondary" @click.prevent="resetPassword">
            Reset password
        </button>
    </form>
</template>

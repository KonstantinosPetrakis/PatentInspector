<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import OTPInput from "../components/form-widgets/OTPInput.vue";
import { getCompleteUrl } from "../utils";

const token = ref("");
const newPassword = ref("");
const confirmNewPassword = ref("");
const errors = ref([]);
const router = useRouter();

const resetPassword = async () => {
    if (!token.value || !newPassword.value || !confirmNewPassword.value) {
        errors.value.push("Please fill in all fields.");
        return;
    }

    if (newPassword.value !== confirmNewPassword.value) {
        errors.value.push("Passwords do not match.");
        return;
    }

    if (token.value.length !== 8) {
        errors.value.push("Invalid token.");
        return;
    }

    const response = await fetch(getCompleteUrl("/user/reset_password"), {
        method: "POST",
        body: JSON.stringify({
            token: token.value,
            new_password: newPassword.value,
        }),
        headers: { "Content-Type": "application/json" },
    });

    if (response.ok) router.push({ name: "login" });
    else errors.value.push((await response.json()).error);
};
</script>

<template>
    <form
        @keydown.enter.prevent="resetPassword"
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
            <OTPInput v-model="token" />
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

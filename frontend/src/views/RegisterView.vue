<script setup>
import { ref, reactive, onMounted } from "vue";
import router from "../router";
import { getCompleteUrl } from "../utils";

const email = ref("");
const password = ref("");
const passwordConfirm = ref("");
const emailElement = ref(null);
const errors = reactive([]);

onMounted(() => emailElement.value.focus());

const register = async () => {
    errors.length = 0;
    if (email.value === "" || !email.value.includes("@"))
        errors.push("Valid email is required");
    if (password.value === "") errors.push("Password is required");
    if (password.value !== passwordConfirm.value)
        errors.push("Passwords do not match");
    if (errors.length > 0) return;

    const result = await fetch(getCompleteUrl("/user"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.value, password: password.value }),
    });

    if (result.status == 400) {
        const data = await result.json();
        for (const fieldErrors of Object.values(data)) {
            for (const error of fieldErrors) {
                errors.push(error);
            }
        }
    } else router.push({ name: "login" });
};
</script>

<template>
    <div class="small-box text-center">
        <h1 class="h2">PatentAnalyzer</h1>
        <h3 class="h4">Register</h3>
        <div class="errors">
            <div
                class="alert alert-danger"
                v-for="(error, i) in errors"
                :key="error"
            >
                {{ error }}
                <button class="btn-close" @click="() => errors.pop(i)"></button>
            </div>
        </div>
        <form>
            <div class="form-group my-2">
                <input
                    type="email"
                    class="form-control"
                    placeholder="Email"
                    v-model="email"
                    ref="emailElement"
                />
            </div>
            <div class="form-group my-2">
                <input
                    type="password"
                    class="form-control"
                    placeholder="Password"
                    v-model="password"
                />
            </div>
            <div class="form-group my-2">
                <input
                    type="password"
                    class="form-control"
                    placeholder="Password confirmation"
                    v-model="passwordConfirm"
                />
            </div>
            <button
                type="submit"
                class="btn btn-secondary"
                @click.prevent="register"
            >
                Register
            </button>
        </form>
    </div>
</template>

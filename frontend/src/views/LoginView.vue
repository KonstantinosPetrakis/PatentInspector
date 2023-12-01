<script setup>
import { ref, reactive, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { logIn, getCompleteUrl } from "../utils";

const email = ref("");
const password = ref("");
const emailElement = ref(null);
const errors = reactive([]);

onMounted(() => emailElement.value.focus());

const login = async () => {
    errors.length = 0;
    if (email.value === "" || !email.value.includes("@"))
        errors.push("Valid email is required");
    if (password.value === "") errors.push("Password is required");
    if (errors.length > 0) return;

    const result = await fetch(getCompleteUrl("/user/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.value, password: password.value }),
    });

    const data = await result.json();
    if (result.status == 400) {
        errors.push(data.error);
        if (data.error.includes("password")) password.value = "";
    } else logIn(data.token, data.email);
};
</script>

<template>
    <div class="small-box text-center">
        <h1 class="h2">PatentInspector</h1>
        <h3 class="h4">Login</h3>
        <form>
            <div class="errors">
                <div
                    class="alert alert-danger alert-dismissible"
                    v-for="error in errors"
                    :key="error"
                >
                    {{ error }}
                    <button
                        type="button"
                        class="btn-close"
                        data-bs-dismiss="alert"
                    ></button>
                </div>
            </div>
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
            <button
                type="submit"
                class="mx-2 btn btn-secondary"
                @click.prevent="login"
            >
                Login
            </button>
            <router-link
                class="mx-2 btn btn-secondary"
                :to="{ name: 'requestResetPassword' }"
            >
                Reset password
            </router-link>
        </form>
    </div>
</template>

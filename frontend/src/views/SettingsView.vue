<script setup>
import { reactive, ref, onMounted } from "vue";
import { authFetch, getUserData, setUserEmail } from "../utils";

const messages = reactive([]);
const emailForm = reactive({
    newEmail: "",
    password: "",
});
const passwordForm = reactive({
    currentPassword: "",
    newPassword: "",
    confirmNewPassword: "",
});
const receiveEmails = ref(true);

const changeEmail = async () => {
    if (emailForm.newEmail === "") {
        messages.push({
            type: "danger",
            text: "Please enter a new email address.",
        });
        return;
    }
    if (emailForm.password === "") {
        messages.push({
            type: "danger",
            text: "Please enter your password.",
        });
        return;
    }
    const response = await authFetch("/user/update_email", {
        method: "POST",
        body: JSON.stringify({
            new_email: emailForm.newEmail,
            password: emailForm.password,
        }),
    });

    if (response.ok) {
        messages.push({
            type: "success",
            text: "Your email has been updated successfully.",
        });
        setUserEmail(emailForm.newEmail);
        emailForm.newEmail = "";
        emailForm.password = "";
    } else {
        const errors = await response.json();
        for (let message of Object.values(errors)) {
            messages.push({
                type: "danger",
                text: Array.isArray(message) ? message[0] : message,
            });
        }
    }
};

const changePassword = async () => {
    if (passwordForm.currentPassword === "") {
        messages.push({
            type: "danger",
            text: "Please enter your current password.",
        });
        return;
    }
    if (passwordForm.newPassword === "") {
        messages.push({
            type: "danger",
            text: "Please enter a new password.",
        });
        return;
    }
    if (passwordForm.confirmNewPassword === "") {
        messages.push({
            type: "danger",
            text: "Please confirm your new password.",
        });
        return;
    }
    if (passwordForm.newPassword !== passwordForm.confirmNewPassword) {
        messages.push({
            type: "danger",
            text: "Your new password and confirmation do not match.",
        });
        return;
    }
    const response = await authFetch("/user/update_password", {
        method: "POST",
        body: JSON.stringify({
            old_password: passwordForm.currentPassword,
            new_password: passwordForm.newPassword,
        }),
    });

    if (response.ok) {
        messages.push({
            type: "success",
            text: "Your password has been updated successfully.",
        });
        passwordForm.currentPassword = "";
        passwordForm.newPassword = "";
        passwordForm.confirmNewPassword = "";
    } else {
        const data = await response.json();
        messages.push({
            type: "danger",
            text: data.error,
        });
    }
};

const changeReceiveEmails = async () => {
    const response = await authFetch("/user/update_wants_emails", {
        method: "POST",
        body: JSON.stringify({
            wants_emails: receiveEmails.value,
        }),
    });

    if (response.ok) {
        messages.push({
            type: "success",
            text: "Your email preference has been updated successfully.",
        });
    } else {
        messages.push({
            type: "danger",
            text: "Your email preference could not be updated.",
        });
        console.error(await response.json());
    }
};

onMounted(
    async () => (receiveEmails.value = (await getUserData()).wants_emails)
);
</script>

<template>
    <div class="container">
        <h1 class="h1 text-center">PatentInspector</h1>
        <h3 class="h3 text-center">Settings</h3>
        <div
            v-for="message of messages"
            :class="`alert alert-${message.type} alert-dismissible col-lg-6 col-12 mx-auto`"
        >
            {{ message.text }}
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="alert"
            ></button>
        </div>
        <div class="row border col-lg-6 col-12 my-3 mx-auto rounded shadow">
            <form class="p-3 d-flex flex-column justify-content-center">
                <h4 class="h-4">Change email</h4>
                <label>
                    New email:
                    <input
                        class="form-control my-1"
                        type="email"
                        v-model="emailForm.newEmail"
                        placeholder="mynewmail@example.com"
                    />
                    Password:
                    <input
                        class="form-control my-1"
                        type="password"
                        v-model="emailForm.password"
                        placeholder="mypassword123"
                    />
                </label>
                <button
                    class="btn btn-secondary mt-3"
                    @click.prevent="changeEmail"
                >
                    Change email
                </button>
            </form>
            <hr />
            <form class="p-3 d-flex flex-column justify-content-center">
                <h4 class="h4">Change password</h4>
                <label>
                    Current Password:
                    <input
                        class="form-control my-1"
                        type="password"
                        v-model="passwordForm.currentPassword"
                        placeholder="mypassword123"
                    />
                    New Password:
                    <input
                        class="form-control my-1"
                        type="password"
                        v-model="passwordForm.newPassword"
                        placeholder="mynewpassword123"
                    />
                    Confirm New Password:
                    <input
                        class="form-control my-1"
                        type="password"
                        v-model="passwordForm.confirmNewPassword"
                        placeholder="mynewpassword123"
                    />
                </label>
                <button
                    class="btn btn-secondary mt-3"
                    @click.prevent="changePassword"
                >
                    Change password
                </button>
            </form>
            <hr />
            <form class="p-3 d-flex flex-column justify-content-center">
                <h4 class="h4">Receive emails</h4>
                <label>
                    <input
                        class="form-check-input"
                        type="checkbox"
                        v-model="receiveEmails"
                    />
                    Receive emails when my reports are ready
                </label>
                <button
                    class="btn btn-secondary mt-3"
                    @click.prevent="changeReceiveEmails"
                >
                    Update my mail preference
                </button>
            </form>
        </div>
    </div>
</template>

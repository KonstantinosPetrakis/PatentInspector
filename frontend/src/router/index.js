import { createRouter, createWebHistory } from "vue-router";
import IndexView from "../views/IndexView.vue";
import { isLoggedIn } from "../utils";

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/",
            name: "home",
            component: IndexView,
        },
        {
            path: "/login",
            name: "login",
            component: () => import("../views/LoginView.vue"),
        },
        {
            path: "/register",
            name: "register",
            component: () => import("../views/RegisterView.vue"),
        },
        {
            path: "/request-reset-password",
            name: "requestResetPassword",
            component: () => import("../views/RequestResetPasswordView.vue"),
        },
        {
            path: "/reset-password",
            name: "resetPassword",
            component: () => import("../views/ResetPasswordView.vue"),
        },
        {
            path: "/settings",
            name: "settings",
            component: () => import("../views/SettingsView.vue"),
        },
        {
            path: "/create-report",
            name: "createReport",
            component: () => import("../views/CreateReportView.vue"),
        },
        {
            path: "/report/:id",
            name: "report",
            component: () => import("../views/SeeReportView.vue"),
            props: (route) => ({
                id: route.params.id,
                page: route.query.page || 1,
            }),
        },
        {
            path: "/list-reports/:page?",
            name: "listReports",
            component: () => import("../views/ListReportsView.vue"),
            props: (route) => ({ page: route.params.page || 1 }),
        },
        {
            path: "/not-found",
            name: "notFound",
            component: () => import("../views/NotFoundView.vue"),
        },
        {
            path: "/:pathMatch(.*)*",
            name: "notFound",
            component: () => import("../views/NotFoundView.vue"),
        },
    ],
});

const authViewRouteNames = [
    "login",
    "register",
    "resetPassword",
    "requestResetPassword",
];
const notRestrictedViewRouteNames = ["home", ...authViewRouteNames];
router.beforeEach((to) => {
    const loggedIn = isLoggedIn();
    const restrictedView = !notRestrictedViewRouteNames.includes(to.name);
    const authView = authViewRouteNames.includes(to.name);

    if (!loggedIn && restrictedView) return { name: "login" };
    if (loggedIn && authView) return { name: "home" };
});

export default router;

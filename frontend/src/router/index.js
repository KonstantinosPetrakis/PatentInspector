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
            path: "/create-report",
            name: "createReport",
            component: () => import("../views/CreateReportView.vue"),
        },
        {
            path: "/report/:id",
            name: "report",
            component: () => import("../views/SeeReportView.vue"),
            props: true,
        },
        {
            path: "/list-reports/:page?",
            name: "listReports",
            component: () => import("../views/ListReportsView.vue"),
            props: true,
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

router.beforeEach((to) => {
    const loggedIn = isLoggedIn();
    const restrictedView = !["home", "login", "register"].includes(to.name);
    const authView = ["login", "register"].includes(to.name);

    if (!loggedIn && restrictedView) return { name: "login" };
    if (loggedIn && authView) return { name: "home" };
});

export default router;

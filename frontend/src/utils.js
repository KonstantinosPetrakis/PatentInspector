import router from "./router";
import { apiUrl } from "./main";

export const isLoggedIn = () => !!localStorage.getItem("token");

export const logIn = (token, email) => {
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);
    window.dispatchEvent(new Event("logIn"));
    router.push({ name: "home" });
};

export const logOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    window.dispatchEvent(new Event("logOut"));
    router.push({ name: "login" });
};

export const getCompleteUrl = (url) => `${apiUrl}${url}`;

export const authFetch = (url, options) => {
    if (!url.includes(apiUrl)) url = getCompleteUrl(url);
    const headers = {
        Authorization: `Token ${localStorage.getItem("token")}`,
        "Content-Type": "application/json",
    };
    return fetch(url, { headers, ...options });
};

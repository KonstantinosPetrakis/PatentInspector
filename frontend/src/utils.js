import router from "./router";
import { apiUrl, debug } from "./main";

export const isLoggedIn = () => !!localStorage.getItem("token");

export const logIn = (token, email) => {
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);
    window.dispatchEvent(new Event("logIn"));
    router.push({ name: "home" });
};

export const logOut = () => {
    if (!confirm("Are you sure you want to log out?")) return;
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    window.dispatchEvent(new Event("logOut"));
    router.push({ name: "login" });
};

export const getUserData = async () => {
    const response = await authFetch("/user/get_data");
    const data = await response.json();
    return data;
};

export const getUserEmail = () => localStorage.getItem("email");

export const setUserEmail = (email) => localStorage.setItem("email", email);

export const getCompleteUrl = (url) =>
    `${debug ? "http" : "https"}://${apiUrl}${url}`;

export const authFetch = (url, options) => {
    if (!url.includes(apiUrl)) url = getCompleteUrl(url);
    const headers = {
        Authorization: `Token ${localStorage.getItem("token")}`,
        "Content-Type": "application/json",
    };
    return fetch(url, { headers, ...options });
};

export const getColorMode = () =>
    document.querySelector("html").getAttribute("data-bs-theme");

export const dateTimeToString = (
    dateTime,
    nullMessage = "In the foreseeable future"
) => (dateTime ? new Date(dateTime).toLocaleString() : nullMessage);

export const dateToString = (date, nullMessage) =>
    date ? new Date(date).toLocaleDateString() : nullMessage;

export const dateTimeDiff = (date1, date2) => {
    if (!date1 || !date2) return "N/A";

    const padNumber = (number) => (number < 10 ? `0${number}` : number);
    let diff = Math.abs(new Date(date1) - new Date(date2)) / 1000;

    const days = Math.floor(diff / 86400);
    diff -= days * 86400;

    const hours = Math.floor(diff / 3600) % 24;
    diff -= hours * 3600;

    const minutes = Math.floor(diff / 60) % 60;
    diff -= minutes * 60;

    const seconds = Math.floor(diff % 60);

    return `${padNumber(hours)}:${padNumber(minutes)}:${padNumber(seconds)}`;
};

export const createAlert = (type, message) => {
    const body = document.querySelector("body");
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} position-fixed top-0 mt-5 start-50 translate-middle-x`;
    alert.textContent = message;
    body.appendChild(alert);
    setTimeout(() => alert.remove(), 1000);
};

export const queryGooglePatents = (query) =>
    window
        .open(`https://patents.google.com/?${query.replace(",", "")}`, "_blank")
        .focus();

export const sendToGooglePatents = (patentCode) =>
    window
        .open(`https://patents.google.com/patent/${patentCode}`, "_blank")
        .focus();

// Colors used for the charts
export const colors = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
];

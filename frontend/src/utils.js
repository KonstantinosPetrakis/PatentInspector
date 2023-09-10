import { startCase } from "lodash";
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
    if (!confirm("Are you sure you want to log out?")) return;
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

export const dateTimeToString = (
    dateTime,
    nullMessage = "In the foreseeable future"
) => (dateTime ? new Date(dateTime).toLocaleString() : nullMessage);

// Not so proud of this one but gets the job done.
export const reportToSubmittedFilters = (report) => {
    if (!report) return report;

    // Remove unnecessary attributes
    const notNeededAttrs = [
        "id",
        "datetime_created",
        "datetime_analysis_started",
        "datetime_analysis_ended",
        "user",
        "results",
    ];
    for (let attr of notNeededAttrs) delete report[attr];

    // Remove attributes if they have default values
    // and transform the others to a user friendly string
    for (let attr of Object.keys(report)) {
        // Remove null, empty array and default range values
        let data = report[attr];

        if (data === null || Object.keys(data).length === 0)
            delete report[attr];
        else if (Array.isArray(data) && data.length == 0) delete report[attr];
        else if (
            typeof data == "object" &&
            ((data.lower == 0 && data.upper == 100) ||
                (data.lower === null && data.upper === null))
        )
            delete report[attr];
        // Cast date and count ranges to a user friendly string
        else if (
            (attr.endsWith("date") || attr.endsWith("count")) &&
            typeof data == "object" &&
            data != null
        ) {
            report[attr] = `${data.lower || "-∞"} - ${data.upper || "∞"}`;
        }

        // Cast lists to a user friendly string
        else if (Array.isArray(data) && data.length > 0)
            report[attr] = data.join(", ");
        //  Cast object to a user friendly string
        else if (typeof data == "object" && data != null) {
            let strRepresentation = "";
            for (let [key, value] of Object.entries(data))
                strRepresentation += `${key}: ${value}, `;
            report[attr] = strRepresentation.slice(0, -2);
        }
    }

    // Remove default keywords logic and transform it to a user friendly string
    if (report.patent_keywords_logic == "|") report.patent_keywords_logic = "OR";
    else delete report.patent_keywords_logic;

    // Make attrs more user friendly
    for (let attr of Object.keys(report)) {
        report[startCase(attr)] = report[attr];
        delete report[attr];
    }

    return report;
};

export const createAlert = (type, message) => {
    const body = document.querySelector("body");
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} position-fixed top-0 mt-5 start-50 translate-middle-x`;
    alert.textContent = message;
    body.appendChild(alert);
    setTimeout(() => alert.remove(), 1000);
};

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

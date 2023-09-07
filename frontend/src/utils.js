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
        "datetimeCreated",
        "datetimeAnalysisStarted",
        "datetimeAnalysisEnded",
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
        
        else if (Array.isArray(data) && data.length == 0) 
            delete report[attr];
        
        else if (
            typeof data == "object" &&
            ((data.lower == 0 && data.upper == 100) ||
                (data.lower === null && data.upper === null))
        )
            delete report[attr];
        
        // Cast date and count ranges to a user friendly string
        else if (
            (attr.endsWith("Date") || attr.endsWith("Count")) &&
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
    if (report.patentKeywordsLogic == "|") report.patentKeywordsLogic = "OR";
    else delete report.patentKeywordsLogic;

    // Make attrs more user friendly
    for (let attr of Object.keys(report)) {
        report[startCase(attr)] = report[attr];
        delete report[attr];
    }
    
    return report;
};

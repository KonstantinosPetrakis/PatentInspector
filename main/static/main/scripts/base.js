/**
 * This function switches the Bootstrap theme between dark and light.
 */
function switchBootstrapTheme() {
    const html = document.querySelector("html");
    const changedTheme = html.getAttribute("data-bs-theme") == "dark" ? "light" : "dark";
    html.setAttribute("data-bs-theme", changedTheme);
    localStorage.setItem("theme", changedTheme);
}


/**
 * This function throttles a function.
 * Code copied from https://stackoverflow.com/a/27078401
 * @param {Function} callback the function to throttle. 
 * @param {Number} limit the time limit in milliseconds to throttle for.
 * @returns the throttled function.
 */
function throttle (callback, limit) {
    var waiting = false;                      
    return function () {                      
        if (!waiting) {                      
            callback.apply(this, arguments);  
            waiting = true;                   
            setTimeout(function () {          
                waiting = false;             
            }, limit);
        }
    }
}

document.querySelector("html").setAttribute("data-bs-theme", localStorage.getItem("theme") || "dark");
addEventListener("DOMContentLoaded", () => {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {html: true}))

    const sliderWrappers = document.querySelectorAll(".min-max-slider");
    for (const sliderWrapper of sliderWrappers) 
        initializeMinMaxSlider(sliderWrapper);

    for (const hiddenElement of document.querySelectorAll(".tri-state-checkbox")) 
        initializeTriStateCheckbox(hiddenElement);

    for (const keywordInput of document.querySelectorAll(".keyword-input")) 
        new Choices(keywordInput, {allowHTML: true, removeItemButton: true, duplicateItemsAllowed: false});

    for (const choiceKeywordInput of document.querySelectorAll(".choice-keywords-input")) 
        initializeChoiceKeywordsInputField(choiceKeywordInput);
});

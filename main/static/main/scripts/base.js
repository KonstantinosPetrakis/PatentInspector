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
 * This function debounces a function (delays its execution until a certain time has passed without it being called)
 * @param {Function} func the function to debounce
 * @param {Number} timeout the milliseconds to wait before executing the function.
 * @returns The new function that has been debounced.
 */
function debounce(func, timeout = 500){
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
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

    for (const radiusInput of document.querySelectorAll(".radius-input")) 
        initializeRadiusInput(radiusInput);

    for (const pointMap of document.querySelectorAll(".point-map")) 
        initializePointMap(pointMap);

    for (const switchInput of document.querySelectorAll(".switch-input")) 
        initializeSwitchInput(switchInput);
    
    for (const inPageNavTab of document.querySelectorAll(".in-page-nav-tab")) 
        initializeInPageNavTab(inPageNavTab);
});

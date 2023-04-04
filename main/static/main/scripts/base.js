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
 * This function initializes a tri-state checkbox.
 * @param {Element} hiddenElement the hidden element that stores the value of the checkbox.
 */
function initializeTriStateCheckbox(hiddenElement) {
    // Create checkbox
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "form-check-input";
    checkbox.checked = hiddenElement.value == "True";
    checkbox.indeterminate = hiddenElement.value == "";

    // Change default behavior to None -> True -> False -> None and update hidden element
    checkbox.addEventListener("change", () => {
        switch (hiddenElement.value) {
            case "":
                checkbox.checked = true;
                hiddenElement.value = "True";
                break;
            case "True":
                checkbox.checked = false;
                hiddenElement.value = "False";
                break;
            case "False":
                checkbox.checked = false;
                checkbox.indeterminate = true;
                hiddenElement.value = "";
                break;
        }
    });
    hiddenElement.insertAdjacentElement("afterend", checkbox);
}


/**
 * This function initializes a slider with two inputs.
 * @param {Element} sliderWrapper  the wrapper element that contains the slider and the inputs.
 */
function initializeMinMaxSlider(sliderWrapper) {
    const slider = sliderWrapper.querySelector(".slider");
    const inputs = [sliderWrapper.querySelector(".min-input"), sliderWrapper.querySelector(".max-input")]
    const min = parseInt(sliderWrapper.getAttribute("data-min"));
    const max = parseInt(sliderWrapper.getAttribute("data-max"));
    noUiSlider.create(slider, { start: [min, max], step: 1, range: {min, max} });
    slider.noUiSlider.on("update", (values, handle) => inputs[handle].value = parseInt(values[handle]));
    inputs.forEach((input, handle) => input.addEventListener("change", () => slider.noUiSlider.setHandle(handle, input.value)));
}

/**
 * This function initializes a choice keyword input field.
 * @param {Element} choiceKeywordInput the hidden input field that stores the keywords.
 */
function initializeChoiceKeywordsInputField(choiceKeywordInput) {
    async function searchKeywords(event) {
        if (event.detail.value.length < minQueryLength) return; 
        const noQueryLimit = event.detail.value.length == 0;
        const response = await fetch(`${url}${noQueryLimit ? '' : '/'}${event.detail.value}`);
        const data = await response.json();
        data.map(item => item.representation = `${item.section} - ${item.title}`);
        choiceKeywords.setChoices(data, "section", "representation", noQueryLimit)
    }

    const choiceKeywords = new Choices(choiceKeywordInput, {allowHTML: true, removeItemButton: true, duplicateItemsAllowed: false});
    const url = choiceKeywordInput.getAttribute("data-url");
    const minQueryLength = parseInt(choiceKeywordInput.getAttribute("data-minQueryLength"));
    choiceKeywordInput.addEventListener("search", searchKeywords);

    // If there is no query limit, trigger a search event to get all keywords and don't
    // listen to search events anymore.
    if (minQueryLength == 0) {
        choiceKeywords.passedElement.triggerEvent("search", {value: "", programmatic: true});
        choiceKeywordInput.removeEventListener("search", searchKeywords)
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

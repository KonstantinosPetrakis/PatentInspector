/**
 * @file Contains the widget initialization code for widgets used in the main app. 
*/


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
async function initializeChoiceKeywordsInputField(choiceKeywordInput) {
    /**
     * This function searches for keywords and updates the available choices.
     * @param {string} value the value to search for. 
     */
    async function searchKeywords(value="") {
        if (value.length < minQueryLength) return; 
        const response = await fetch(`${url}${noQueryLimit ? '' : '/'}${value}`);
        const data = await response.json();
        formatData(data);
        choiceKeywords.setChoices(data, "search_id", "representation", true)
    }

    /**
     * This function searches for keywords and updates the available choices.
     * @param {Event} event the event choice.js triggers when the user searches for a choice.
     */
    async function searchKeywordsByEvent(event) { await searchKeywords(event.detail.value) }
    const searchKeywordsByEventThrottled = throttle(searchKeywordsByEvent, 500); 


    async function populateChoices(values) {
        // Make a POST request via fetch
        const response = await fetch(`${url}?ids=${encodeURIComponent(JSON.stringify(values))}`, {method: "GET", headers: {"Content-Type": "application/json"}});
        const data = await response.json();
        formatData(data);
        choiceKeywords.setChoices(data, "search_id", "representation", false)
    }

    /**
     * This function formats the data to be displayed in the choices.
     * @param {Array<Object>} data the data returned by the API to be formatted.  
     */
    function formatData(data) {
        if (data == null || data.length == 0) return;
        if (data[0].search_title == undefined)
            data.map(item => item.representation = `${item.search_id}`);
        else
            data.map(item => item.representation = `${item.search_id} - ${item.search_title}`);
    }

    const url = choiceKeywordInput.getAttribute("data-url");
    const minQueryLength = parseInt(choiceKeywordInput.getAttribute("data-minQueryLength"));
    const noQueryLimit = minQueryLength == 0;

    // Choices need a multiple select element to work, but we can't afford to have one 
    // in the backend because choices are fetched via JS and default backend validation 
    // wouldn't work. So we create a fake multiple select element and we copy its value to 
    // a comma separated string in the hidden input field.
    const fakeSelect = document.createElement("select");
    fakeSelect.multiple = true;
    choiceKeywordInput.insertAdjacentElement("afterend", fakeSelect);

    const choiceKeywords = new Choices(fakeSelect, {allowHTML: true, removeItemButton: true, duplicateItemsAllowed: false, shouldSort: false, searchFields: ["representation"], searchResultLimit: 10000});
    fakeSelect.addEventListener("search", searchKeywordsByEventThrottled);

    // If there is no query limit, trigger a search event to get all keywords and don't
    // listen to search events anymore.
    if (noQueryLimit) {
        fakeSelect.removeEventListener("search", searchKeywordsByEventThrottled);
        await searchKeywords();
    }
    
    // If hidden input field has a value, add the corresponding choices
    if (choiceKeywordInput.value) {
        const choices = choiceKeywordInput.value.split(",");
        const alreadyExistingChoices = choiceKeywords._currentState.choices.map(choice => choice.value);
        
        // Fetch choices only if there are not already fetched (there wasn't a query limit)
        if (choices.some(choice => !alreadyExistingChoices.includes(choice))) 
            await populateChoices(choices);

        // Add choices
        choices.forEach(choice => choiceKeywords.setChoiceByValue(choice));
    }

    // Copy the value of the fake select to the hidden input field
    fakeSelect.addEventListener("change", () => {
        choiceKeywordInput.value = Array.from(fakeSelect.selectedOptions).map(option => option.value).join(",")
    });
}

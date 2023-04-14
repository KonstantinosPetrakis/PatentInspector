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
    const inputs = [sliderWrapper.querySelector(".min-input"), sliderWrapper.querySelector(".max-input")];
    
    const min = parseInt(sliderWrapper.getAttribute("data-min"));
    const max = parseInt(sliderWrapper.getAttribute("data-max"));
    const minValue = inputs[0].value == "" ? min : inputs[0].value;
    const maxValue = inputs[1].value == "" ? max : inputs[1].value;
    noUiSlider.create(slider, { start: [minValue, maxValue], step: 1, range: { min, max } });
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
    async function searchKeywords(value = "") {
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
    const searchKeywordsByEventDebounced = debounce(searchKeywordsByEvent, 500);

    /**
     * This function populates the choices with the given values.
     * It's used to add choices that were already selected when the page was loaded (e.g. when the form is invalid).
     * @param {Array<String>} values the IDs of the values to populate the choices with.
     */
    async function populateChoices(values) {
        // Make a POST request via fetch
        const response = await fetch(`${url}?ids=${encodeURIComponent(JSON.stringify(values))}`, { method: "GET", headers: { "Content-Type": "application/json" } });
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

    const choiceKeywords = new Choices(fakeSelect, { allowHTML: true, removeItemButton: true, duplicateItemsAllowed: false, shouldSort: false, searchResultLimit: 10000 });
    fakeSelect.addEventListener("search", searchKeywordsByEventDebounced);

    // If there is no query limit, trigger a search event to get all keywords and don't
    // listen to search events anymore.
    if (noQueryLimit) {
        fakeSelect.removeEventListener("search", searchKeywordsByEventDebounced);
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


/**
 * This function initializes a radius field.
 * @param {Element} radiusInput the hidden input field that stores the radius.
 */
function initializeRadiusInput(radiusInput) {
    // Create a div to contain the map
    const mapElement = document.createElement("div");
    mapElement.className = "map";
    mapElement.id = radiusInput.getAttribute("name");
    radiusInput.insertAdjacentElement("afterend", mapElement);

    // Create the map and center it on the US
    const map = L.map(mapElement.id).setView([37.8, -96], 3);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Create a new layer group to store the drawn items
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    var drawControl = new L.Control.Draw({
        draw: {
            polygon: false,
            marker: false,
            polyline: false,
            rectangle: false,
            circlemarker: false
        },
        edit: { featureGroup: drawnItems}
    });
    map.addControl(drawControl);

    // When a circle is drawn, add a marker at its center and store that lat, lng and
    // radius in the hidden input field
    map.on(L.Draw.Event.CREATED, (e) => {
        const circle = e.layer;
        const circleCoords = circle.getLatLng();
        const circleRadius = circle.getRadius();
        drawnItems.clearLayers(); // clear old circle
        drawnItems.addLayer(circle); // Add the circle
        drawnItems.addLayer(L.marker(circleCoords)); // Add a marker in the center
        radiusInput.value = `${circleCoords.lat},${circleCoords.lng},${circleRadius}`;
    });

    // Fix bootstrap accordion mess with leaflet map
    const accordion = mapElement.closest(".accordion");
    if (accordion) accordion.addEventListener("shown.bs.collapse", () => map.invalidateSize());
}

/**
 * This function initializes a map with already pinned points.
 * @param {Element} pointMapElement the html element that will contain the map.
 */
function initializePointMap(pointMapElement) {
    const circle = pointMapElement.getAttribute("data-circle").split(",");
    const points = pointMapElement.getAttribute("data-points").split(",");

    pointMapElement.id = Date.now() * Math.floor(Math.random() * 10000);
    pointMapElement.className = "map";
    
    const map = L.map(pointMapElement.id).setView([+circle[0], +circle[1]], 3.5);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    L.circle([+circle[0], +circle[1]], +circle[2]).addTo(map);
    for (let point of points) {
        point = point.split("|");
        console.log([+point[0], +point[1]])
        L.marker([+point[0], +point[1]]).addTo(map); // marker doesn't work 
    }
}
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
    inputs.forEach((input, handle) => input.addEventListener("change", 
        () => slider.noUiSlider.setHandle(handle, input.value)));  
}


/**
 * This function initializes a choice keyword input field.
 * @param {Element} choiceKeywordInput the hidden input field that stores the keywords.
 */
async function initializeChoiceKeywordsInputField(choiceKeywordInput) {
    /**
     * This function is used to put the options in the choices element.
     * @param {Array<Object|String>} data the data returned from the API. 
     */
    function putChoicesFromData(data) {
        if (!Array.isArray(data) || !data.length) return;

        // If the array contains objects, the id and the representation are the 1st and 2nd key
        if (typeof data[0] === 'object') {
            const [id, repr] = Object.keys(data[0]);
            // The id is the 1st key, the representation is the 2nd
            data.forEach(o => {
                delete Object.assign(o, {["id"]: o[id] })[id];
                delete Object.assign(o, {["repr"]: `${o["id"]} - ${o[repr]}` })[repr];
            });
        }
        // If the array contains strings, the id and the representation are the same
        else data = data.map(val => ({ "id": val, "repr": val }));
        choiceKeywords.setChoices(data, "id", "repr", true);
    }

    /**
     * This function is used to populate the choices element with the results of a query.
     * @param {String} value the query that will be used for filtering in the backend.
     * @returns {Promise<Array<Object|String>>} the data returned from the API.
     */
    async function populateChoicesFromQuery(value = "") {
        const response = await fetch(`${queryURL}&query=${encodeURIComponent(value)}`);
        const data = await response.json();
        putChoicesFromData(data);
        return data;
    }

    /**
     * This function is used to populate the choices element by asking the backend more info about the
     * given values.
     * @param {Array} values the values that will be used for filtering in the backend.
     * @returns  {Promise<Array<Object|String>>} the data returned from the API.
     */
    async function populateChoicesFromValues(values) {
        const response = await fetch(`${exactURL}&exact-values=${encodeURIComponent(values.join("~#"))}`);
        const data = await response.json();
        putChoicesFromData(data);
        return data;
    }

    const populateChoicesFromQueryEventDebounced = debounce(
        async (event) => await populateChoicesFromQuery(event.detail.value), 500);

    const exactURL = choiceKeywordInput.getAttribute("data-exact-url");
    const queryURL = choiceKeywordInput.getAttribute("data-query-url");

    // Create a fake multiple select element and copy its value to 
    // a '~#' separated string in the hidden input field.
    const fakeSelect = document.createElement("select");
    fakeSelect.multiple = true;
    choiceKeywordInput.insertAdjacentElement("afterend", fakeSelect);

    const choiceKeywords = new Choices(fakeSelect, { allowHTML: true, removeItemButton: true,
        duplicateItemsAllowed: false, shouldSort: false, searchResultLimit: 10000 });
    fakeSelect.addEventListener("search", populateChoicesFromQueryEventDebounced);

    // Try to populate choices immediately, if results are found, remove the event listener.
    // Results could not be found if there's a minimum query length required by the backend.
    const data = await populateChoicesFromQuery();
    if (Array.isArray(data) && data.length) 
        fakeSelect.removeEventListener("search", populateChoicesFromQueryEventDebounced);

    // If hidden input field has a value, add the corresponding choices
    // The values could be filled by the backend if the form is invalid or for prefilling
    if (choiceKeywordInput.value) {
        const choices = choiceKeywordInput.value.split("~#");
        const alreadyExistingChoices = choiceKeywords._currentState.choices.map(choice => choice.value);
        // Fetch choices only if there are not already fetched (there wasn't a query limit)
        if (choices.some(choice => !alreadyExistingChoices.includes(choice))) 
            await populateChoicesFromValues(choices);
        
        // Select choices in the fake select
        for (let choice of choices) choiceKeywords.setChoiceByValue(choice);
    }

    // Copy the value of the fake select to the hidden input field
    fakeSelect.addEventListener("change", () => {
        choiceKeywordInput.value = Array.from(fakeSelect.selectedOptions).map(
            option => option.value).join("~#");
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

    // When a circle is deleted clear the hidden input field
    map.on(L.Draw.Event.DELETED, () => radiusInput.value = "");

    // Fix bootstrap accordion mess with leaflet map
    const accordion = mapElement.closest(".accordion");
    if (accordion) accordion.addEventListener("shown.bs.collapse", () => map.invalidateSize());

    // If the hidden input field has a value, add the corresponding circle
    if (radiusInput.value) {
        const coords = radiusInput.value.split(",").map(val => +val);
        const circle = L.circle([coords[0], coords[1]], { radius: coords[2] });
        drawnItems.addLayer(circle);
        drawnItems.addLayer(L.marker([coords[0], coords[1]]));
    }
}

/**
 * This function initializes a map with already pinned points.
 * @param {Element} pointMapElement the html element that will contain the map.
 */
function initializePointMap(pointMapElement) {
    const circle = pointMapElement.getAttribute("data-circle").split(",").filter(val => val != "");
    const points = pointMapElement.getAttribute("data-points").split(",").filter(val => val != "");
    pointMapElement.id = Date.now() * Math.floor(Math.random() * 10000);
    pointMapElement.className = "map";
    if (circle.length) var map = L.map(pointMapElement.id).setView([+circle[0], +circle[1]], 3.5);
    else var map = L.map(pointMapElement.id).setView([37.8, -96], 3);
    
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    if(circle.length) L.circle([+circle[0], +circle[1]], +circle[2]).addTo(map);
    for (let point of points) {
        point = point.split("|");
        L.marker([+point[1], +point[0]]).addTo(map);
    }
}


/**
 * This function initializes a switch input.
 * @param {Element} inputElement the input element which is a checkbox.
 */
function initializeSwitchInput(inputElement) {
    inputElement.classList.add("form-check-input", "m-0");
    inputElement.parentElement.classList.add("form-check", "form-switch", "ps-0", "mb-4");
}


/**
 * This function initializes a tabbed in-page navigation.
 * @param {Element} tabsWrapper the wrapper element that contains the tabs and the tab contents.
 */
function initializeInPageNavTab(tabsWrapper) {
    const tabs = tabsWrapper.querySelectorAll(".nav-link");
    const tabContents = tabsWrapper.querySelectorAll(".tab-contents > div");

    // Add the active class to the first tab and show its content
    tabs[0].classList.add("active");
    tabContents[0].classList.add("active");

    for (let i=0; i<tabs.length; i++) {
        tabs[i].addEventListener("click", (e) => {
            e.preventDefault();
            for (let j=0; j<tabs.length; j++) {
                tabs[j].classList.remove("active");
                tabContents[j].classList.remove("active");
            }
            tabs[i].classList.add("active");
            tabContents[i].classList.add("active");
        });
    }
}
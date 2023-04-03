/**
 * This function creates a wrapper element for the keyword-input element.
 * @param {Element} input the keyword-input element
 * @returns A wrapper element that contains the keyword-input element.
 */
function createInputWrapper(input) {
    const keywordInputWrapper = document.createElement("div");
    keywordInputWrapper.classList.add("keyword-input-wrapper", "border", "p-2", "d-flex", "flex-wrap",
        "align-items-center")
    input.parentNode.insertBefore(keywordInputWrapper, input.nextSibling);
    keywordInputWrapper.appendChild(input);
    return keywordInputWrapper;
}


/**
 * This function creates a dummy input element that is used to capture the keyword.
 * @param {Element} wrapper the wrapper element that contains the keyword-input element. 
 * @param {Element} input the keyword-input element. 
 * @returns a dummy input element that is used to capture the keyword. 
 */
function createDummyInput(wrapper, input) {
    const dummyKeywordInput = document.createElement("input");
    dummyKeywordInput.style = "all: unset; border: 0";
    dummyKeywordInput.setAttribute("type", "text");
    dummyKeywordInput.setAttribute("placeholder", "Enter a keyword...");

    dummyKeywordInput.addEventListener("keydown", event => {
        if (event.key == " ") {
            event.preventDefault();
            updateKeywords(wrapper, input, dummyKeywordInput);
        }
    });

    wrapper.appendChild(dummyKeywordInput);
    return dummyKeywordInput;
}


/**
 * This function updates the keyword-input element and the UI with the keyword captured by the dummy input element.
 * @param {Element} wrapper the wrapper element that contains the keyword-input element.
 * @param {Element} input the keyword-input element. 
 * @param {Element} dummyInput the dummy input element that is used to capture the keyword.
 */
function updateKeywords(wrapper, input, dummyInput) {
    // Update the keyword-input element
    const keyword = dummyInput.value;
    if (input.value.length > 0) input.value += `,${keyword}`;
    else input.value += keyword;
    dummyInput.value = "";

    // Create box to display the keyword and a button to remove the keyword
    const keywordBox = document.createElement("div");
    keywordBox.classList.add("keyword-box", "d-flex", "align-items-center", "justify-content-between",
        "ps-1", "me-2", "border", "rounded");
    keywordBox.innerHTML = keyword;

    const removeButton = document.createElement("button");
    removeButton.classList.add("btn", "btn-sm", "fs-5", "p-0", "mb-2", "ms-2");
    removeButton.innerHTML = "<i class='fa-solid fa-xmark'></i>";
    removeButton.addEventListener("click", () => {
        keywordBox.remove();
        if (input.value.length > 0) input.value = input.value.replace(`,${keyword}`, "");
        else input.value = input.value.replace(keyword, "");
    });

    keywordBox.appendChild(removeButton);
    wrapper.insertBefore(keywordBox, dummyInput);
}


function populateKeywords(wrapper, input, dummyInput) {
    if (input.value.length == 0) return;
    for (const keyword of input.value.split(",")) {
        dummyInput.value = keyword;
        updateKeywords(wrapper, input, dummyInput);
    }
}


document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".keyword-input").forEach(input => {
        const keywordInputWrapper = createInputWrapper(input);
        createDummyInput(keywordInputWrapper, input);
        // Populate keyword-input if initial data is provided
        populateKeywords(keywordInputWrapper, input, keywordInputWrapper.lastChild);  
    });
});

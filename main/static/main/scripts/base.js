function switchBootstrapTheme() {
    const html = document.querySelector("html");
    const changedTheme = html.getAttribute("data-bs-theme") == "dark" ? "light" : "dark";
    html.setAttribute("data-bs-theme", changedTheme);
    localStorage.setItem("theme", changedTheme);
}


// Initialize theme
document.querySelector("html").setAttribute("data-bs-theme", localStorage.getItem("theme") || "dark");
addEventListener("DOMContentLoaded", () => {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {html: true}))

    // Initialize min-max sliders
    const sliderWrappers = document.querySelectorAll(".min-max-slider");
    for (const sliderWrapper of sliderWrappers) {
        const slider = sliderWrapper.querySelector(".slider");
        const inputs = [sliderWrapper.querySelector(".min-input"), sliderWrapper.querySelector(".max-input")]
        const min = parseInt(sliderWrapper.getAttribute("data-min"));
        const max = parseInt(sliderWrapper.getAttribute("data-max"));
        noUiSlider.create(slider, { start: [min, max], step: 1, range: {min, max} });
        slider.noUiSlider.on("update", (values, handle) => inputs[handle].value = parseInt(values[handle]));
        inputs.forEach((input, handle) => input.addEventListener("change", () => slider.noUiSlider.setHandle(handle, input.value)));
    }
});

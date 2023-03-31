function switchBootstrapTheme() {
    const html = document.querySelector("html");
    html.setAttribute("data-bs-theme", html.getAttribute("data-bs-theme") == "dark" ? "light" : "dark");
}

addEventListener("DOMContentLoaded", () => {
        // Initialize tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {html: true}))
});


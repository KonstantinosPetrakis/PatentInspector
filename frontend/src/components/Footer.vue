<style>
footer img {
    width: 3rem;
}

html[data-bs-theme="dark"] footer img {
    filter: invert(1) hue-rotate(180deg);
}
</style>

<template>
    <div class="d-flex flex-wrap align-items-center bg-secondary-subtle p-2">
        <div class="col-12 col-md-8">
            <h2 class="h4">PatentInspector</h2>
            <p class="mb-0">
                A tool for easy and open-source patent analysis.
            </p>
        </div>
        <div class="d-flex col-12 col-md-4">
            <div class="d-flex ms-md-auto mt-3 mt-md-0 ms-0">
                <a
                    class="me-2"
                    href="https://github.com/KonstantinosPetrakis/PatentInspector"
                >
                    <img src="/src/assets/images/github.png" alt="github" />
                </a>
                <a class="ms-2" href="https://patentinspector.csd.auth.gr/">
                    <img
                        src="/src/assets/images/csd.png"
                        alt="csd auth hosted application"
                    />
                </a>
            </div>
        </div>
    </div>
</template>

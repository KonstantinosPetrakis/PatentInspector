<style scoped>
img {
    width: 3rem;
}

html[data-bs-theme="dark"] img{
    filter: invert(1) hue-rotate(180deg);
}

</style>

<template>
    <div class="d-flex flex-wrap align-items-center bg-secondary-subtle p-2">
        <div class="col-12 col-md-8">
            <h2 class="h4">PatentAnalyzer</h2>
            <p class="mb-0">
                A tool for easy, fast and open-source patent analysis.
            </p>
        </div>
        <div class="d-flex col-12 col-md-4">
            <div class="d-flex ms-md-auto mt-3 mt-md-0 ms-0">
                <a
                    class="me-2"
                    href="https://github.com/KonstantinosPetrakis/PatentAnalyzer"
                >
                    <img src="src/assets/images/github.png" alt="github" />
                </a>
                <a
                    class="ms-2"
                    href="https://patentanalyzer.csd.auth.gr/"
                >
                    <img src="src/assets/images/csd.png" alt="csd auth hosted application" />
                </a>
            </div>
        </div>
    </div>
</template>

<script setup>
import { RouterLink } from "vue-router";
import { isLoggedIn, getUserEmail } from "../utils";
import MovingContainer from "../components/MovingContainer.vue";
import ThemeImage from "../components/ThemeImage.vue";

const email = getUserEmail();
const loggedIn = isLoggedIn();

const scrollToTop = () => window.scrollTo(0, 0, { behavior: "smooth" });
</script>

<template>
    <div class="container overflow-x-hidden">
        <template v-if="loggedIn">
            <h1 class="h1 text-center">PatentAnalyzer</h1>
            <p class="text-center h5">
                Welcome back {{ email }}, what would you like to do?
            </p>
            <div class="d-flex justify-content-center mt-4">
                <RouterLink
                    class="btn btn-outline-secondary mx-2"
                    :to="{ name: 'createReport' }"
                >
                    Create new report
                </RouterLink>
                <RouterLink
                    class="btn btn-outline-secondary mx-2"
                    :to="{ name: 'listReports' }"
                >
                    See all reports
                </RouterLink>
            </div>
        </template>

        <template v-else>
            <h2 class="h2 text-center">PatentAnalyzer</h2>
            <h4 class="h4 text-center mb-5">
                A tool for easy, fast and open-source patent analysis.
            </h4>
            <div class="row my-5">
                <div class="col-6 d-flex justify-content-center">
                    <a
                        class="btn btn-outline-secondary"
                        href="https://github.com/KonstantinosPetrakis/PatentAnalyzer"
                    >
                        View the source code on GitHub
                        <img
                            src="/src/assets/images/github.png"
                            alt="GitHub"
                            class="ms-2 logo"
                        />
                    </a>
                </div>
                <div class="col-6 d-flex justify-content-center">
                    <RouterLink
                        class="btn btn-outline-secondary d-flex align-items-center"
                        :to="{ name: 'register' }"
                    >
                        Register now and start analyzing patents
                    </RouterLink>
                </div>
            </div>
            <div class="row">
                <MovingContainer title="Creating Reports">
                    <p>
                        Easily generate reports by filtering the patents based
                        on comprehensive filters.
                    </p>
                    <hr />
                    <ThemeImage
                        srcName="form"
                        alt="PatentAnalyzer report creating form"
                    />
                </MovingContainer>
                <MovingContainer title="View Reports Anytime" alignment="right">
                    <p>
                        Your reports are securely saved, accessible whenever you
                        need them, ensuring you can track patent trends
                        effortlessly.
                    </p>
                    <hr />
                    <ThemeImage
                        srcName="reports"
                        alt="PatentAnalyzer list of reports page"
                    />
                </MovingContainer>
                <MovingContainer title="Statistical Measures">
                    <p>
                        Quickly grasp the patent landscape with statistical
                        metrics such as the average number of claims.
                    </p>
                    <hr />
                    <ThemeImage
                        srcName="stats"
                        alt="PatentAnalyzer statistics"
                    />
                </MovingContainer>
                <MovingContainer title="Time Series Analysis" alignment="right">
                    <p>
                        Dive into how variables change over time with intuitive
                        time series plots, helping you identify trends and
                        patterns.
                    </p>
                    <hr />
                    <ThemeImage
                        srcName="timeseries"
                        alt="PatentAnalyzer interactive timeseries plot"
                    />
                </MovingContainer>
                <MovingContainer title="Interactive Exploration">
                    <p>
                        Explore the patent landscape from various aspects with
                        interactive plots, including bar charts and heat maps,
                        to uncover hidden insights.
                    </p>
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="assignee"
                        alt="PatentAnalyzer interactive bar plot"
                    />
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="map"
                        alt="PatentAnalyzer interactive heatmap plot"
                    />
                </MovingContainer>
                <MovingContainer title="Thematic Analysis" alignment="right">
                    <p>
                        Gain an understanding of the main topics within the
                        patent landscape and their significance through visually
                        engaging bar charts and scatter plots in the thematic
                        analysis section.
                    </p>
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="topic-form"
                        alt="PatentAnalyzer topic form"
                    />
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="topic-class"
                        alt="PatentAnalyzer interactive scatter plot"
                    />
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="topics"
                        alt="PatentAnalyzer interactive bar plots"
                    />
                </MovingContainer>
                <MovingContainer title="Citation Analysis">
                    <p>
                        Visualize the citation network of patents in your
                        reports and discover the most cited patents.
                    </p>
                    <hr />
                    <ThemeImage
                        srcName="graph"
                        alt="An interactive 3D citation network"
                        type="gif"
                    />
                <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="cited"
                        alt="PatentAnalyzer interactive bar plot"
                    />
                </MovingContainer>
                <MovingContainer
                    title="Quickly export charts"
                    alignment="right"
                >
                    <p>
                        Each chart in PatentAnalyzer comes with a corresponding
                        table that can be effortlessly copied with a single
                        click and seamlessly pasted into your spreadsheet of
                        choice.
                    </p>
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="topic-table"
                        alt="PatentAnalyzer table and copy button"
                    />
                </MovingContainer>
                <MovingContainer
                    title="Download the filtered patents in excel format"
                >
                    <p>
                        PatentAnalyzer empowers you to export filtered patents in
                        Excel format, providing you with the freedom to conduct
                        further in-depth analyses on your terms.
                    </p>
                    <hr />
                    <ThemeImage
                        class="d-block"
                        srcName="patents"
                        alt="PatentAnalyzer patent table and download button"
                    />
                </MovingContainer>
                <button
                    class="btn btn-secondary col-lg-2 col-6 my-3 mx-auto"
                    @click="scrollToTop"
                >
                    Scroll to top
                </button>
            </div>
        </template>
    </div>
</template>

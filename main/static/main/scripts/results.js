// The colors that are being used for the plots.
const colors = [
    '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
    '#f95d6a', '#ff7c43', '#ffa600', '#8a2be2', '#dc143c'
];


/**
 * This function adds a "processing" message to the given container.
 * @param {String} selector the selector of the container that will contain the message.
 * @param {Boolean} table whether the container is a table or not. 
 */
function addProcessingMessage(selector, table = false) {
    const container = document.querySelector(selector);
    const message = `
        <p> Processing in progress... Please wait. </p>
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;

    if (table) container.innerHTML += `<tr class="fetch-message"> <td class="text-center" colspan="100"> ${message} </td> </tr>`;
    else container.innerHTML += `<div class="fetch-message text-center"> ${message} </div>`;
}

/**
 * This function removes the "processing" message from the given container.
 * @param {String} selector the selector of the container that contains the message.
 */
function removeProcessingMessage(selector) {
    document.querySelector(selector).removeChild(document.querySelector(`${selector} .fetch-message`));
}


/**
 * This function creates a table from a data object.
 * @param {Array[Array]} data an array of arrays containing the data (e.g [[x1, y1], [x2, y2], ...])
 * @param {Array[String]} labels the labels of the columns (e.g ["x", "y"])
 * @param {String} wrapperId the id of the element that will contain the table
 */
function createTable(data, labels, wrapperId) {
    const wrapper = document.getElementById(wrapperId);

    let headers = "";
    for (let label of labels) headers += `<th> ${label} </th>`;

    let rows = "";
    for (let row of data) {
        rows += "<tr>";
        for (let value of row) rows += `<td> ${value} </td>`;
        rows += "</tr>";
    }

    wrapper.innerHTML = `
        <div class="table-responsive">
            <div> <button class="btn btn-sm btn-theme"> 📋 </button> </div> 
            <table
                id="statistics-table"
                class="table table-sm"
            >
                <thead> ${headers} </thead>
                <tbody> ${rows} </tbody>
            </table>
        </div>
        `;

    wrapper.querySelector("button").addEventListener("click", () => 
        navigator.clipboard.writeText(wrapper.querySelector("table").innerText.trim())
    );
}


/**
 * This function creates a table from a data object.
 * @param {Object} object an object containing the data (e.g {x1: {y1: z1, y2: z2}, ...}
 * @return {Array[Array]} an array of arrays containing the data (e.g [[x1, y1, z1], ...])
 */
function objectToArray(object) {
    if (object[""] != undefined) object = object[""]; // Empty string is used for single dataset of datasets

    let array = [];
    for (let [key, value] of Object.entries(object)) {
        if (typeof value !== 'object') array.push([key, value]);
        else {
            for (let subArrayItem of objectToArray(value)) array.push([key, ...subArrayItem]);
        }
    }
    return array;
}

/**
 * This function creates an in-page navigation tab used to accommodate a plot and its respective table.
 * @param {String} id a unique id for the tab
 * @param {Sting} wrapperId the id of the element that will contain the plot and the table
 */
function createPlotAndTableNav(id, wrapperId) {
    const navWrapper = document.createElement("div");
    navWrapper.innerHTML = `
        <ul class="nav nav-tabs">
            <li class="nav-item">
                <a class="nav-link" style='font-size: .75rem' href="#${id}-plot"> Plot </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" style='font-size: .75rem'href="#${id}-table"> Table </a>
            </li>
        </ul>
        <div class="tab-contents">
            <div id="${id}-plot"> <canvas class="bar"> </canvas> </div>
            <div id="${id}-table"> </div>
        </div>
    `;
    navWrapper.className = "in-page-nav-tab col-12 col-md-6";
    document.querySelector(`#${wrapperId}`).appendChild(navWrapper);
    initializeInPageNavTab(navWrapper);
}

/**
 * This function creates a 2D plot with the given datasets and title.
 * @param {Object} datasets an object with keys the names of the lines, and values the data of the lines (e.g line1: {x1: y1, x2: y2, ...}, line2: {x1: y1, x2: y2, ...}, ...})
 * @param {String} title the title of the plot 
 * @param {Array[String]} dataLabels the labels of the columns (e.g ["x", "y"])
 */
function create2DPlot(datasets, title, dataLabels) {    
    const singleLine = Object.keys(datasets)[0] == "";

    // Find labels that fit all datasets
    let minYear = Infinity;
    let maxYear = -Infinity;

    for (let dataset of Object.values(datasets)) {
        for (let year of Object.keys(dataset)) {
            year = +year;
            if (year < minYear) minYear = year;
            if (year > maxYear) maxYear = year;
        }
    }

    let labels = [];
    for (let i = minYear; i <= maxYear; i++) labels.push(i.toString());

    // Fill missing values with 0
    for (let dataset of Object.values(datasets)) {
        for (let label of labels) 
            if (!dataset[label]) dataset[label] = 0;
    }

    const titleAsID = title.toLowerCase().replace(/ /g, "-");
    createPlotAndTableNav(titleAsID, "time-series");
    createTable(objectToArray(datasets), dataLabels, `${titleAsID}-table`);

    new Chart(document.querySelector(`#${titleAsID}-plot > canvas`), {
        type: "line",
        data: {
            labels,
            datasets: Object.entries(datasets).map(([name, data]) => ({
                label: singleLine ? title : name,
                data,
                tension: 0.1,
                backgroundColor: colors[Object.keys(datasets).indexOf(name)],
                borderColor: colors[Object.keys(datasets).indexOf(name)],
            }))
        },
        options: {
            plugins: {
                title: {
                    display: !singleLine,
                    text: title
                },
                legend: {
                    // We do that because text gets cut off in small screens
                    align: window.outerWidth > 768 ? "center" : "start",
                }
            },
            responsive: true,
			maintainAspectRatio: false,
            animation: false,
        }
    });
}


/**
 * This function creates a bar chart with the given dataset and title.
 * @param {Object} dataset an object with keys the names of the bars, and values the data of the bars
 * @param {String} title the title of the plot (e.g "y with respect to x")
 * @param {String} keyColumnName the title of the keys of the dataset (e.g "x")
 * @param {String} valueColumnName the title of the values of the dataset (e.g "y")
 * @param {String} wrapperId the id of the element that will contain the plot 
 */
function createBar(dataset, title, keyColumnName, valueColumnName, wrapperId) {
    const titleAsID = title.toLowerCase().replace(/ /g, "-");
    createPlotAndTableNav(titleAsID, wrapperId);
    createTable(objectToArray(dataset), [keyColumnName, valueColumnName], `${titleAsID}-table`);

    new Chart(document.querySelector(`#${titleAsID}-plot > canvas`), {
        type: "bar",
        data: {
            labels: Object.keys(dataset).map(key => key.length > 40 ? key.substring(0, 40) + "..." : key),
            datasets: [{
                data: Object.values(dataset),
                maxBarThickness: 25,
                backgroundColor: colors[0]
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: title
                },
                legend: {
                    display: false,
                }
            },
            indexAxis: 'y',
            responsive: true,
			maintainAspectRatio: false,
            
            animation: false
        }
    });
}


/**
 * This function creates a heatmap with the given points and title.
 * @param {Array<Object>} points the points (lat, lng, count) that will be used to create the heatmap 
 * @param {String} title the title of the plot 
 * @param {String} wrapperID the id of the element that will contain the plot 
 */
function createHeatmap(points, title, wrapperID) {
    console.log(points);
    var mapWithLegendElement = document.createElement("div");
    mapWithLegendElement.textContent = title;
    mapWithLegendElement.classList.add("col-12", "d-flex", "flex-column", "align-items-center");
    var mapElement = document.createElement("div");
    mapElement.classList.add("map", "global-map");
    mapElement.id = `map-${(Math.round(Math.random() * 100))}`;
    mapWithLegendElement.appendChild(mapElement);
    document.querySelector(`#${wrapperID}`).appendChild(mapWithLegendElement);

    var map = L.map(mapElement.id).setView([44, -50], 3);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Fix mess of hidden elements with leaflet map
    const observer = new MutationObserver(() => map.invalidateSize());
    const mapWrapper = mapElement.closest(".accordion-collapse, .tab-contents > div");
    if (mapWrapper) observer.observe(mapWrapper, { attributes: true, attributeFilter: ["style", "class"] });

    var heatmapLayer = new HeatmapOverlay({
        "radius": 2,
        "maxOpacity": .8,
        "scaleRadius": true,
        "useLocalExtrema": false,
        latField: 'lat',
        lngField: 'lng',
        valueField: 'count'
    });

    heatmapLayer.addTo(map);
    heatmapLayer.setData({ max: Math.max(...points.map((point) => point.count)), data: points });
}


/**
 * This function creates the plots for the topic analysis.
 * @param {Object} data the data that will be used to create the plots.
 */
function createTopicAnalysisPlot(data) {
    const coherenceText = document.createElement("div");
    coherenceText.textContent = `Topic Coherence: ${data.coherence}`;
    document.getElementById("topic-analysis").appendChild(coherenceText);
    for (let i = 0; i < data.n_topics; i++) {
        let topicObj = {};
        for (let j=0; j< data.n_words; j++) topicObj[data.topics[i].words[j]] = data.topics[i].weights[j];           
        createBar(topicObj, `Topic ${i + 1}`, "Word", "Weight", "topic-analysis");
    }
}

/**
 * This function creates the scatter plot for the topic analysis.
 * @param {Object} data the data that will be used to create the plot.
 */
function createTopicAnalysisScatter(data) {
    const wrapper = document.createElement("div");
    const canvas = document.createElement("canvas");
    wrapper.classList.add("col-12", "col-md-6", "col-lg-4");
    wrapper.appendChild(canvas);
    document.querySelector("#topic-analysis").appendChild(wrapper);

    const scatterData = data.topics.map(topic => ({ x: topic.ratio, y: topic.cagr }));
    const labels = [];
    for (let i = 0; i < data.topics.length; i++)
        labels.push(`Topic ${i + 1}: ${data.topics[i].words.join()}`);

    let averageRatio = scatterData.reduce((acc, curr) => acc + curr.x, 0) / scatterData.length;

    new Chart(canvas, {
        type: "scatter",
        data: {
            labels,
            datasets: [{
                data: scatterData,
                backgroundColor: colors,
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                },
                labels,
                annotation: {
                    annotations: {
                        emerging: {
                            type: "box",
                            xMax: averageRatio,
                            yMin: 0,
                            backgroundColor: 'rgba(250, 250, 3, 0.25)',
                            label: {
                                drawTime: 'afterDraw',
                                display: true,
                                content: 'Emerging Topics',
                                position: {
                                    x: 'center',
                                    y: 'start'
                                }
                            }
                        },
                        dominant: {
                            type: "box",
                            xMin: averageRatio,
                            yMin: 0,
                            backgroundColor: 'rgba(250, 106, 3, 0.25)',
                            label: {
                                drawTime: 'afterDraw',
                                display: true,
                                content: 'Dominant Topics',
                                position: {
                                    x: 'center',
                                    y: 'start'
                                }
                            }
                        },
                        declining: {
                            type: "box",
                            xMax: averageRatio,
                            yMax: 0,
                            backgroundColor: 'rgba(52, 58, 59, 0.25)',
                            label: {
                                drawTime: 'afterDraw',
                                display: true,
                                content: 'Declining Topics',
                                position: {
                                    x: 'center',
                                    y: 'start'
                                }
                            }
                        },
                        saturated: {
                            type: "box",
                            xMin: averageRatio,
                            yMax: 0,
                            backgroundColor: 'rgba(130, 157, 129, 0.25)',
                            label: {
                                drawTime: 'afterDraw',
                                display: true,
                                content: 'Saturated Topics',
                                position: {
                                    x: 'center',
                                    y: 'start'
                                }
                            }
                        }
                    }
                }
            },
            responsive: true,
			maintainAspectRatio: false,
            animation: false,
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: "Ratio",
                }
            },
            y: {
                title: {
                    display: true,
                    text: "CAGR",
                }
            }
        }
    });
}

/**
 * This function creates the citation graph given the data retrieved from the server api.
 * @param {Array<Object>} data the array containing the patent citations. 
 * @param {String} wrapperSelector the selector of the element that will contain the graph.
 */
function createGraph(data, wrapperSelector) {
    function _createGraph(data, wrapper) {
        const darkMode = document.querySelector("html").getAttribute("data-bs-theme") == "dark";
        const nodes = {};
        const links = [];

        data.forEach(item => {
            const citingNode = { id: item.citing_patent_id, code: item.citing_patent_code, title: item.citing_patent__title, granted_date: item.citing_patent__granted_date };
            const citedNode = { id: item.cited_patent_id, code: item.cited_patent_code, title: item.cited_patent__title, granted_date: item.cited_patent__granted_date };

            nodes[citingNode.id] = citingNode;
            nodes[citedNode.id] = citedNode;

            links.push({ source: citingNode.id, target: citedNode.id });
        });

        const graph = ForceGraph3D({ controlType: 'orbit' })(wrapper)
            .graphData({ nodes: Object.values(nodes), links })
            .nodeLabel(node => `<span style="color: ${darkMode ? "#fff" : "#000"}">${node.code} - ${node.title} - ${node.granted_date}</span>`)
            .linkDirectionalArrowLength(3.5)
            .linkDirectionalArrowRelPos(1)
            .linkCurvature(0.25)
            .width(window.screen.width * 0.8)
            .height(window.screen.height * 0.8)
            .backgroundColor(darkMode ? "#212529" : "#fff")
            .linkColor(() => darkMode ? "#fff" : "#000")
            .nodeColor(() => "#d45087")
            .onNodeClick(node => window.open(`https://patents.google.com/?oq=${node.code}`))
            .warmupTicks(30)
            .cooldownTicks(0)
            .enableNodeDrag(false);
    }

    const wrapper = document.querySelector(wrapperSelector);
    if (data.length < 5000) _createGraph(data, wrapper);
    else {
        const graphMessage = document.createElement("div");
        graphMessage.textContent = `
        The citation graph consist of ${data.length} citations and it would need a lot of processing power
        to be drawn. This could lead to an unresponsive page, some PCs might handle it. If you want to try
        you can click on the button below. Although a graph of this size is not so easy to read/understand.`;

        const graphButton = document.createElement("button");
        graphButton.className = "btn btn-outline-secondary";
        graphButton.textContent = "Draw graph";
        graphButton.addEventListener("click", () => {
            wrapper.innerHTML = "";
            _createGraph(data, wrapper);
        });

        wrapper.appendChild(graphMessage);
        wrapper.appendChild(graphButton);
    }
}

/**
 * This function populates the table with the given data.
 * @param {Array<Object>} data the data containing the patents 
 */
function populatePatentTable(data) {
    const tbody = document.querySelector("#patent-table tbody");
    let html = "";
    let replaceNullWithZero = (val) => val == null ? 0 : val;
    for (const patent of data.patents) {
        html += `
            <tr>
                <td> <div> ${patent.office} </div> </td>
                <td> <div> ${patent.office_patent_id} </div> </td>
                <td> <div> ${patent.type} </div> </td>
                <td> <div> ${patent.application_filed_date} </div> </td>
                <td> <div> ${patent.granted_date} </div> </td>
                <td> <div> ${patent.title} </div> </td>
                <td> <div> ${patent.abstract_processed != null ? patent.abstract_processed : "No abstract"} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.claims_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.figures_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.sheets_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.cpc_groups_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.inventor_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.assignee_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.incoming_citations_count)} </div> </td>
                <td> <div> ${replaceNullWithZero(patent.outgoing_citations_count)} </div> </td>
                <td> <div> ${patent.withdrawn} </div> </td>
            </tr>
        `;
    }
    tbody.innerHTML = html;
    for (const pointMap of document.querySelectorAll(".point-map")) initializePointMap(pointMap);
}


/**
 * This function creates the pagination for the patent table.
 * @param {Object} data the data containing the pagination information 
 */
function createPagination(data) {
    const pagination = document.querySelector(".pagination");
    let html = "";

    for (const page of data.page_range) {
        let extraClass = "";
        if (page === "…") extraClass = "disabled";
        else if (page === data.page) extraClass = "active";
        html += `
            <li class="page-item">
                <a class="page-link ${extraClass}" href="#"> ${page} </a>
            </li>
        `;
    }
    pagination.innerHTML = html;

    for (const page of document.querySelectorAll(".page-link:not(.disabled)")) {
        page.addEventListener("click", async (e) => {
            e.preventDefault();
            await goToPage(+page.textContent);
        });
    }
}


/**
 * This function fetches the patents for the given page and populates the table and creates the pagination.
 * @param {Number} page the page to go to. 
 */
async function goToPage(page) {
    document.querySelector(".pagination").innerHTML = "";

    addProcessingMessage("#patent-table tbody", true)
    const response = await fetch(`/api/patents?page=${page}`);
    const data = await response.json();
    removeProcessingMessage("#patent-table tbody");

    populatePatentTable(data);
    createPagination(data);
    document.querySelector("#result-counts").textContent = `You selected ${data.selected_record_count} out of ${data.total_record_count} patents.`
}


/**
 * This function fetches the statistics and populates the table.
 */
async function fetchStatisticsTable() {
    let formatNumber = num => num == null ? "N/A" : num.toFixed(2);

    addProcessingMessage("#statistics-table tbody", true);
    const response = await fetch("/api/statistics");
    const data = await response.json();

    let html = "";
    for (let field of Object.keys(data)) {
        html += `
            <tr>
                <td> ${field} </td>
                <td> ${formatNumber(data[field].avg)} </td>
                <td> ${formatNumber(data[field].med)} </td>
                <td> ${formatNumber(data[field].std_dev)} </td>
                <td> ${formatNumber(data[field].min)} </td>
                <td> ${formatNumber(data[field].max)} </td>
            </tr>
        `;
    }
    document.querySelector("#statistics-table tbody").innerHTML = html;
}


/**
 * This function fetches the time series and creates the plots.
 */
async function fetchTimeSeries() {
    addProcessingMessage("#time-series", false);
    const response = await fetch("/api/time-series");
    const data = await response.json();
    removeProcessingMessage("#time-series");
    create2DPlot(data.applications_per_year, "Applications per year", ["Year", "Application Count"]);
    create2DPlot(data.granted_patents_per_year, "Granted patents per year", ["Year", "Grant Count"]);
    create2DPlot(data.pct_protected_patents_per_year, "PCT protected patents per year", ["Year", "PCT Grant Count"]);
    create2DPlot(data.citations_made_per_year, "Citations made per year", ["Year", "Citation Made Count"]);
    create2DPlot(data.citations_received_per_year, "Citations received per year", ["Year", "Citation Received Count"]);
    create2DPlot(data.granted_patents_per_type_year, "Granted patents of different types per year", ["Type", "Year", "Grant Count"]);
    create2DPlot(data.granted_patents_per_office_year, "Granted patents of different offices per year", ["Office", "Year", "Grant Count"]);
    create2DPlot(data.granted_patents_per_cpc_year, "Granted patents of different CPC sections per year", ["CPC Section", "Year", "Grant Count"]);
}


/**
 * This function fetches the entity information and creates the plots.
 */
async function fetchEntityInfo() {
    addProcessingMessage("#entity-info", false);
    const response = await fetch("/api/entity-info");
    const data = await response.json();
    removeProcessingMessage("#entity-info");

    // Patent
    createBar(data.patent.pct, "PCT protection of patents", "PCT Status", "Count", "entity-patent");
    createBar(data.patent.type, "Types of patents", "Patent Type", "Count", "entity-patent");
    createBar(data.patent.office, "Offices of patents", "Office", "Count", "entity-patent");

    // Inventor
    createBar(data.inventor.top_10, "Inventors with the most inventions", "Inventor", "Invention Count", "entity-inventor");
    createHeatmap(data.inventor.locations, "Inventor Locations", "entity-inventor");

    // Assignee
    createBar(data.assignee.top_10, "Most common assignees", "Assignee", "Patent Count", "entity-assignee");
    createBar(data.assignee.corporation_vs_individual, "Corporation and individual assignees", "Assignee Type", "Count", "entity-assignee");
    createHeatmap(data.assignee.locations, "Assignee Locations", "entity-assignee");

    // CPC
    createBar(data.cpc.section, "CPC sections", "CPC Section", "References from patents", "entity-cpc");
    createBar(data.cpc.top_5_classes, "Most common CPC classes", "CPC Class", "References from patents", "entity-cpc");
    createBar(data.cpc.top_5_subclasses, "Most common CPC subclasses", "CPC Subclass", "References from patents", "entity-cpc");
    createBar(data.cpc.top_5_groups, "Most common CPC groups", "CPC Group", "References from patents", "entity-cpc");
}


/**
 * This function fetches the topic modeling data and creates the plots.
 */
async function getTopicModeling() {
    const wrapper = document.querySelector("#topic-analysis");
    let model = document.querySelector(`select[name="topic-analysis-method"]`).value;
    let start_date = document.querySelector(`input[name="topic-analysis-start-date"]`)?.value;
    let end_date = document.querySelector(`input[name="topic-analysis-end-date"]`)?.value;
    let n_topics = document.querySelector(`input[name="topic-analysis-number-topics"]`)?.value;
    let n_words = document.querySelector(`input[name="topic-analysis-number-words"]`)?.value;
    let arguments = { model: model };
    if (start_date) arguments.start_date = start_date;
    if (end_date) arguments.end_date = end_date;
    if (n_topics) arguments.n_topics = n_topics;
    if (n_words) arguments.n_words = n_words;

    wrapper.innerHTML = "";
    addProcessingMessage("#topic-analysis", false);
    const response = await fetch("/api/topic-modeling?" + new URLSearchParams(arguments));
    const data = await response.json();
    removeProcessingMessage("#topic-analysis");
    createTopicAnalysisScatter(data);
    createTopicAnalysisPlot(data);

    let createdMessage = document.createElement("div");
    createdMessage.textContent += `Created ${data.n_topics} topics with ${data.n_words} words each, 
        using the ${model} model/algorithm. Classified topics using range 
        ${data.start_date} to ${data.end_date}.`;
    wrapper.prepend(createdMessage);
}


/**
 * This function fetches the citation data and creates some pies and a 3D graph.
 */
async function getCitationData() {
    addProcessingMessage("#network-analysis", false);
    const response = await fetch("/api/citation-data");
    const data = await response.json();
    removeProcessingMessage("#network-analysis");

    createGraph(data.graph, "#citation-graph");
    createBar(data.most_cited_patents_global, "Most cited patents globally", "Patent", "Citations", "most-cited");
    createBar(data.most_cited_patents_local, "Most cited patents locally", "Patent", "Citations", "most-cited");
}


document.addEventListener("DOMContentLoaded", () => {
    goToPage(1);
    fetchStatisticsTable();
    fetchTimeSeries();
    fetchEntityInfo();
    getTopicModeling();
    getCitationData();
});

// The colors that are being used for the plots.
const colors = [
    '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
    '#f95d6a', '#ff7c43', '#ffa600', '#8a2be2', '#dc143c'
];


/**
 * This function creates a 2D plot with the given datasets and title.
 * @param {Object} datasets an object with keys the names of the lines, and values the data of the lines
 * @param {String} title the title of the plot 
 */
function create2DPlot(datasets, title) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("col-12", "col-md-6", "col-lg-4");

    const canvas = document.createElement("canvas");
    wrapper.appendChild(canvas);
    document.getElementById("time-series").appendChild(wrapper);

    const singleLine = Object.keys(datasets)[0] == "";

    new Chart(canvas, {
        type: "line",
        data: {
            labels: Object.keys(datasets).values()[0], // labels are the same for all datasets, 
            datasets: Object.entries(datasets).map(([name, data]) => ({
                label: singleLine ? title : name,
                data: Object.values(data),
                data,
                tension: 0.1,
                backgroundColor: colors[Object.keys(datasets).indexOf(name)],
                borderColor: colors[Object.keys(datasets).indexOf(name)],
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: !singleLine,
                    text: title
                }
            }
        }
    });
}


/**
 * This function creates a pie chart with the given dataset and title.
 * @param {Object} dataset an object with keys the names of the slices, and values the data of the slices
 * @param {String} title the title of the plot 
 * @param {String} wrapperId the id of the element that will contain the plot 
 */
function createPie(dataset, title, wrapperId) {
    const wrapper = document.createElement("div");
    const canvas = document.createElement("canvas");
    wrapper.classList.add("col-12", "col-md-6", "col-lg-4");
    wrapper.appendChild(canvas);
    document.querySelector(`#${wrapperId}`).appendChild(wrapper);

    new Chart(canvas, {
        type: "pie",
        data: {
            labels: Object.keys(dataset).map(key => key.length > 80 ? key.substring(0, 80) + "..." : key),
            datasets: [{
                data: Object.values(dataset),
                backgroundColor: colors
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: title
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            animation: false
        }   
    });
}


function createHeatmap(points) {    

}

/**
 * This function populates the table with the given data.
 * @param {Array<Object>} data the data containing the patents 
 */
function populatePatentTable(data) {
    const tbody = document.querySelector("#patent-table tbody");
    let html = "";
    for (const patent of data.patents) {
        html += `
            <tr>
                <td> <div> ${patent.office} </div> </td>
                <td> <div> ${patent.office_patent_id} </div> </td>
                <td> <div> ${patent.type} </div> </td>
                <td> <div> ${patent.application_filed_date} </div> </td>
                <td> <div> ${patent.granted_date} </div> </td>
                <td> <div> ${patent.title} </div> </td>
                <td> <div> ${patent.abstract != null ? patent.abstract : "No abstract"} </div> </td>
                <td> <div> ${patent.claims_count} </div> </td>
                <td> <div> ${patent.figures_count} </div> </td>
                <td> <div> ${patent.withdrawn} </div> </td>
                <td> <div> ${patent.cpc_groups_groups} </div> </td>
                <td> <div> ${patent.pct_documents} </div> </td>
                <td> <div> ${patent.inventor_names} </div> </td>
                <td> <div class="point-map" data-circle="${data.inventor_circle}" data-points="${patent.inventor_points}"> </div> </td>
                <td> <div> ${patent.assignee_names} </div> </td>
                <td> <div class="point-map" data-circle="${data.assignee_circle}" data-points="${patent.assignee_points}"> </div> </td>
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
    const tbody = document.querySelector("#patent-table tbody");
    const pagination = document.querySelector(".pagination");
    pagination.innerHTML = "";
    tbody.innerHTML = `
        <tr class="fetch-message">
            <td class="text-center" colspan="100"> <!-- It's ok for < 100 columns -->
                <p> Fetching data... Please wait. </p>
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </td>
        </tr>
    `;

    const response = await fetch(`/api/patents?page=${page}`);
    const data = await response.json();
    populatePatentTable(data);
    createPagination(data);
    document.querySelector("#result-counts").textContent = `You selected ${data.selected_record_count} out of ${data.total_record_count} patents.`
}


/**
 * This function fetches the statistics and populates the table.
 */
async function fetchStatisticsTable() {
    const table = document.querySelector("#statistics-table tbody");
    table.innerHTML = `
        <tr class="fetch-message">
            <td class="text-center" colspan="100"> <!-- It's ok for < 100 columns -->
                <p> Processing in progress... Please wait. </p>
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </td>
        </tr>
    `;

    const response = await fetch("/api/statistics");
    const data = await response.json();

    let html = "";
    for (let field of Object.keys(data)) {
        html += `
            <tr>
                <td> ${field} </td>
                <td> ${data[field].avg.toFixed(2)} </td>
                <td> ${data[field].med.toFixed(2)} </td>
                <td> ${data[field].std_dev.toFixed(2)} </td>
            </tr>
        `;
    }
    table.innerHTML = html;
}


/**
 * This function fetches the time series and creates the plots.
 */
async function fetchTimeSeries() {
    const timeSeriesWrapper = document.getElementById("time-series");
    timeSeriesWrapper.innerHTML = `
        <div class="text-center">
            <p> Processing in progress... Please wait. </p>
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;

    const response = await fetch("/api/time-series");
    const data = await response.json();
    timeSeriesWrapper.innerHTML = "";
    create2DPlot({"": data.applications_per_year}, "Applications per year");
    create2DPlot({"": data.granted_patents_per_year}, "Granted patents per year");
    create2DPlot({"": data.pct_protected_patents_per_year}, "PCT protected patents per year");
    create2DPlot({"": data.citations_made_per_year}, "Citations made per year");
    create2DPlot({"": data.citations_received_per_year}, "Citations received per year");
    create2DPlot(data.granted_patents_per_type_year, "Granted patents of different types per year");
    create2DPlot(data.granted_patents_per_office_year, "Granted patents of different offices per year");
    create2DPlot(data.granted_patents_per_cpc_year, "Granted patents of different CPC sections per year");
}


/**
 * This function fetches the entity information and creates the plots.
 */
async function fetchEntityInfo() {
    const response = await fetch("/api/entity-info");
    const data = await response.json();

    // Patent
    createPie(data.patent.pct, "PCT protection of patents", "entity-patent");
    createPie(data.patent.type, "Types of patents", "entity-patent");
    createPie(data.patent.office, "Offices of patents", "entity-patent");

    // Inventor
    createPie(data.inventor.top_10, "Top 10 inventors", "entity-inventor");
    createHeatmap(1);

    // Assignee
    createPie(data.assignee.top_10, "Top 10 assignees", "entity-assignee");
    createPie(data.assignee.corporation_vs_individual, "Corporation and individual assignees", "entity-assignee");

    // CPC
    createPie(data.cpc.section, "CPC sections", "entity-cpc");
    createPie(data.cpc.top_5_classes, "Top 5 CPC classes", "entity-cpc");
    createPie(data.cpc.top_5_subclasses, "Top 5 CPC subclasses", "entity-cpc");
    createPie(data.cpc.top_5_groups, "Top 5 CPC groups", "entity-cpc");
}


document.addEventListener("DOMContentLoaded", () => {
    goToPage(1);
    fetchStatisticsTable();
    fetchTimeSeries();
    fetchEntityInfo();
});

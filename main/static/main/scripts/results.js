function populateTable(data) {
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
                <td> <div> ${patent.abstract} </div> </td>
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
    populateTable(data);
    createPagination(data);
}


document.addEventListener("DOMContentLoaded", () => goToPage(1));

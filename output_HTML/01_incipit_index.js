let hymns = [];
const sortState = {};

fetch("01_incipit_index.json")
    .then(response => response.json())
    .then(data => {

        hymns = data;

        renderTable(hymns);

        document.querySelectorAll("th").forEach(th => {

            th.addEventListener("click", () => {

                const key = th.dataset.sort;

                sortBy(key);

            });

        });

    });

function renderTable(data) {

    const tbody = document.querySelector("#hymn-table tbody");

    tbody.innerHTML = "";

    data.forEach(item => {

        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>
                <a href="${item.file}"
                   target="_blank"
                   rel="noopener noreferrer">
                    ${item.incipit}
                </a>
            </td>
            <td>${item.auctor ?? ""}</td>
            <td>${item.metrum ?? ""}</td>
            <td>${item.fons ?? ""} (${item.annus ?? ""})</td>
        `;

        tbody.appendChild(tr);

    });

}

function sortBy(key) {

    sortState[key] = !sortState[key];

    hymns.sort((a, b) => {

        let valueA;
        let valueB;

        if (key === "fonsannus") {

            valueA =
                `${a.fons ?? ""} ${a.annus ?? ""}`
                .toLowerCase();

            valueB =
                `${b.fons ?? ""} ${b.annus ?? ""}`
                .toLowerCase();

        } else {

            valueA =
                (a[key] ?? "")
                .toLowerCase();

            valueB =
                (b[key] ?? "")
                .toLowerCase();

        }

        if (valueA < valueB)
            return sortState[key] ? -1 : 1;

        if (valueA > valueB)
            return sortState[key] ? 1 : -1;

        return 0;

    });

    renderTable(hymns);

}

let searchData = [];

function normalize(text) {
    return text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();
}

fetch("02_versus_index.json")
    .then(response => response.json())
    .then(data => {
        searchData = data;
        populateDatalists();
    })
    .catch(error => {
        console.error("Error...", error);
    });

function populateDatalists() {
    const auctores = [...new Set(searchData.map(item => item.auctor))].sort();
    const fontes = [...new Set(searchData.map(item => item.fons))].sort();

    const auctorList = document.getElementById("auctores");
    const fonsList = document.getElementById("fontes");

    auctores.forEach(a => {
        if (a) {
            const option = document.createElement("option");
            option.value = a;
            auctorList.appendChild(option);
        }
    });

    fontes.forEach(f => {
        if (f) {
            const option = document.createElement("option");
            option.value = f;
            fonsList.appendChild(option);
        }
    });
}

function evaluateTextQuery(query, text) {
    if (!query) return true;

    const normalizedText = normalize(text);
    const tokens = query.trim().split(/\s+/);

    if (tokens.length === 1) {
        return normalizedText.includes(normalize(tokens[0]));
    }

    let result = null;
    let operator = null;

    tokens.forEach(token => {
        const upper = token.toUpperCase();

        if (upper === "AND" || upper === "OR" || upper === "NOT" || upper === "XOR") {
            operator = upper;
            return;
        }

        const current = normalizedText.includes(normalize(token));

        if (result === null) {
            result = current;
            return;
        }

        switch (operator) {
            case "AND":
                result = result && current;
                break;
            case "OR":
                result = result || current;
                break;
            case "XOR":
                result = result !== current;
                break;
            case "NOT":
                result = result && !current;
                break;
        }
    });

    return result;
}

function highlightText(text, query) {
    if (!query) return text;

    const words = query
        .split(/\s+/)
        .filter(word => {
            const upper = word.toUpperCase();
            return !["AND", "OR", "NOT", "XOR"].includes(upper);
        });

    let output = text;

    words.forEach(word => {
        if (word.trim().length === 0) return;
        const regex = new RegExp("(" + word + ")", "gi");
        output = output.replace(regex, "<mark>$1</mark>");
    });

    return output;
}

function performSearch() {
    const textQuery = document.getElementById("textus").value.trim();
    const auctorQuery = normalize(document.getElementById("auctor").value);
    const fonsQuery = normalize(document.getElementById("fons").value);

    const opAuctor = document.getElementById("operatorAuctor").value;
    const opFons = document.getElementById("operatorFons").value;

    const resultsSection = document.getElementById("resultsSection");
    if (resultsSection) {
        resultsSection.classList.remove("hidden-section");
    }

    if (textQuery) {
        sessionStorage.setItem("lastSearchQuery", textQuery);
    } else {
        sessionStorage.removeItem("lastSearchQuery");
    }

    const results = searchData.filter(item => {
        const textMatch = evaluateTextQuery(textQuery, item.textus_norm);
        const auctorMatch = !auctorQuery || normalize(item.auctor).includes(auctorQuery);
        const fonsMatch = !fonsQuery || normalize(item.fons).includes(fonsQuery);

        let combinedTextAuctor = textMatch;
        if (auctorQuery) {
            switch (opAuctor) {
                case "AND": combinedTextAuctor = textMatch && auctorMatch; break;
                case "OR":  combinedTextAuctor = textMatch || auctorMatch; break;
                case "XOR": combinedTextAuctor = textMatch !== auctorMatch; break;
                case "NOT": combinedTextAuctor = textMatch && !auctorMatch; break;
            }
        }

        let finalMatch = combinedTextAuctor;
        if (fonsQuery) {
            switch (opFons) {
                case "AND": finalMatch = combinedTextAuctor && fonsMatch; break;
                case "OR":  finalMatch = combinedTextAuctor || fonsMatch; break;
                case "XOR": finalMatch = combinedTextAuctor !== fonsMatch; break;
                case "NOT": finalMatch = combinedTextAuctor && !fonsMatch; break;
            }
        }

        return finalMatch;
    });

    renderResults(results, textQuery);
}

function renderResults(results, textQuery) {
    const container = document.getElementById("results");
    const count = document.getElementById("resultCount");

    count.textContent = results.length + " eventus";
    container.innerHTML = "";

    if (results.length === 0) {
        container.innerHTML = "<p>Nihil inventum est.</p>";
        return;
    }

    results.forEach(item => {
        const div = document.createElement("div");
        div.className = "result";

        const highlighted = highlightText(item.textus, textQuery);

        const urlSafeQuery = encodeURIComponent(textQuery);

        div.innerHTML = `
            <div class="result-title">
                <a href="${item.file}?search=${urlSafeQuery}#${item.id}" target="_blank" rel="noopener noreferrer">
                    ${item.titulus}
                </a>
            </div>
            <div class="result-locus">
                ${item.locus} · ${item.auctor}
            </div>
            <div class="result-text">
                ${highlighted}
            </div>
        `;

        container.appendChild(div);
    });
}

document.getElementById("searchButton").addEventListener("click", performSearch);

[document.getElementById("textus"), document.getElementById("auctor"), document.getElementById("fons")].forEach(input => {
    if (input) {
        input.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                performSearch();
            }
        });
    }
});

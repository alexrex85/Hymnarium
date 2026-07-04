document.addEventListener("DOMContentLoaded", () => {
    const wrappers = document.querySelectorAll(".bib-wrapper");

    if (wrappers.length === 0) return;

    wrappers.forEach(wrapper => {
        const sortSelect = wrapper.querySelector(".sort-bibliography");
        const targetElement = wrapper.querySelector(".bib-target");

        if (!targetElement) return;

        const jsonFile = targetElement.getAttribute("data-source");
        let bibliographyData = [];

        fetch(jsonFile)
            .then(response => response.json())
            .then(data => {
                bibliographyData = data;
                
                renderSection(bibliographyData, targetElement, sortSelect ? sortSelect.value : "author");

                if (sortSelect) {
                    sortSelect.addEventListener("change", () => {
                        renderSection(bibliographyData, targetElement, sortSelect.value);
                    });
                }
            })
            .catch(err => {
                console.error("Errore nel caricamento del file " + jsonFile, err);
                targetElement.innerHTML = "<p>Error...</p>";
            });
    });

    function renderSection(items, targetElement, sortBy) {
        if (!items || items.length === 0) {
            targetElement.innerHTML = "<p>Nihil inventum.</p>";
            return;
        }

        items.sort((a, b) => {
            const authorA = getAuthorString(a).toLowerCase();
            const authorB = getAuthorString(b).toLowerCase();
            const yearA = getYear(a);
            const yearB = getYear(b);
            const titleA = (a.title || "").toLowerCase();
            const titleB = (b.title || "").toLowerCase();

            if (sortBy === "year") {
                if (yearA !== yearB) return yearA - yearB;
                return authorA.localeCompare(authorB);
            } else if (sortBy === "title") {
                return titleA.localeCompare(titleB);
            } else {
                return authorA.localeCompare(authorB);
            }
        });

        targetElement.innerHTML = "";

        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "bib-item";

            const hasAuthor = item.author && item.author.length > 0;
            const hasEditor = item.editor && item.editor.length > 0;
            const authorsStr = getAuthorString(item, true);
            const year = getYear(item) || "s.a.";
            const title = item.title || "Untitled";
            
            let citationText = "";

            if (item.type === "manuscript" && !hasAuthor && !hasEditor) {
                citationText = `(${year}), `;
            } else {
                citationText = `${authorsStr} (${year}), `;
            }

            if (item.type === "article-journal" || item.type === "article") {
                const journal = item["container-title"] || "";
                const volume = item.volume || "";
                const issue = item.issue || "";
                const pages = item.page || "";
                citationText += `«${title}», in <em>${journal}</em> ${volume}${issue ? "." + issue : ""} (${year}), ${pages ? "pp. " + pages : ""}`;
            } else if (item.type === "chapter") {
                const bookTitle = item["container-title"] || "";
                const editors = item.editor ? item.editor.map(e => `${e.given ? e.given[0] + ". " : ""}${e.family}`).join(", ") + " (ed.)" : "";
                const pages = item.page || "";
                citationText += `«${title}», in ${editors ? editors + ", " : ""}<em>${bookTitle}</em>, ${pages ? "pp. " + pages : ""}`;
            } else if (item.type === "manuscript") {
                const archive = item.archive || "";
                citationText += `<em>${title}</em>, ${archive}`;
            } else {
                const place = item["publisher-place"] || "";
                const publisher = item.publisher || "";
                
                if (!hasAuthor && hasEditor) {
                    citationText += `<em>${title}</em>${place ? ", " + place : ""}${publisher ? ": " + publisher : ""}`;
                } else {
                    let editorSuffix = hasEditor ? ", curante " + item.editor.map(e => `${e.given ? e.given[0] + ". " : ""}${e.family}`).join(", ") : "";
                    citationText += `<em>${title}</em>${editorSuffix}${place ? ", " + place : ""}${publisher ? ": " + publisher : ""}`;
                }
            }

            let linkUrl = item.DOI ? `https://doi.org/${item.DOI}` : (item.URL || "");
            if (linkUrl) {
                citationText += ` [<a href="${linkUrl}" target="_blank" rel="noopener noreferrer">Hic lege</a>]`;
            }

            div.innerHTML = citationText + ".";
            targetElement.appendChild(div);
        });
    }

    function getYear(item) {
        if (item.issued && item.issued["date-parts"] && item.issued["date-parts"][0]) {
            return parseInt(item.issued["date-parts"][0][0], 10);
        }
        return 0;
    }

    function getAuthorString(item, formatHTML = false) {
        if (item.author && item.author.length > 0) {
            return item.author.map(auth => {
                if (auth.literal) return formatHTML ? `<strong>${auth.literal}</strong>` : auth.literal;
                return formatHTML ? `<strong>${auth.family}</strong> ${auth.given ? auth.given[0] + "." : ""}` : `${auth.family} ${auth.given ? auth.given[0] + "." : ""}`;
            }).join(", ");
        }
        if (item.editor && item.editor.length > 0) {
            return item.editor.map(ed => {
                return formatHTML ? `<strong>${ed.family}</strong> ${ed.given ? ed.given[0] + "." : ""} (ed.)` : `${ed.family} ${ed.given ? ed.given[0] + "." : ""} (ed.)`;
            }).join(", ");
        }
        return item.title || "Anonymus";
    }
});

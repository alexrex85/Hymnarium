document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get("search");
    
    const hash = window.location.hash;

    if (!query && !hash) return;

    let firstMatch = null;

    if (query) {
        const decodedQuery = decodeURIComponent(query);
        
        const words = decodedQuery
            .split(/\s+/)
            .filter(w => !["AND", "OR", "NOT", "XOR"].includes(w.toUpperCase()));
        
        const lineTexts = document.querySelectorAll(".line-text");
        
        lineTexts.forEach(el => {
            let html = el.innerHTML;
            let matched = false;
            
            words.forEach(word => {
                if (word.trim().length === 0) return;
                
                const regex = new RegExp("(" + word + ")", "gi");
                
                if (regex.test(html)) {
                    matched = true;
                }
                html = html.replace(regex, "<mark>$1</mark>");
            });
            
            el.innerHTML = html;
            
            if (matched && !firstMatch && !hash) {
                firstMatch = el.closest(".line") || el;
            }
        });
    }

    if (hash) {
        const targetId = hash.substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            firstMatch = targetElement;
        }
    }

    if (firstMatch) {
        window.scrollTo(0, 0);

        setTimeout(() => {
            firstMatch.scrollIntoView({ 
                behavior: "smooth", 
                block: "center"
            });
        }, 150);
    }
});

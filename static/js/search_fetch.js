// Typewriter effect for auto-typing
function typeWriterEffect(text, element, callback) {
    let index = 0;
    const speed = 100;

    function type() {
        if (index < text.length) {
            element.value += text.charAt(index);
            index++;
            setTimeout(type, speed);
        } else {
            callback(); // Trigger search after typing ends
        }
    }

    element.value = "";
    type();
}

// === Dual Trigger Detection ===
function detectFetchTrigger(message) {
    const input = document.getElementById("search-bar");

    // 1. First check structured marker (recommended LLM format)
    const match = message.match(/__FETCH_FROM_(JUMIA|AMAZON)__(.+)/i);
    if (match) {
        const site = match[1].toLowerCase();
        let product = match[2].trim();

        if (product.toLowerCase() === "it" || product === "") {
            const last = sessionStorage.getItem("lastSuggestedProduct");
            if (last) {
                typeTextAndSearch(last, site);
                return;
            }
        }

        const cleaned = cleanProductName(product);
        const formatted = capitalizeProductName(cleaned, true);
        sessionStorage.setItem("lastSuggestedProduct", formatted);
        typeTextAndSearch(formatted, site);
        return;
    }

    // 2. If no marker found, try detecting natural phrases like: "Searching for X on Amazon..."
    const lowerMsg = message.toLowerCase();

    if (lowerMsg.includes("searching for") && lowerMsg.includes("on amazon")) {
        const regex = /searching for "(.*?)" on amazon/i;
        const productMatch = message.match(regex);
        let product = "";

        if (productMatch && productMatch[1]) {
            product = productMatch[1].trim();
        }

        if (!product || product === "it") {
            const last = sessionStorage.getItem("lastSuggestedProduct");
            if (last) {
                typeTextAndSearch(last, "amazon");
                return;
            }
        }

        const cleaned = cleanProductName(product);
        const formatted = capitalizeProductName(cleaned, true);
        sessionStorage.setItem("lastSuggestedProduct", formatted);
        typeTextAndSearch(formatted, "amazon");
    }
}


// Auto-fill input with typewriter effect and perform search
function typeTextAndSearch(productName, site = "") {
    const input = document.getElementById("search-bar");
    const capitalizedName = capitalizeProductName(productName); // Ensure title-case
    input.value = "";
    let i = 0;
    const typingSpeed = 80;

    const typeChar = () => {
        if (i < capitalizedName.length) {
            input.value += capitalizedName.charAt(i);
            i++;
            setTimeout(typeChar, typingSpeed);
        } else {
            // Inject site into search logic if applicable
            if (site) {
                const dropdown = document.getElementById("specific-site-dropdown");
                if (dropdown) dropdown.value = site;
                const categorySelect = document.getElementById("category-select");
                if (categorySelect) categorySelect.value = "specific-sites";
            }

            setTimeout(() => {
                const searchBtn = document.querySelector(".search-btn");
                if (searchBtn) {
                    searchBtn.click(); // Click the actual search button
                } else if (typeof performSearch === "function") {
                    performSearch(); // Fallback if button is not found
                } else {
                    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
                }
            }, 300);
        }
    };

    typeChar();
}

// Clean product name for consistency
function cleanProductName(text) {
    const stopWords = [
        "fetch", "get", "find", "look for", "search for", "buy", "order",
        "to", "show me", "get me", "i want", "i want to", "i want to buy", "find me",
        "the", "a", "an", "from jumia", "on jumia", "from amazon", "on amazon", "in", "for", "it"
    ];

    let cleaned = text.toLowerCase();

    stopWords.forEach(word => {
        const pattern = new RegExp(`\\b${word}\\b`, "gi");
        cleaned = cleaned.replace(pattern, "");
    });

    return cleaned.replace(/\s{2,}/g, " ").trim();
}

// Capitalize or standardize product names
function capitalizeProductName(text, isFromLLM = false) {
    if (isFromLLM) return text.trim();

    const knownWords = {
        "iphone": "iPhone",
        "t-shirt": "T-shirt",
        "ipad": "iPad",
        "macbook": "MacBook",
        "airpods": "AirPods",
        "playstation": "PlayStation",
        "ps5": "PS5",
        "ps4": "PS4",
        "samsung": "Samsung",
        "xiaomi": "Xiaomi",
        "huawei": "Huawei",
        "nokia": "Nokia",
        "tecno": "Tecno",
        "infinix": "Infinix",
        "laptop": "Laptop",
        "smartwatch": "Smartwatch",
        "earbuds": "Earbuds"
    };

    const correctWord = (word) => {
        const lowerWord = word.toLowerCase();
        if (knownWords[lowerWord]) return knownWords[lowerWord];

        let minDistance = Infinity;
        let bestMatch = word;

        for (let key in knownWords) {
            const dist = levenshtein(lowerWord, key);
            if (dist < minDistance && dist <= 2) {
                minDistance = dist;
                bestMatch = key;
            }
        }

        return knownWords[bestMatch] || (word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
    };

    return text
        .split(" ")
        .map(correctWord)
        .join(" ");
}

// Levenshtein distance for typo correction
function levenshtein(a, b) {
    const dp = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
    for (let i = 0; i <= a.length; i++) dp[i][0] = i;
    for (let j = 0; j <= b.length; j++) dp[0][j] = j;

    for (let i = 1; i <= a.length; i++) {
        for (let j = 1; j <= b.length; j++) {
            if (a[i - 1] === b[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + Math.min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1]
                );
            }
        }
    }

    return dp[a.length][b.length];
}

// === Hook for chatbot/voicebot to intercept LLM messages ===
function handleBotResponse(message) {
    // Optional: Only call if function exists
    if (typeof addBotMessage === "function") {
        addBotMessage(message);
    } else {
        console.warn("⚠️ addBotMessage() not defined – skipping chat UI render.");
    }

    // Always detect triggers
    detectFetchTrigger(message);
}


// Expose for chatbot/voicebot
window.cleanProductName = cleanProductName;
window.detectFetchTrigger = detectFetchTrigger;
window.typeTextAndSearch = typeTextAndSearch;
window.handleBotResponse = handleBotResponse;

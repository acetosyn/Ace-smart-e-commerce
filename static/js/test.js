document.addEventListener("DOMContentLoaded", () => {
    const micButton = document.getElementById("mic-button");
    const voiceChatDisplay = document.getElementById("voice-chat-display");
    const languageSelect = document.getElementById("language-select");

    let recognition;
    let isRecording = false;
    let selectedLanguage = "en";

    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
        alert("⚠ Your browser does not support voice recognition. Try using Google Chrome.");
        return;
    }

    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isRecording = true;
        micButton.classList.add("recording");
        micButtonAnimation.play();
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim();
        if (transcript) {
            displayUserMessage(transcript);
    
            // ✅ Only for phrases like "get it from Jumia"
            if (typeof detectJumiaTrigger === "function") {
                detectJumiaTrigger(transcript);
            }
    
            const speakingBubble = createSpeakingBubble();
    
            // Optional fallback direct product searches (not for Jumia trigger)
            const lower = transcript.toLowerCase();
            const searchTriggers = [
                "search for", "i want to buy", "look for", "get me", "find", "show me",
                "search on jumia"
            ];
            const trigger = searchTriggers.find(trigger => lower.includes(trigger));
            if (trigger) {
                const productRaw = lower.split(trigger)[1]?.trim();
                if (productRaw && typeof typeAndSearchProduct === "function") {
                    const fixedProduct = capitalizeProductName(productRaw);
                    typeAndSearchProduct(fixedProduct, "auto");  // ✅ Category explicitly set to "auto"
                }
            }
    
            fetchBotResponse(transcript, speakingBubble);
        }
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        alert("⚠ Speech recognition error. Try again.");
    };

    recognition.onend = () => {
        isRecording = false;
        micButton.classList.remove("recording");
        micButtonAnimation.stop();
    };

    micButton.addEventListener("click", () => {
        if (isRecording) recognition.stop();
        else recognition.start();
    });

    languageSelect.addEventListener("change", (event) => {
        selectedLanguage = event.target.value;
        recognition.lang = getSpeechRecognitionLang(selectedLanguage);
    });

    function getSpeechRecognitionLang(lang) {
        return {
            "en": "en-US",
            "es": "es-ES",
            "fr": "fr-FR",
            "it": "it-IT"
        }[lang] || "en-US";
    }

    async function fetchBotResponse(userMessage, speakingBubble) {
        try {
            const response = await fetch("/voice", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage, language: selectedLanguage })
            });

            if (!response.ok || !response.body) throw new Error("Failed to fetch response");

            voiceChatDisplay.removeChild(speakingBubble);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botMessageDiv = displayBotMessage("");
            let botResponseText = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                botResponseText += chunk;
                await typeWriterEffect(botMessageDiv, chunk);
                voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;
            }

            // ✅ Trigger typing if bot says __FETCH_FROM_JUMIA__
            if (typeof detectJumiaTrigger === "function") {
                detectJumiaTrigger(botResponseText);
            }

            const ttsResponse = await fetch("/generate_tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: botResponseText })
            });

            if (!ttsResponse.ok) throw new Error("TTS fetch failed");

            const audioBlob = await ttsResponse.blob();
            const audioURL = URL.createObjectURL(audioBlob);
            playAudio(audioURL);
        } catch (error) {
            console.error("❌ Error fetching or playing bot response:", error);
        }
    }

    function displayUserMessage(message) {
        const messageRow = document.createElement("div");
        messageRow.classList.add("d-flex", "flex-row", "p-3", "justify-content-end");

        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat", "user-message", "p-3");
        messageDiv.textContent = message;

        messageRow.appendChild(messageDiv);
        voiceChatDisplay.appendChild(messageRow);
        voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;
    }

    function createSpeakingBubble() {
        const speakingRow = document.createElement("div");
        speakingRow.classList.add("d-flex", "flex-row", "p-3", "speaking-row");

        const botAvatar = document.createElement("img");
        botAvatar.src = "/static/images/bot.jpg";
        botAvatar.classList.add("bot-avatar");

        const speakingBubble = document.createElement("div");
        speakingBubble.classList.add("chat", "bot-message", "p-3", "speaking-bubble");
        speakingBubble.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;

        speakingRow.appendChild(botAvatar);
        speakingRow.appendChild(speakingBubble);
        voiceChatDisplay.appendChild(speakingRow);
        voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;

        return speakingRow;
    }

    async function typeWriterEffect(element, text, speed = 50) {
        for (let i = 0; i < text.length; i++) {
            element.textContent += text[i];
            await new Promise(resolve => setTimeout(resolve, speed));
        }
    }

    function playAudio(audioURL) {
        const audio = new Audio(audioURL);
        audio.play().catch(error => console.error("❌ Error playing audio:", error));
    }

    function capitalizeProductName(text) {
        const knownWords = {
            "iphone": "iPhone", "t-shirt": "T-shirt", "ipad": "iPad", "macbook": "MacBook",
            "airpods": "AirPods", "playstation": "PlayStation", "ps5": "PS5", "ps4": "PS4",
            "samsung": "Samsung", "xiaomi": "Xiaomi", "huawei": "Huawei", "nokia": "Nokia",
            "tecno": "Tecno", "infinix": "Infinix", "laptop": "Laptop", "smartwatch": "Smartwatch",
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
});

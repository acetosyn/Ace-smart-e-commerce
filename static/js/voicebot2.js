document.addEventListener("DOMContentLoaded", () => {
    const voiceChatIcon = document.getElementById("voice-chat-icon");
    const voiceChatContainer = document.getElementById("voice-chat-container");
    const closeVoiceChat = document.getElementById("close-voice-chat");
    const micButton = document.getElementById("mic-button");
    const voiceChatDisplay = document.getElementById("voice-chat-display");

    voiceChatIcon.addEventListener("click", (e) => {
        e.stopPropagation();
        const isActive = voiceChatContainer.classList.contains("active");
        voiceChatContainer.classList.toggle("active", !isActive);
    });

    closeVoiceChat.addEventListener("click", () => {
        voiceChatContainer.classList.remove("active");
    });

    const micAnimation = lottie.loadAnimation({
        container: voiceChatIcon,
        renderer: "svg",
        loop: true,
        autoplay: true,
        path: "/static/mic2.json",
    });

    window.micButtonAnimation = lottie.loadAnimation({
        container: micButton,
        renderer: "svg",
        loop: true,
        autoplay: false,
        path: "/static/mic2.json",
    });

    document.getElementById("clear-voice-chat").addEventListener("click", () => {
        voiceChatDisplay.innerHTML = "";
    });

    document.getElementById("clear-chat").addEventListener("click", () => {
        document.getElementById("chat-display").innerHTML = "";
    });

    const initialBotMessage = "Hi!... I'm Ace, your e-commerce voice assistant... Kindly click the mic button to speak to me.";

    function fetchInitialTTS(message) {
        fetch("/generate_tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: message })
        })
        .then(response => response.blob())
        .then(audioBlob => {
            const audioURL = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioURL);
            audio.play().catch(error => console.error("❌ Error playing initial TTS:", error));
        })
        .catch(error => console.error("❌ Error fetching initial TTS:", error));
    }

    fetchInitialTTS(initialBotMessage);
});

function displayUserMessage(message) {
    const voiceChatDisplay = document.getElementById("voice-chat-display");
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
    const voiceChatDisplay = document.getElementById("voice-chat-display");
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

function displayBotMessage(message) {
    const voiceChatDisplay = document.getElementById("voice-chat-display");
    const messageRow = document.createElement("div");
    messageRow.classList.add("d-flex", "flex-row", "p-3");

    const avatar = document.createElement("img");
    avatar.classList.add("bot-avatar");
    avatar.src = "/static/images/bot.jpg";

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chat", "bot-message", "p-3");
    messageDiv.textContent = message;

    messageRow.appendChild(avatar);
    messageRow.appendChild(messageDiv);
    voiceChatDisplay.appendChild(messageRow);
    voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;

    return messageDiv;
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
                dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
            }
        }
    }

    return dp[a.length][b.length];
}
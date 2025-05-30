document.addEventListener("DOMContentLoaded", () => {
    const voiceChatDisplay = document.getElementById("voice-chat-display");

    window.displayUserMessage = function (message) {
        const messageRow = document.createElement("div");
        messageRow.classList.add("d-flex", "flex-row", "p-3", "justify-content-end");

        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat", "user-message", "p-3");
        messageDiv.textContent = message;

        messageRow.appendChild(messageDiv);
        voiceChatDisplay.appendChild(messageRow);
        voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;
    };

    window.displayBotMessage = function (message) {
        const messageRow = document.createElement("div");
        messageRow.classList.add("d-flex", "flex-row", "p-3");

        const botAvatar = document.createElement("img");
        botAvatar.src = "/static/images/bot.jpg";
        botAvatar.classList.add("bot-avatar");

        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat", "bot-message", "ml-2", "p-3");
        messageDiv.textContent = message;

        messageRow.appendChild(botAvatar);
        messageRow.appendChild(messageDiv);
        voiceChatDisplay.appendChild(messageRow);
        voiceChatDisplay.scrollTop = voiceChatDisplay.scrollHeight;

        return messageDiv;
    };

    window.createSpeakingBubble = function () {
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
    };

    window.typeWriterEffect = async function (element, text, speed = 50) {
        for (let i = 0; i < text.length; i++) {
            element.textContent += text[i];
            await new Promise(resolve => setTimeout(resolve, speed));
        }
    };

    window.levenshtein = function (a, b) {
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
    };

    window.fetchBotResponse = async function (userMessage, speakingBubble) {
        const languageSelect = document.getElementById("language-select");
        const selectedLanguage = languageSelect?.value || "en";

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

            // ✅ NEW: Trigger the auto-type search if response has fetch trigger
            handleBotResponse(botResponseText);

            window.initTTS?.(botResponseText); // Optional TTS
        } catch (error) {
            console.error("❌ Error fetching or speaking bot response:", error);
        }
    };

    window.handleVoiceInput = function (transcript) {
        displayUserMessage(transcript);
        const speakingBubble = createSpeakingBubble();
        fetchBotResponse(transcript, speakingBubble);
    };
});

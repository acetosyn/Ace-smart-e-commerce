document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-btn");
    const chatDisplay = document.getElementById("chat-display");
    const chatIcon = document.getElementById("chat-icon");
    const chatbotContainer = document.getElementById("chatbot-container");

    // Toggle chatbot visibility
    chatIcon.addEventListener("click", () => {
        chatbotContainer.classList.toggle("active");
        chatbotContainer.style.display = chatbotContainer.classList.contains("active") ? "block" : "none";
    });

    document.getElementById("close-chat").addEventListener("click", () => {
        chatbotContainer.classList.remove("active");
        setTimeout(() => chatbotContainer.style.display = "none", 300);
    });

    // Display user message
    function displayUserMessage(message) {
        const row = document.createElement("div");
        row.classList.add("d-flex", "flex-row", "p-3", "justify-content-end");

        const msg = document.createElement("div");
        msg.classList.add("chat", "user-message", "p-3");
        msg.textContent = message;

        row.appendChild(msg);
        chatDisplay.appendChild(row);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    // Show typing indicator
    function createTypingBubble() {
        const row = document.createElement("div");
        row.classList.add("d-flex", "flex-row", "p-3", "typing-row");

        const avatar = document.createElement("img");
        avatar.src = "/static/images/bot.jpg";
        avatar.classList.add("bot-avatar");

        const bubble = document.createElement("div");
        bubble.classList.add("chat", "bot-message", "p-3", "typing-bubble");
        bubble.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;

        row.appendChild(avatar);
        row.appendChild(bubble);
        chatDisplay.appendChild(row);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        return row;
    }

    // Display bot message container
    function displayBotMessage() {
        const row = document.createElement("div");
        row.classList.add("d-flex", "flex-row", "p-3");

        const avatar = document.createElement("img");
        avatar.src = "/static/images/bot.jpg";
        avatar.classList.add("bot-avatar");

        const msg = document.createElement("div");
        msg.classList.add("chat", "bot-message", "p-3");
        msg.textContent = "";

        row.appendChild(avatar);
        row.appendChild(msg);
        chatDisplay.appendChild(row);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        return msg;
    }

    // Typing effect for bot reply
    async function typeWriterEffect(element, text, speed = 50) {
        for (let char of text) {
            element.textContent += char;
            await new Promise(resolve => setTimeout(resolve, speed));
        }
    }

    // Main message send logic
    async function sendMessage() {
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
    
        displayUserMessage(userMessage);
        userInput.value = "";
    
        const typingBubble = createTypingBubble();
    
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage })
            });
    
            if (!response.ok) throw new Error("Chat response failed");
    
            chatDisplay.removeChild(typingBubble);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
    
            const botMsgDiv = displayBotMessage();
            let fullBotResponse = "";
    
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
    
                const chunk = decoder.decode(value, { stream: true });
                fullBotResponse += chunk;
                await typeWriterEffect(botMsgDiv, chunk);
                chatDisplay.scrollTop = chatDisplay.scrollHeight;
            }
    
            // ✅ Extract and store product for auto-type search
            const fetchMatch = fullBotResponse.match(/__FETCH_FROM_JUMIA__(.+)/);
            if (fetchMatch && fetchMatch[1]) {
                const cleanProduct = fetchMatch[1].trim();
                sessionStorage.setItem("lastSuggestedProduct", cleanProduct);
            }
    
            // ✅ Detect trigger and type-search
            detectJumiaTrigger(fullBotResponse);
    
        } catch (err) {
            console.error("❌ Error:", err);
            chatDisplay.removeChild(typingBubble);
            const errorDiv = displayBotMessage();
            errorDiv.textContent = "⚠ Sorry, something went wrong.";
        }
    }
    

    // Show welcome message
    function showInitialMessage() {
        chatDisplay.innerHTML = "";

        const row = document.createElement("div");
        row.classList.add("d-flex", "flex-row", "p-3", "first-response");

        const avatar = document.createElement("img");
        avatar.src = "/static/images/bot.jpg";
        avatar.classList.add("bot-avatar");

        const msg = document.createElement("div");
        msg.classList.add("chat", "bot-message", "p-3");
        msg.textContent = "Hi! I'm Ace, your e-commerce assistant 🤖. What can I find for you today?";

        row.appendChild(avatar);
        row.appendChild(msg);
        chatDisplay.appendChild(row);
    }

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    showInitialMessage();
});

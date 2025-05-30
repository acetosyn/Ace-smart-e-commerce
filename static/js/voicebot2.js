document.addEventListener("DOMContentLoaded", () => {
    const voiceChatIcon = document.getElementById("voice-chat-icon");
    const voiceChatContainer = document.getElementById("voice-chat-container");
    const closeVoiceChat = document.getElementById("close-voice-chat");
    const micButton = document.getElementById("mic-button");
    const voiceChatDisplay = document.getElementById("voice-chat-display");

    // Toggle Voice Chat Visibility
    voiceChatIcon.addEventListener("click", (e) => {
        e.stopPropagation();
        const isActive = voiceChatContainer.classList.contains("active");
        voiceChatContainer.classList.toggle("active", !isActive);
    });

    closeVoiceChat.addEventListener("click", () => {
        voiceChatContainer.classList.remove("active");
    });

    // Load Lottie animations
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

    // Clear Chat Buttons
    document.getElementById("clear-voice-chat").addEventListener("click", () => {
        voiceChatDisplay.innerHTML = "";
    });

    document.getElementById("clear-chat").addEventListener("click", () => {
        document.getElementById("chat-display").innerHTML = "";
    });

    // Initial Bot Greeting with TTS
    const initialBotMessage = "Hi!... I'm Ace, your e-commerce voice assistant... Kindly click the mic button to speak to me.";
    if (typeof initTTS === "function") {
        initTTS(initialBotMessage);
    } else {
        console.warn("initTTS not found. Please ensure voicebot.js is loaded before voicebot2.js");
    }
});

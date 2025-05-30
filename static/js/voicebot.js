document.addEventListener("DOMContentLoaded", () => {
    const micButton = document.getElementById("mic-button");
    const languageSelect = document.getElementById("language-select");

    let recognition;
    let isRecording = false;
    let selectedLanguage = "en";
    let bestVoice = null;

    function cacheBestVoice() {
        const voices = window.speechSynthesis.getVoices();
        const preferredVoices = [
            'Microsoft Aria Online', 'Microsoft Jenny Online', 'Microsoft Zira Desktop',
            'Google UK English Female', 'Google US English'
        ];
        bestVoice = voices.find(v => preferredVoices.some(name => v.name.includes(name))) ||
                    voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
                    voices[0];
    }

    function sanitizeTTS(text) {
        const emojiRegex = /([\u231A-\u231B]|[\u23E9-\u23EC]|[\u23F0-\u23F3]|[\u25FD-\u25FE]|[\u2600-\u27BF]|[\u2934-\u2935]|[\u2B05-\u2B07]|[\u3030\u303D]|[\u3297\u3299]|[\uD83C-\uDBFF\uDC00-\uDFFF]|[\uFE00-\uFE0F])/g;
        let cleaned = text.replace(emojiRegex, '');
        cleaned = cleaned.replace(/__FETCH_FROM_[A-Z]+__/g, '');
        cleaned = cleaned.replace(/\b(from\s+\w+)(\s+\1)+/gi, '$1');
        return cleaned.replace(/\s{2,}/g, ' ').trim();
    }

    function speakText(text) {
        const synth = window.speechSynthesis;
        if (synth.speaking) synth.cancel();
        const cleanText = sanitizeTTS(text);
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.voice = bestVoice;
        utterance.pitch = 1;
        utterance.rate = 1;
        synth.speak(utterance);
    }

    function initTTS(text) {
        const synth = window.speechSynthesis;
        const tryLoad = () => {
            if (synth.getVoices().length > 0) {
                cacheBestVoice();
                speakText(text);
            } else {
                setTimeout(tryLoad, 200);
            }
        };
        tryLoad();
    }

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
            window.handleVoiceInput?.(transcript);  // Call external handler
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
        recognition.lang = {
            "en": "en-US", "es": "es-ES", "fr": "fr-FR", "it": "it-IT"
        }[selectedLanguage] || "en-US";
    });

    window.initTTS = initTTS;  // expose TTS function globally
});

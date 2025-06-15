document.addEventListener("DOMContentLoaded", () => {
  const micButton = document.getElementById("mic-button");
  const languageSelect = document.getElementById("language-select");

  let recognition;
  let isRecording = false;
  let selectedLanguage = "en";
  let bestVoice = null;

  const isiOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
  const isAndroid = /Android/i.test(navigator.userAgent);

  function cacheBestVoice() {
    const voices = window.speechSynthesis.getVoices();
    const preferredVoices = [
      'Google UK English Female', 'Google US English',
      'Microsoft Aria Online', 'Microsoft Jenny Online', 'Microsoft Zira Desktop',
      'Samantha', 'Karen', 'Moira'  // Apple voices
    ];
    bestVoice = voices.find(v => preferredVoices.some(name => v.name.includes(name))) ||
                voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
                voices.find(v => v.lang.startsWith('en')) ||
                voices[0];
  }

  function sanitizeTTS(text) {
    return text
      .replace(/([\u231A-\uDFFF])/g, '')
      .replace(/__FETCH_FROM_[A-Z]+__/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  function speakText(text) {
    const synth = window.speechSynthesis;
    if (!text) return;

    const cleanText = sanitizeTTS(text);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = bestVoice;
    utterance.pitch = 1.1;
    utterance.rate = 1.05;

    if (synth.speaking) synth.cancel();

    // iOS/Safari requires user interaction, but we allow only one listener
    if (isiOS && !window._ttsPrimed) {
      const unlock = () => {
        synth.speak(new SpeechSynthesisUtterance(" "));
        window._ttsPrimed = true;
        document.body.removeEventListener("click", unlock);
      };
      document.body.addEventListener("click", unlock);
    }

    synth.speak(utterance);
  }

  function initTTS(text) {
    const synth = window.speechSynthesis;

    const tryLoad = (attempts = 0) => {
      const voices = synth.getVoices();
      if (voices.length > 0 || attempts > 5) {
        cacheBestVoice();
        speakText(text);
      } else {
        setTimeout(() => tryLoad(attempts + 1), 200);
      }
    };

    tryLoad();
  }

  // Expose globally to call when bot replies
  window.initTTS = initTTS;

  // Speech recognition
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
    micButtonAnimation?.play?.();
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (transcript) {
      window.handleVoiceInput?.(transcript);
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    alert("⚠ Speech recognition error. Try again.");
  };

  recognition.onend = () => {
    isRecording = false;
    micButton.classList.remove("recording");
    micButtonAnimation?.stop?.();
  };

  micButton.addEventListener("click", () => {
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
      initTTS("Voice assistant activated. Listening now.");
    }
  });

  languageSelect.addEventListener("change", (event) => {
    selectedLanguage = event.target.value;
    recognition.lang = {
      "en": "en-US", "es": "es-ES", "fr": "fr-FR", "it": "it-IT"
    }[selectedLanguage] || "en-US";
  });
});

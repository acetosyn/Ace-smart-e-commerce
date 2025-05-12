document.addEventListener("DOMContentLoaded", () => {
  const messages = [
    "🛍️ Looking for the best deals online? ACE compares top stores so you don’t have to.",
    "📦 Discover high-rated products from Jumia, Amazon, Temu, and more — all in one place.",
    "✨ Save time and money — ACE scans top e-commerce platforms to find what you need.",
    "🔍 Type in any product, and let ACE fetch the best prices and reviews instantly.",
    "💬 Not sure what to search? Chat with our smart assistant to help you find the perfect product.",
    "🎙️ Try voice search with our Voicebot — just speak, and ACE will find it for you."
  ];

  const typewriter = document.getElementById("typewriter");
  let messageIndex = 0;
  let charIndex = 0;

  function type() {
    const currentMessage = messages[messageIndex];
    const visibleText = currentMessage.substring(0, charIndex);
    
    // Set the typed text with cursor
    typewriter.innerHTML = `${visibleText}<span class="cursor"></span>`; 

    if (charIndex < currentMessage.length) {
      charIndex++;
      setTimeout(type, 40);  // Continue typing the next character
    } else {
      // Once typing finishes, wait and then clear the text for the next message
      setTimeout(() => {
        charIndex = 0;
        messageIndex = (messageIndex + 1) % messages.length;
        type();  // Start typing the next message
      }, 10000); // Pause after each message
    }
  }

  type(); // Start typing the first message
});

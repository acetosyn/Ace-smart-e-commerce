document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const loginTab = document.getElementById("loginTab");
  const signupTab = document.getElementById("signupTab");

  loginTab.addEventListener("click", () => {
    loginForm.classList.add("active");
    signupForm.classList.remove("active");
    loginTab.classList.add("active");
    signupTab.classList.remove("active");
  });

  signupTab.addEventListener("click", () => {
    signupForm.classList.add("active");
    loginForm.classList.remove("active");
    signupTab.classList.add("active");
    loginTab.classList.remove("active");
  });
});


// Typewriter effect
function initTypewriter(targetId, messages) {
  const element = document.getElementById(targetId);
  let messageIndex = 0;
  let charIndex = 0;

  function type() {
    const current = messages[messageIndex];
    const visibleText = current.substring(0, charIndex);
    element.innerHTML = `${visibleText}<span class="cursor"></span>`;

    if (charIndex < current.length) {
      charIndex++;
      setTimeout(type, 40);
    } else {
      setTimeout(() => {
        charIndex = 0;
        messageIndex = (messageIndex + 1) % messages.length;
        type();
      }, 3000);
    }
  }

  type();
}

// Initialize for login and signup
document.addEventListener("DOMContentLoaded", () => {
  initTypewriter("login-typewriter", ["Please login to continue."]);
  initTypewriter("signup-typewriter", ["Create your account to get started."]);
});

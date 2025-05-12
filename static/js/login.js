document.addEventListener("DOMContentLoaded", function () {
    const container = document.querySelector(".cont");
    const toggleButton = document.querySelector(".img-btn");

    toggleButton.addEventListener("click", function () {
        container.classList.toggle("s-signup");
    });

    // Smooth Text Animation
    document.querySelectorAll("h2, label span").forEach((element) => {
        element.style.opacity = "0";
        element.style.transform = "translateY(-20px)";
        setTimeout(() => {
            element.style.opacity = "1";
            element.style.transform = "translateY(0)";
        }, 500);
    });

    // Ensure flashed messages are displayed
    const messages = JSON.parse(document.getElementById("flashed-messages").textContent || "[]");
    if (messages.length > 0) {
        messages.forEach((message) => {
            alert(message);
        });
    }
});

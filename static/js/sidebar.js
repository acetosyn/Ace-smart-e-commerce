document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector(".sidebar");
    const toggleButton = document.createElement("button");
    
    toggleButton.innerHTML = "☰";
    toggleButton.classList.add("sidebar-toggle");
    document.body.appendChild(toggleButton);

    toggleButton.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed");
        toggleButton.innerHTML = sidebar.classList.contains("collapsed") ? "☰ Expand" : "✖ Collapse";
    });

    // Collapse sidebar by default
    sidebar.classList.add("collapsed");
    toggleButton.innerHTML = "☰ Expand";
});


document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector(".sidebar");
    const toggleButton = document.createElement("button");

    toggleButton.innerHTML = "☰";
    toggleButton.classList.add("sidebar-toggle");
    document.body.appendChild(toggleButton);

    toggleButton.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed");

        // Adjust button text
        toggleButton.innerHTML = sidebar.classList.contains("collapsed") ? "☰ Expand" : "✖ Collapse";

        // Adjust main content width
        document.querySelector(".main-content").style.marginLeft = 
            sidebar.classList.contains("collapsed") ? "0" : "150px";
    });

    // Collapse sidebar by default
    sidebar.classList.add("collapsed");
    toggleButton.innerHTML = "☰ Expand";
});

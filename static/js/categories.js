const categories = {
    laptop: ["HP Laptop", "Sony Laptop", "Samsung Laptop", "Dell Laptop"],
    phones: ["iPhone", "Samsung Galaxy", "Infinix Note", "Tecno Spark"],
    fashion: ["Men's Shoes", "Women's Bags", "T-Shirts", "Suits"],
    electronics: ["Smart TV", "Soundbar", "Home Theater"]
  };
  
  const input = document.getElementById("searchInput"); // your input field
  const autocompleteBox = document.getElementById("autocompleteBox");
  
  input.addEventListener("input", function () {
    const query = this.value.toLowerCase();
    autocompleteBox.innerHTML = ""; // Clear previous
  
    if (query.length === 0) {
      autocompleteBox.style.display = "none";
      return;
    }
  
    let matches = [];
  
    Object.values(categories).forEach(arr => {
      matches.push(...arr.filter(item => item.toLowerCase().includes(query)));
    });
  
    if (matches.length > 0) {
      matches.slice(0, 8).forEach(item => {
        const div = document.createElement("div");
        div.classList.add("autocomplete-item");
        div.textContent = item;
        div.addEventListener("click", () => {
          input.value = item;
          autocompleteBox.innerHTML = "";
          autocompleteBox.style.display = "none";
        });
        autocompleteBox.appendChild(div);
      });
      autocompleteBox.style.display = "block";
    } else {
      autocompleteBox.style.display = "none";
    }
  });
  


function handleCategoryChange() {
  const category = document.getElementById("categorySelect").value;
  const siteDropdown = document.getElementById("specificSitesDropdown");

  if (category === "specific-sites") {
    siteDropdown.classList.remove("hidden");
    siteDropdown.focus(); // Optional: automatically focus dropdown
  } else {
    siteDropdown.classList.add("hidden");
  }
}

// Optional: hide dropdown after user selects from it
document.getElementById("specificSitesDropdown").addEventListener("change", () => {
  const category = document.getElementById("categorySelect").value;
  if (category === "specific-sites") {
    // Auto-hide after selection
    document.getElementById("specificSitesDropdown").classList.add("hidden");
  }
});

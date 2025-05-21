let categorySuggestions = {};
let currentFocus = -1;
let selectedSpecificSite = null;

const searchInput = document.getElementById("search-bar");
const suggestionBox = document.getElementById("suggestions");
const categorySelect = document.getElementById("categorySelect");
const specificSitesDropdown = document.getElementById("specificSitesDropdown");
const searchResults = document.getElementById("searchResults");

// Load category autocomplete
fetch('/static/data/categories.json')
  .then(res => res.json())
  .then(data => categorySuggestions = data)
  .catch(err => console.error("❌ Failed to load categories.json:", err));

// Autocomplete logic
searchInput.addEventListener("input", function () {
  const input = this.value.toLowerCase();
  suggestionBox.innerHTML = "";
  currentFocus = -1;

  if (!input) return;

  const matched = Object.entries(categorySuggestions)
    .flatMap(([key, items]) => items.filter(item => item.toLowerCase().includes(input)));

  const unique = [...new Set(matched)];

  unique.forEach(item => {
    const option = document.createElement("div");
    option.className = "autocomplete-item";
    option.textContent = item;
    option.onclick = () => {
      searchInput.value = item;
      suggestionBox.innerHTML = "";
    };
    suggestionBox.appendChild(option);
  });
});

searchInput.addEventListener("keydown", function (e) {
  const items = suggestionBox.getElementsByClassName("autocomplete-item");
  if (!items.length) return;

  if (e.key === "ArrowDown") {
    currentFocus++;
    highlight(items);
  } else if (e.key === "ArrowUp") {
    currentFocus--;
    highlight(items);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (currentFocus > -1 && items[currentFocus]) {
      items[currentFocus].click();
    } else {
      performSearch();
    }
  }
});

function highlight(items) {
  Array.from(items).forEach(item => item.classList.remove("autocomplete-active"));
  if (currentFocus >= items.length) currentFocus = 0;
  if (currentFocus < 0) currentFocus = items.length - 1;
  items[currentFocus].classList.add("autocomplete-active");
  items[currentFocus].scrollIntoView({ block: "nearest" });
}

const loaderHTML = `
  <div class="lottie-loader" id="lottieLoader"></div>
  <div class="loading-text">⏳ Please wait, fetching products...</div>
`;

function rememberSuggestedProduct(name) {
  sessionStorage.setItem("lastSuggestedProduct", name);
}

function performSearch() {
  const query = searchInput.value.trim();
  const category = categorySelect.value || "auto";

  if (!searchResults) {
    console.error("Element #searchResults not found.");
    return;
  }

  if (!query) {
    searchResults.innerHTML = `<div class="error">❌ Please enter a product name.</div>`;
    return;
  }

  let specificSite = null;

  if (category === "specific-sites") {
    specificSite = selectedSpecificSite;
    console.log("📌 Category is specific-sites. selectedSpecificSite =", selectedSpecificSite);
    if (!specificSite) {
      searchResults.innerHTML = `<div class="error">❌ Please select a site to search from.</div>`;
      return;
    }
  } else if (category !== "ratings" && category !== "non-ratings") {
    specificSite = category;
  }

  suggestionBox.innerHTML = "";
  searchInput.blur();
  rememberSuggestedProduct(query);
  searchResults.classList.remove("hidden");
  searchResults.innerHTML = loaderHTML;

  lottie.loadAnimation({
    container: document.getElementById("lottieLoader"),
    renderer: "svg",
    loop: true,
    autoplay: true,
    path: "/static/data/animation.json"
  });

  console.log("🚀 Fetching from:", { query, category, specificSite });

  fetch("/search-products", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query, category, specificSite })
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        searchResults.innerHTML = `<div class="error">❌ ${data.error}</div>`;
        return;
      }

      const allProducts = data.products.flatMap(site => site.data || []);

      if (!allProducts.length) {
        searchResults.innerHTML = "<div class='error'>No products found.</div>";
        return;
      }

      const seen = new Set();
      const uniqueProducts = allProducts.filter(p => {
        const key = `${p.name}|${p.price}|${p.image}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      const cards = uniqueProducts.map(p => {
        const siteClass = p.source?.toLowerCase() || "";
        return `
          <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 ${siteClass}">
              <img src="${p.image}" class="card-img-top" alt="${p.name}">
              <div class="card-body">
                <h5 class="card-title">${p.name}</h5>
                <p class="card-text">Price: ${p.price}</p>
                ${p.rating !== undefined ? `<p class="card-text">Rating: ${p.rating} ⭐</p>` : ""}
                <p class="card-text"><strong>Source:</strong> ${capitalize(p.source)}</p>
                <div class="d-flex justify-content-between align-items-center gap-2 mt-3">
                  <a href="${p.url}" class="btn btn-primary" target="_blank">Buy Now</a>
                  <button class="btn btn-danger btn-sm clear-btn" onclick="clearSearch()">Clear</button>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join("");

      searchResults.innerHTML = `
        <div class="container">
          <div class="row">${cards}</div>
        </div>
      `;
    })
    .catch(err => {
      console.error("Fetch error:", err);
      searchResults.innerHTML = "<div class='error'>Error fetching products.</div>";
    });
}

function clearSearch() {
  searchInput.value = "";
  categorySelect.value = "ratings";
  document.getElementById("searchResults").innerHTML = "";
  document.getElementById("searchResults").classList.add("hidden");
  document.getElementById("clearWrapper").classList.add("hidden");
  sessionStorage.removeItem("lastSuggestedProduct");
}

function handleCategoryChange() {
  const category = categorySelect.value;
  if (category === "specific-sites") {
    specificSitesDropdown.classList.remove("hidden");
    specificSitesDropdown.value = "";
    selectedSpecificSite = null;
  } else {
    specificSitesDropdown.classList.add("hidden");
  }
}

specificSitesDropdown.addEventListener("change", function () {
  selectedSpecificSite = this.value;
  console.log("✅ Site selected from dropdown:", selectedSpecificSite);
});

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : "";
}

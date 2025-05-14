let categorySuggestions = {};
let currentFocus = -1;

// Load autocomplete category data
fetch('/static/data/categories.json')
  .then(response => response.json())
  .then(data => {
    categorySuggestions = data;
  });

const searchInput = document.getElementById("search-bar");
const suggestionBox = document.getElementById("suggestions");

// Autocomplete logic
searchInput.addEventListener("input", function () {
  const input = this.value.toLowerCase();
  suggestionBox.innerHTML = "";
  currentFocus = -1;

  if (!input) return;

  const matched = Object.entries(categorySuggestions)
    .flatMap(([key, items]) =>
      items.filter(item => item.toLowerCase().includes(input))
    );

  const uniqueMatched = [...new Set(matched)]; // remove duplicates

  if (uniqueMatched.length) {
    uniqueMatched.forEach(item => {
      const option = document.createElement("div");
      option.className = "autocomplete-item";
      option.textContent = item;
      option.onclick = () => {
        searchInput.value = item;
        suggestionBox.innerHTML = "";
      };
      suggestionBox.appendChild(option);
    });
  }
});

// Keyboard navigation for autocomplete
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
      performSearch();  // Manually triggered search
    }
  }
});

function highlight(items) {
  if (!items.length) return;

  for (let i = 0; i < items.length; i++) {
    items[i].classList.remove("autocomplete-active");
  }

  if (currentFocus >= items.length) currentFocus = 0;
  if (currentFocus < 0) currentFocus = items.length - 1;

  items[currentFocus].classList.add("autocomplete-active");
  items[currentFocus].scrollIntoView({ block: "nearest" });
}

// Loader UI
const loaderHTML = `
  <div class="lottie-loader" id="lottieLoader"></div>
  <div class="loading-text">⏳ Please wait, fetching products...</div>
`;

// Wrapper to delegate to search_fetch.js
function detectJumiaCommand(message) {
  if (typeof detectJumiaTrigger === "function") {
    detectJumiaTrigger(message);
  } else {
    console.warn("detectJumiaTrigger not defined.");
  }
}

// Store product in session for voice triggers
function rememberSuggestedProduct(productName) {
  sessionStorage.setItem("lastSuggestedProduct", productName);
}

// Perform product search
function performSearch() {
  const query = document.getElementById("search-bar").value.trim();
  const categorySelect = document.getElementById("categorySelect");
  const category = categorySelect ? categorySelect.value || "auto" : "auto";
  const searchResults = document.getElementById("searchResults");

  if (!searchResults) {
    console.error("Element #searchResults not found.");
    return;
  }

  if (!query) {
    searchResults.innerHTML = `<div class="error">❌ Please enter a product name.</div>`;
    return;
  }

  // Reset UI state
  suggestionBox.innerHTML = "";
  searchInput.blur();
  rememberSuggestedProduct(query);
  searchResults.classList.remove("hidden");
  searchResults.innerHTML = loaderHTML;

  // Lottie loader
  lottie.loadAnimation({
    container: document.getElementById("lottieLoader"),
    renderer: "svg",
    loop: true,
    autoplay: true,
    path: "/static/data/animation.json"
  });

  // Search API call
  fetch("/search-products", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query, category })
  })
    .then(response => response.json())
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

      // Remove duplicates
      const seen = new Set();
      const uniqueProducts = allProducts.filter(p => {
        const key = `${p.name}|${p.price}|${p.image}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      // Generate product cards
      const cards = uniqueProducts.map(p => `
        <div class="col-md-6 col-lg-4 mb-4">
          <div class="card h-100">
            <img src="${p.image}" class="card-img-top" alt="${p.name}">
            <div class="card-body">
              <h5 class="card-title">${p.name}</h5>
              <p class="card-text">Price: ${p.price}</p>
              ${p.rating !== undefined ? `<p class="card-text">Rating: ${p.rating} ⭐</p>` : ""}
              <div class="d-flex justify-content-between align-items-center gap-2 mt-3">
                <a href="${p.url}" class="btn btn-primary" target="_blank">Buy Now</a>
                <button class="btn btn-danger btn-sm clear-btn" onclick="clearSearch()">Clear</button>
              </div>
            </div>
          </div>
        </div>
      `).join("");

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
  document.getElementById("search-bar").value = "";
  document.getElementById("categorySelect").value = "ratings";
  document.getElementById("searchResults").innerHTML = "";
  document.getElementById("searchResults").classList.add("hidden");
  document.getElementById("clearWrapper").classList.add("hidden");
  sessionStorage.removeItem("lastSuggestedProduct");
}

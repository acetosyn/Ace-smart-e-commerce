const categories = {
  laptop: ["HP Laptop", "Sony Laptop", "Samsung Laptop", "Dell Laptop"],
  phones: ["iPhone", "Samsung Galaxy", "Infinix Note", "Tecno Spark"],
  fashion: ["Men's Shoes", "Women's Bags", "T-Shirts", "Suits"],
  electronics: ["Smart TV", "Soundbar", "Home Theater"]
};

const input = document.getElementById("search-bar");
const autocompleteBox = document.getElementById("suggestions");

let currentFocus = -1;

input.addEventListener("input", function () {
  const query = this.value.toLowerCase();
  autocompleteBox.innerHTML = "";
  currentFocus = -1;

  if (!query) {
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

// Keyboard navigation
input.addEventListener("keydown", function (e) {
  const items = autocompleteBox.querySelectorAll(".autocomplete-item");
  if (!items.length) return;

  if (e.key === "ArrowDown") {
    currentFocus = (currentFocus + 1) % items.length;
    setActive(items);
  } else if (e.key === "ArrowUp") {
    currentFocus = (currentFocus - 1 + items.length) % items.length;
    setActive(items);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (currentFocus > -1) {
      items[currentFocus].click();
    }
  }
});

function setActive(items) {
  items.forEach(item => item.classList.remove("autocomplete-active"));
  if (currentFocus >= 0) {
    items[currentFocus].classList.add("autocomplete-active");
    items[currentFocus].scrollIntoView({ block: "nearest" });
  }
}

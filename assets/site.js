let entries = [];

const dialog = document.querySelector("#searchDialog");
const input = document.querySelector("#searchInput");
const results = document.querySelector("#searchResults");
const trigger = document.querySelector("#searchTrigger");

fetch("/search-index.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Search index request failed: ${response.status}`);
    }
    return response.json();
  })
  .then((data) => {
    entries = data.entries;
  })
  .catch(() => {
    trigger.disabled = true;
    trigger.title = "Search index unavailable";
  });

function scoreEntry(entry, words) {
  const title = entry.title.toLowerCase();
  const searchable = [entry.title, entry.kind, entry.text, entry.aliases]
    .join(" ")
    .toLowerCase();
  let score = 0;
  for (const word of words) {
    if (!searchable.includes(word)) {
      return -1;
    }
    score += title.includes(word) ? 5 : 1;
  }
  return score;
}

function resultLink(entry) {
  const link = document.createElement("a");
  const title = document.createElement("strong");
  const kind = document.createElement("span");
  link.className = "search-result";
  link.href = entry.href;
  title.textContent = entry.title;
  kind.textContent = entry.kind;
  link.append(title, kind);
  return link;
}

function render(query) {
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const ranked = entries
    .map((entry) => [entry, scoreEntry(entry, words)])
    .filter(([, score]) => score >= 0)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 12);

  results.replaceChildren();
  if (!ranked.length) {
    const empty = document.createElement("p");
    empty.textContent = "No matching documentation.";
    results.append(empty);
    return;
  }
  results.append(...ranked.map(([entry]) => resultLink(entry)));
}

function openSearch() {
  render("");
  dialog.showModal();
  input.focus();
}

trigger.addEventListener("click", openSearch);
input.addEventListener("input", () => render(input.value));
document.addEventListener("keydown", (event) => {
  const editing = /INPUT|TEXTAREA/.test(document.activeElement.tagName);
  if (event.key === "/" && !dialog.open && !editing) {
    event.preventDefault();
    openSearch();
  }
});

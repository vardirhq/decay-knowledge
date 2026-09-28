let entries = [];
let ranked = [];
let active = 0;

const dialog = document.querySelector("#searchDialog");
const input = document.querySelector("#searchInput");
const results = document.querySelector("#searchResults");
const triggers = document.querySelectorAll("[data-search]");

fetch("/search-index.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Search index request failed: ${response.status}`);
    }
    return response.json();
  })
  .then((data) => {
    entries = data.entries;
    if (dialog.open) render(input.value);
  })
  .catch(() => {
    for (const trigger of triggers) {
      trigger.disabled = true;
      trigger.title = "Search index unavailable";
    }
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

function resultLink(entry, index) {
  const link = document.createElement("a");
  const body = document.createElement("span");
  const title = document.createElement("strong");
  const text = document.createElement("span");
  const kind = document.createElement("span");
  link.className = "search-result";
  link.href = entry.href;
  link.id = `search-result-${index}`;
  link.setAttribute("role", "option");
  link.addEventListener("mouseenter", () => select(index));
  body.className = "body";
  text.className = "text";
  kind.className = "kind";
  title.textContent = entry.title;
  text.textContent = entry.text.slice(0, 160);
  kind.textContent = entry.kind;
  body.append(title, text);
  link.append(body, kind);
  return link;
}

function select(index) {
  const links = results.querySelectorAll(".search-result");
  if (!links.length) return;
  active = Math.max(0, Math.min(index, links.length - 1));
  links.forEach((link, i) => link.setAttribute("aria-selected", String(i === active)));
  links[active].scrollIntoView({ block: "nearest" });
  input.setAttribute("aria-activedescendant", links[active].id);
}

function render(query) {
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  ranked = entries
    .map((entry) => [entry, scoreEntry(entry, words)])
    .filter(([, score]) => score >= 0)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 12)
    .map(([entry]) => entry);

  results.replaceChildren();
  input.removeAttribute("aria-activedescendant");
  if (!ranked.length) {
    const empty = document.createElement("p");
    empty.className = "search-empty";
    empty.textContent = "No matching documentation.";
    results.append(empty);
    return;
  }
  results.append(...ranked.map(resultLink));
  select(0);
}

function openSearch() {
  input.value = "";
  render("");
  dialog.showModal();
  input.focus();
}

for (const trigger of triggers) trigger.addEventListener("click", openSearch);
input.addEventListener("input", () => render(input.value));
input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    select(active + (event.key === "ArrowDown" ? 1 : -1));
  } else if (event.key === "Enter" && ranked[active]) {
    event.preventDefault();
    window.location.href = ranked[active].href;
  }
});
dialog.querySelector("[data-close]").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
document.addEventListener("keydown", (event) => {
  const editing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
  if (event.key === "/" && !dialog.open && !editing) {
    event.preventDefault();
    openSearch();
  }
});

// Theme: saved choice, else the system preference (applied early in <head>).
const themeToggle = document.querySelector("#themeToggle");
function labelTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  themeToggle.setAttribute("aria-label", `Switch to ${next} theme`);
  themeToggle.title = `Switch to ${next} theme`;
}
themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem("decay-theme", next);
  } catch {}
  labelTheme();
});
labelTheme();

// Mobile menu.
const menuToggle = document.querySelector("#menuToggle");
const mobileNav = document.querySelector("#mobileNav");
menuToggle.addEventListener("click", () => {
  const open = mobileNav.hidden;
  mobileNav.hidden = !open;
  menuToggle.setAttribute("aria-expanded", String(open));
  menuToggle.querySelector("path").setAttribute(
    "d",
    open ? "M3.5 3.5l9 9M12.5 3.5l-9 9" : "M2.5 4.5h11M2.5 8h11M2.5 11.5h11"
  );
});

// Copy buttons for code samples.
for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const source = document.getElementById(button.dataset.copy);
    const text = [...source.querySelectorAll(".line")].map((l) => l.textContent).join("\n");
    try {
      await navigator.clipboard.writeText(text || source.textContent);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Copy failed";
    }
    setTimeout(() => (button.textContent = "Copy"), 1400);
  });
}

// Highlight the current section in "On this page".
const tocLinks = [...document.querySelectorAll(".toc a[href^='#']")];
if (tocLinks.length && "IntersectionObserver" in window) {
  const byId = new Map(tocLinks.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
  const observer = new IntersectionObserver(
    (seen) => {
      for (const entry of seen) {
        if (!entry.isIntersecting) continue;
        tocLinks.forEach((a) => a.classList.remove("active"));
        byId.get(entry.target.id)?.classList.add("active");
      }
    },
    { rootMargin: "-80px 0px -70% 0px" }
  );
  for (const id of byId.keys()) {
    const heading = document.getElementById(id);
    if (heading) observer.observe(heading);
  }
}

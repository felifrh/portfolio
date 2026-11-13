// filter.js: der Tag-Filter auf dem Index.
//
// Ein Tag auf einmal, dazu "All". Zeilen, die nicht passen, werden abgeblendet statt entfernt,
// damit die Liste nicht springt. Der Zustand steht in der Adresse (?tag=...), ist also verlinkbar.

const buttons = document.querySelectorAll(".filter button");
const rows = document.querySelectorAll(".row");

function apply(tag) {
  for (const button of buttons) {
    button.setAttribute("aria-pressed", String(button.dataset.tag === tag));
  }
  for (const row of rows) {
    const matches = tag === "" || row.dataset.tags.split(" ").includes(tag);
    row.classList.toggle("is-dimmed", !matches);
  }
}

function tagFromAddress() {
  const tag = new URLSearchParams(location.search).get("tag") || "";
  // Unbekannte Werte in der Adresse zählen als "All".
  return [...buttons].some((b) => b.dataset.tag === tag) ? tag : "";
}

for (const button of buttons) {
  button.addEventListener("click", () => {
    const tag = button.dataset.tag;
    const url = new URL(location.href);
    tag ? url.searchParams.set("tag", tag) : url.searchParams.delete("tag");
    history.replaceState(null, "", url);
    apply(tag);
  });
}

apply(tagFromAddress());

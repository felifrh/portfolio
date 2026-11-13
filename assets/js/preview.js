// preview.js: auf dem Index folgt ein Cover-Ausschnitt der Maus.
//
// Nur bei Mausbedienung. Auf dem Handy steht stattdessen ein kleines Cover in jeder Zeile (CSS).
// Das Cover wird aus der Zeile kopiert, es gibt also keine zweite Bildliste zu pflegen.

const mouse = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (mouse) {
  const preview = document.createElement("div");
  preview.className = "preview";
  preview.setAttribute("aria-hidden", "true");
  document.body.append(preview);

  let targetX = 0, targetY = 0, x = 0, y = 0;

  for (const row of document.querySelectorAll(".row")) {
    row.addEventListener("mouseenter", () => {
      preview.replaceChildren(row.querySelector(".cover").cloneNode(true));
      preview.classList.add("is-visible");
    });
    row.addEventListener("mouseleave", () => preview.classList.remove("is-visible"));
  }

  window.addEventListener("mousemove", (event) => {
    targetX = event.clientX + 24;
    targetY = event.clientY - 120;
  });

  // Das Bild zieht weich nach. Bei reduzierter Bewegung sitzt es direkt an der Maus.
  function follow() {
    const ease = calm ? 1 : 0.14;
    x += (targetX - x) * ease;
    y += (targetY - y) * ease;
    preview.style.transform = `translate(${x}px, ${y}px)`;
    requestAnimationFrame(follow);
  }
  follow();
}

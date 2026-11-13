// cursor.js: der eigene Mauszeiger, eine runde Scheibe aus Milchglas.
//
// Nur bei Mausbedienung. In Ruhe ist die Scheibe klein, über Links etwas größer, über Projektbildern
// groß; auf der Startseite steht dann Titel und Jahr daneben. Die Scheibe sitzt ohne Verzögerung
// genau an der Maus, weich verändert sich nur ihre Größe (CSS).
// Ohne dieses Skript bleibt der normale Mauszeiger des Systems.

if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  const cursor = document.createElement("div");
  cursor.className = "cursor";
  cursor.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  label.className = "cursor__label";
  cursor.append(label);
  document.body.append(cursor);

  window.addEventListener("mousemove", (event) => {
    cursor.style.transform = `translate(${event.clientX}px, ${event.clientY}px)`;
    document.documentElement.classList.add("js-cursor");   // erst jetzt den Systemzeiger ausblenden

    const project = event.target.closest("[data-cursor]");  // Projektbild (Startseite, Index)
    const link = event.target.closest("a, button, video");
    cursor.classList.toggle("is-project", Boolean(project));
    cursor.classList.toggle("is-link", Boolean(link) && !project);
    label.textContent = project ? project.dataset.cursor : "";
  });

  // Verlässt die Maus das Fenster, verschwindet die Scheibe
  document.documentElement.addEventListener("mouseleave", () => cursor.classList.add("is-away"));
  document.documentElement.addEventListener("mouseenter", () => cursor.classList.remove("is-away"));
  window.addEventListener("mousedown", () => cursor.classList.add("is-pressed"));
  window.addEventListener("mouseup", () => cursor.classList.remove("is-pressed"));
}

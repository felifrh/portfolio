// cursor.js: der eigene Mauszeiger, eine runde Scheibe aus Milchglas.
//
// Nur bei Mausbedienung. In Ruhe ist die Scheibe klein, über Links etwas größer, über Projektbildern
// groß; auf der Startseite steht dann der Einzeiler des Projekts daneben. Die Scheibe sitzt ohne Verzögerung
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

  // Mausposition merken. Auch wenn die Maus still steht, bewegen sich auf der Startseite die Bilder
  // darunter (Scrollen, Treiben); deshalb wird in jedem Bild neu geprüft, was unter der Maus liegt.
  let at = null;
  function look(element) {
    const project = element && element.closest("[data-cursor]");  // Projektbild (Startseite, Index)
    const link = element && element.closest("a, button, video");
    cursor.classList.toggle("is-project", Boolean(project));
    cursor.classList.toggle("is-link", Boolean(link) && !project);
    const text = project ? project.dataset.cursor : "";
    if (label.textContent !== text) label.textContent = text;
    // Reicht rechts der Platz nicht, steht der Text links von der Scheibe
    cursor.classList.toggle("is-flipped", text !== "" && at.x + label.offsetWidth + 60 > window.innerWidth);
  }

  window.addEventListener("mousemove", (event) => {
    at = { x: event.clientX, y: event.clientY };
    cursor.style.transform = `translate(${at.x}px, ${at.y}px)`;
    document.documentElement.classList.add("js-cursor");   // erst jetzt den Systemzeiger ausblenden
    look(event.target);
  });

  const watch = () => {
    if (at && !cursor.classList.contains("is-away")) look(document.elementFromPoint(at.x, at.y));
    requestAnimationFrame(watch);
  };
  requestAnimationFrame(watch);

  // Verlässt die Maus das Fenster, verschwindet die Scheibe
  document.documentElement.addEventListener("mouseleave", () => cursor.classList.add("is-away"));
  document.documentElement.addEventListener("mouseenter", () => cursor.classList.remove("is-away"));
  window.addEventListener("mousedown", () => cursor.classList.add("is-pressed"));
  window.addEventListener("mouseup", () => cursor.classList.remove("is-pressed"));
}

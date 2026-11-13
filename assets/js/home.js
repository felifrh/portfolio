// home.js: legt die Projektliste der Startseite auf einen großen, stark angeschnittenen Kreis.
//
// Im HTML steht eine ganz normale Liste mit Links. Dieses Skript ordnet dieselben Listenpunkte
// als Bilder auf einem Kreisbogen an: am Desktop nebeneinander, auf dem Handy untereinander.
// Gescrollt wird mit dem normalen Scrollen des Browsers (Mausrad, Wischen, Tastatur). Die Seite
// ist dafür nur höher als das Fenster, die Bühne bleibt stehen, und die Scroll-Position bestimmt,
// welches Projekt vorn liegt. So bleiben Tastatur, Zoom und Screenreader unberührt.
//
// Bei reduzierter Bewegung tut dieses Skript nichts: Dann bleibt die Startseite die schlichte Liste.

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const track = document.querySelector(".home__track");

if (track && !calm) {
  const tiles = [...track.querySelectorAll(".row")];
  const counter = track.querySelector(".counter");
  const label = track.querySelector(".home__label");   // Handy: Titel des vorderen Bildes, bleibt immer sichtbar
  const count = tiles.length;
  const two = (n) => String(n).padStart(2, "0");

  // ---------- Stellschrauben ----------
  const SPACING = 0.7;     // Abstand zweier Bilder auf dem Bogen, als Anteil der Bildgröße (unter 1 = überlappt)
  const RADIUS = 1.6;      // Kreisradius, als Vielfaches der Fensterbreite (Handy: Fensterhöhe mal 0.9)
  const TURN = 0.5;        // wie stark sich die Bilder mit dem Kreis mitdrehen (0 = gar nicht, 1 = ganz)
  const SHRINK = 0.1;      // um wie viel jedes Bild pro Platz Abstand kleiner wird
  const SOFTNESS = 0.07;   // Weichheit des Scrollens: kleiner = weicher und träger
  const SWAY = 0.045;      // Stärke des langsamen Treibens (in Plätzen)

  let vertical, step, radius, tileSize;
  let position = 0;        // aktuell gezeigte Stelle (0 = erstes Projekt vorn), läuft weich hinterher
  let time = 0;            // Uhr für das Treiben; steht still, solange die Maus oder ein Finger auf der Bühne ist
  let paused = false;
  let last = performance.now();

  document.documentElement.classList.add("js-home");

  function measure() {
    vertical = window.innerWidth < 900;
    tileSize = vertical ? tiles[0].offsetHeight : tiles[0].offsetWidth;   // Größe kommt aus dem CSS (--tile)
    radius = vertical ? window.innerHeight * 0.9 : window.innerWidth * RADIUS;
    step = window.innerHeight * 0.6;                          // Scrollweg von einem Projekt zum nächsten
    track.style.height = `${window.innerHeight + (count - 1) * step}px`;
  }

  // Wo in der Liste stehen wir laut Scroll-Position?
  const target = () => Math.min(count - 1, Math.max(0, (window.scrollY - track.offsetTop) / step));

  function frame(now) {
    if (!paused) time += (now - last) / 1000;
    last = now;
    position += (target() - position) * SOFTNESS;

    const angleStep = (tileSize * SPACING) / radius;          // Winkel zwischen zwei Bildern
    const front = Math.round(position);

    tiles.forEach((tile, i) => {
      // Abstand zum vorderen Platz, plus ein kleines, für jedes Bild anderes Treiben
      const distance = i - position + Math.sin(time * 0.35 + i * 1.7) * SWAY;
      const angle = distance * angleStep;
      const along = Math.sin(angle) * radius;                 // Weg entlang des Bogens
      const away = (1 - Math.cos(angle)) * radius;            // Weg vom Scheitel des Kreises weg
      const bob = Math.sin(time * 0.5 + i) * 5;               // leichtes Auf und Ab
      const x = vertical ? -away : along;
      const y = vertical ? along + bob : away + bob;
      const far = Math.abs(distance);
      const scale = Math.max(0.5, 1 - far * SHRINK);
      const turn = (vertical ? -angle : angle) * TURN;

      tile.style.transform = `translate(${x}px, ${y}px) rotate(${turn}rad) scale(${scale})`;
      tile.style.opacity = Math.min(1, Math.max(0, 2.3 - far * 0.8));   // blendet zum Rand hin aus
      tile.style.zIndex = 100 - Math.round(far * 10);                   // das mittlere liegt vorn
      tile.style.visibility = far > 3 ? "hidden" : "visible";
      tile.classList.toggle("is-front", i === front);
    });

    counter.textContent = `${two(front + 1)} / ${two(count)}`;
    if (label.dataset.shown !== String(front)) {
      label.dataset.shown = front;
      label.textContent = tiles[front].querySelector(".row__title").textContent;
    }
    requestAnimationFrame(frame);
  }

  const goTo = (i) => window.scrollTo({ top: track.offsetTop + Math.min(count - 1, Math.max(0, i)) * step });

  // Treiben pausiert, solange die Maus über einem Bild oder ein Finger auf der Bühne ist
  for (const tile of tiles) {
    tile.addEventListener("mouseenter", () => (paused = true));
    tile.addEventListener("mouseleave", () => (paused = false));
    // Tastatur: Wer mit Tab zu einem Projekt springt, bekommt es nach vorn geholt
    tile.querySelector("a").addEventListener("focus", () => goTo(tiles.indexOf(tile)));
    // Klick: Dieses Bild wächst zur Projektseite (CSS: view-transition-name, siehe site.css)
    // Der Name darf nur einmal auf der Seite vorkommen, deshalb erst bei allen anderen entfernen.
    tile.querySelector("a").addEventListener("click", () => {
      tiles.forEach((other) => (other.querySelector(".cover").style.viewTransitionName = ""));
      tile.querySelector(".cover").style.viewTransitionName = "hero";
    });
  }
  track.addEventListener("touchstart", () => (paused = true), { passive: true });
  track.addEventListener("touchend", () => (paused = false));

  // Pfeiltasten links und rechts blättern um ein Projekt
  window.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight") goTo(Math.round(target()) + 1);
    if (event.key === "ArrowLeft") goTo(Math.round(target()) - 1);
  });

  window.addEventListener("resize", measure);
  measure();

  // Wer von einer Projektseite zurückkommt, landet wieder bei diesem Projekt.
  const from = tiles.findIndex((tile) => document.referrer.endsWith(tile.querySelector("a").getAttribute("href").replace(/^\.\//, "")));
  if (from > 0 && window.scrollY === 0) { goTo(from); position = from; }

  requestAnimationFrame(frame);
}

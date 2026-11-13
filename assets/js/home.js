// home.js: legt die Projektliste der Startseite auf einen großen, stark angeschnittenen Kreis.
//
// Im HTML steht eine ganz normale Liste mit Links. Dieses Skript ordnet dieselben Listenpunkte
// als Bilder auf einem Kreisbogen an: am Desktop nebeneinander, auf dem Handy untereinander.
// Der Bogen ist endlos: Nach dem letzten Projekt kommt wieder das erste. Er treibt langsam in die
// Richtung weiter, in die zuletzt gescrollt wurde. Die Seite selbst scrollt dabei nicht; Mausrad,
// Wischen und Pfeiltasten bewegen nur den Bogen. Die Links bleiben mit der Tab-Taste erreichbar.
//
// Bei reduzierter Bewegung tut dieses Skript nichts: Dann bleibt die Startseite die schlichte Liste.

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const stage = document.querySelector(".home__stage");

if (stage && !calm) {
  const tiles = [...stage.querySelectorAll(".row")];
  const covers = tiles.map((tile) => tile.querySelector(".cover"));
  const links = tiles.map((tile) => tile.querySelector("a"));
  const label = stage.querySelector(".home__label");   // Handy: Titel des vorderen Bildes, bleibt immer sichtbar
  const count = tiles.length;

  // ---------- Stellschrauben ----------
  const SPACING = 0.78;    // Abstand zweier Bilder auf dem Bogen, als Anteil der Bildgröße
  const RADIUS = 1.6;      // Kreisradius, als Vielfaches der Fensterbreite (Handy: Fensterhöhe mal 0.9)
  const TURN = 0.5;        // wie stark sich die Bilder mit dem Kreis mitdrehen (0 = gar nicht, 1 = ganz)
  const SMALL = 0.7;       // Größe der Bilder, die nicht vorn sind (Desktop)
  const BLUR = 3;          // Unschärfe der Bilder, die nicht vorn sind, in Pixeln
  const SOFTNESS = 0.11;   // Weichheit des Scrollens: kleiner = weicher und träger
  const DRIFT = 0.045;     // Tempo des Treibens, in Projekten pro Sekunde
  const WHEEL = 1 / 450;   // Mausrad: Projekte pro Pixel Scrollweg

  let vertical, radius, tileSize;
  let target = 0;          // wohin der Bogen will (wächst endlos, 3.0 = viertes Projekt vorn)
  let position = 0;        // wo er gerade ist, läuft weich hinterher
  let direction = 1;       // letzte Scrollrichtung, in die das Treiben weiterläuft
  let speed = 0;           // Schwung nach dem Wischen, klingt zum Treiben hin ab
  let paused = false;      // Maus auf einem Bild oder Finger auf der Bühne
  let leaving = false;     // ein Projekt wurde angeklickt
  let last = performance.now();
  const blurNow = new Array(count).fill(-1);

  document.documentElement.classList.add("js-home");

  function measure() {
    vertical = window.innerWidth < 900;
    tileSize = vertical ? tiles[0].offsetHeight : tiles[0].offsetWidth;   // Größe kommt aus dem CSS (--tile)
    radius = vertical ? window.innerHeight * 0.9 : window.innerWidth * RADIUS;
  }

  // Abstand eines Bildes zum vorderen Platz, über das Ende der Liste hinweg gerechnet (endlos)
  const distanceOf = (i, at) => ((((i - at) % count) + count * 1.5) % count) - count / 2;

  function frame(now) {
    const seconds = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (!paused && !leaving) {
      speed += (direction * DRIFT - speed) * 0.04;          // Schwung klingt ab, das Treiben bleibt
      target += speed * seconds;
    }
    position += (target - position) * SOFTNESS;

    const angleStep = (tileSize * SPACING) / radius;        // Winkel zwischen zwei Bildern
    let front = 0, nearest = Infinity;

    tiles.forEach((tile, i) => {
      const distance = distanceOf(i, position);
      const far = Math.abs(distance);
      if (far < nearest) { nearest = far; front = i; }

      // "focus": 1 = ganz vorn, 0 = ein Platz oder weiter weg. Die Kurve ist am Rand flach, deshalb
      // sind zwei Bilder im Moment des Wechsels gleich klein und berühren sich nicht: Keines springt
      // vor das andere, das neue wächst nach vorn.
      const focus = Math.max(0, 1 - far) ** 2;
      const angle = distance * angleStep;
      const along = Math.sin(angle) * radius;               // Weg entlang des Bogens
      const away = (1 - Math.cos(angle)) * radius;          // Weg vom Scheitel des Kreises weg
      const x = vertical ? -away : along;
      const y = vertical ? along : away;
      const scale = vertical
        ? Math.max(0.5, 1 - far * 0.1)
        : SMALL + (1 - SMALL) * focus - Math.max(0, far - 1) * 0.04;
      const turn = (vertical ? -angle : angle) * TURN;

      tile.style.transform = `translate(${x}px, ${y}px) rotate(${turn}rad) scale(${scale})`;
      tile.style.opacity = Math.min(1, Math.max(0, 2.6 - far));     // blendet zum Rand hin aus
      tile.style.zIndex = 100 - Math.round(far * 20);                // das mittlere liegt vorn
      tile.style.pointerEvents = far < 3 ? "" : "none";

      // Unschärfe nur neu setzen, wenn sie sich merklich ändert (spart Rechenarbeit)
      const blur = Math.round(Math.min(1, far) * BLUR * 2) / 2;
      if (blur !== blurNow[i]) { blurNow[i] = blur; covers[i].style.filter = blur ? `blur(${blur}px)` : ""; }
    });

    tiles.forEach((tile, i) => tile.classList.toggle("is-front", i === front));
    if (label.dataset.shown !== String(front)) {
      label.dataset.shown = front;
      label.textContent = tiles[front].querySelector(".row__title").textContent;
    }
    requestAnimationFrame(frame);
  }

  function nudge(amount) {             // den Bogen um 'amount' Projekte bewegen
    target += amount;
    if (amount) direction = Math.sign(amount);
  }

  // ---------- Eingaben ----------
  window.addEventListener("wheel", (event) => nudge((event.deltaY + event.deltaX) * WHEEL), { passive: true });

  window.addEventListener("keydown", (event) => {
    const steps = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key];
    if (steps) { target = Math.round(target); nudge(steps); speed = 0; }
  });

  let touch = null;
  stage.addEventListener("touchstart", (event) => {
    paused = true; speed = 0;
    touch = { at: vertical ? event.touches[0].clientY : event.touches[0].clientX, time: event.timeStamp };
  }, { passive: true });
  stage.addEventListener("touchmove", (event) => {
    const at = vertical ? event.touches[0].clientY : event.touches[0].clientX;
    const moved = (touch.at - at) / (tileSize * SPACING);
    const seconds = Math.max(0.001, (event.timeStamp - touch.time) / 1000);
    nudge(moved);
    speed = moved / seconds;                                 // Schwung für das Loslassen
    touch = { at, time: event.timeStamp };
  }, { passive: true });
  stage.addEventListener("touchend", () => { paused = false; speed = Math.max(-4, Math.min(4, speed)); });

  tiles.forEach((tile, i) => {
    // Treiben pausiert, solange die Maus über einem Bild ist
    tile.addEventListener("mouseenter", () => (paused = true));
    tile.addEventListener("mouseleave", () => (paused = false));
    // Tastatur: Wer mit Tab zu einem Projekt springt, bekommt es nach vorn geholt
    links[i].addEventListener("focus", () => { target += distanceOf(i, target); speed = 0; });
    // Klick: Das Bild wächst zur Projektseite
    links[i].addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;   // neuer Tab usw.
      event.preventDefault();
      if (!leaving) open(i);
    });
  });

  // ---------- Übergang zur Projektseite ----------
  // Das angeklickte Bild wächst an den Platz, an dem die Projektseite beginnt: oben, volle Breite.
  // Erst danach wird die Seite gewechselt. Dort steht dasselbe Bild an derselben Stelle und gleitet
  // dann an seinen Platz unter dem Titel (assets/js/enter.js).
  function open(i) {
    leaving = true;
    const box = covers[i].getBoundingClientRect();
    const big = covers[i].cloneNode(true);
    big.className = `${covers[i].className} home__grow`;
    big.style.filter = "";
    Object.assign(big.style, { left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${box.height}px` });
    big.querySelector("img").sizes = "150vw";                // jetzt schon das große Bild laden
    document.body.append(big);
    stage.classList.add("is-leaving");
    big.getBoundingClientRect();                             // Startzustand festhalten, dann wachsen
    Object.assign(big.style, { left: "0px", top: "0px", width: "100vw", height: "92svh" });

    try {
      sessionStorage.setItem("enter", links[i].href);        // sagt der Projektseite: mit Übergang beginnen
      sessionStorage.setItem("home-front", i);               // merkt sich, wo wir waren (für "zurück")
    } catch (error) { /* ohne Speicher gibt es nur den ersten Teil des Übergangs */ }
    setTimeout(() => (location.href = links[i].href), 950);
  }

  // "Zurück" im Browser: Startseite wieder in den Ausgangszustand bringen
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    document.querySelector(".home__grow")?.remove();
    stage.classList.remove("is-leaving");
    leaving = false;
  });
  let remembered = 0;
  try { remembered = Number(sessionStorage.getItem("home-front")) || 0; } catch (error) { /* egal */ }
  target = position = remembered;

  window.addEventListener("resize", measure);
  measure();
  requestAnimationFrame(frame);
}

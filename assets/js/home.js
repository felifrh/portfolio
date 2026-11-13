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
  const SPACING = 0.86;    // Abstand zweier Bilder auf dem Bogen, als Anteil der Bildgröße (unter 1 = überlappt)
  const RADIUS = 1.6;      // Kreisradius, als Vielfaches der Fensterbreite (Handy: Fensterhöhe mal 0.9)
  const TURN = 0.5;        // wie stark sich die Bilder mit dem Kreis mitdrehen (0 = gar nicht, 1 = ganz)
  const SMALL = 0.86;      // Größe der Bilder, die nicht vorn sind
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
  const placed = tiles.map(() => ({ scale: 1, turn: 0 }));   // aktuelle Größe und Drehung jedes Bildes

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

      // "focus": 1 = ganz vorn, 0 = ein Platz oder weiter weg, dazwischen ein weicher Bogen
      const focus = (1 + Math.cos(Math.min(1, far) * Math.PI)) / 2;
      const angle = distance * angleStep;
      const along = Math.sin(angle) * radius;               // Weg entlang des Bogens
      const away = (1 - Math.cos(angle)) * radius;          // Weg vom Scheitel des Kreises weg
      const x = vertical ? -away : along;
      const y = vertical ? along : away;
      const scale = SMALL + (1 - SMALL) * focus - Math.max(0, far - 1) * 0.03;
      const turn = (vertical ? -angle : angle) * TURN;
      placed[i] = { scale, turn };

      tile.style.transform = `translate(${x}px, ${y}px) rotate(${turn}rad) scale(${scale})`;
      tile.style.opacity = Math.min(1, Math.max(0, 2.6 - far));     // blendet zum Rand hin aus
      // Feste Reihenfolge wie bei aufgefächerten Karten: Jedes Bild liegt über seinem Vorgänger.
      // Die Reihenfolge zweier sichtbarer Bilder wechselt nie, deshalb springt nichts nach vorn.
      tile.style.zIndex = 500 + Math.round(distance * 10);
      tile.style.pointerEvents = far < 3 ? "" : "none";
      tile.style.setProperty("--glass", (1 - focus).toFixed(3));    // Glasschicht über Bildern, die nicht vorn sind
      tile.style.setProperty("--label", far < 1.6 ? (0.3 + 0.7 * focus).toFixed(3) : 0);   // Schrift ausgegraut
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
  //
  // Damit das flüssig läuft, wird nichts neu angeordnet: Eine Kopie des Bildes liegt von Anfang an
  // in ihrer Endgröße da und wird nur verkleinert gezeigt und beschnitten ('transform', 'clip-path').
  function open(i) {
    leaving = true;
    const wait = (ms) => new Promise((done) => setTimeout(done, ms));
    const ratio = Number(covers[i].dataset.ratio);           // Seitenverhältnis des Bildausschnitts (Fokus)
    const fw = window.innerWidth, fh = stage.offsetHeight * 0.92;      // Ziel: oben, volle Breite, 92 % Höhe
    const ew = Math.max(fw, fh * ratio), eh = ew / ratio;    // Rahmen im Seitenverhältnis des Ausschnitts, der das Ziel überdeckt

    const big = covers[i].cloneNode(true);
    big.className = `${covers[i].className} home__grow`;
    Object.assign(big.style, { left: `${(fw - ew) / 2}px`, top: `${(fh - eh) / 2}px`, width: `${ew}px`, height: `${eh}px` });

    // Start: genau dort und so groß wie das Bild auf dem Bogen
    const box = covers[i].getBoundingClientRect();
    const tw = covers[i].offsetWidth * placed[i].scale, th = covers[i].offsetHeight * placed[i].scale;
    const k = Math.max(tw / ew, th / eh);
    const start = {
      transform: `translate(${box.left + box.width / 2 - fw / 2}px, ${box.top + box.height / 2 - fh / 2}px) rotate(${placed[i].turn}rad) scale(${k})`,
      clipPath: `inset(${(eh - th / k) / 2}px ${(ew - tw / k) / 2}px)`,
    };
    const end = { transform: "none", clipPath: `inset(${(eh - fh) / 2}px ${(ew - fw) / 2}px)` };

    document.body.append(big);
    stage.classList.add("is-leaving");
    const grow = big.animate([start, end], { duration: 1000, easing: "cubic-bezier(0.65, 0, 0.2, 1)", fill: "forwards" });

    // Währenddessen das große Bild laden, das auch die Projektseite zeigt. Erst wenn es da ist
    // (höchstens 1,5 Sekunden warten), wird gewechselt: So bleibt beim Wechsel nichts leer.
    const image = big.querySelector("img");
    const large = new Image();
    large.srcset = image.srcset; large.sizes = "150vw";
    const loaded = large.decode().then(() => (image.sizes = "150vw")).catch(() => {});

    try {
      sessionStorage.setItem("enter", links[i].href);        // sagt der Projektseite: mit Übergang beginnen
      sessionStorage.setItem("home-front", i);               // merkt sich, wo wir waren (für "zurück")
    } catch (error) { /* ohne Speicher gibt es nur den ersten Teil des Übergangs */ }

    Promise.all([grow.finished, Promise.race([loaded, wait(1500)])]).then(() => (location.href = links[i].href));
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

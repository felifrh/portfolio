// pointer.js: eine gemeinsame "Neigung" für alle Effekte, die auf die Maus reagieren.
//
// tilt.x und tilt.y liegen zwischen -1 und 1 (0 = Mitte) und kommen von der Mausposition im Fenster.
// Andere Skripte lesen nur diese zwei Werte und müssen nicht wissen, woher sie kommen.
//
// Auf dem Handy (ohne Maus) bleibt tilt 0, alles steht still. Ein Bewegungssensor wird nicht
// verwendet (Entscheidung 16.11.): Die Seite greift nicht auf Sensoren des Geräts zu.
// Bei reduzierter Bewegung bleibt tilt immer 0.

export const tilt = { x: 0, y: 0 };

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const clamp = (value) => Math.max(-1, Math.min(1, value));

if (!calm) {
  // Maus: Position im Fenster, von der Mitte aus gemessen
  window.addEventListener("mousemove", (event) => {
    tilt.x = clamp((event.clientX / window.innerWidth) * 2 - 1);
    tilt.y = clamp((event.clientY / window.innerHeight) * 2 - 1);
  });
}

// pointer.js: eine gemeinsame "Neigung" für alle Effekte, die auf Maus oder Handy reagieren.
//
// tilt.x und tilt.y liegen zwischen -1 und 1 (0 = Mitte). Am Rechner kommen sie von der Mausposition
// im Fenster, auf dem Handy von der Neigung des Geräts. Andere Skripte lesen nur diese zwei Werte
// und müssen nicht wissen, woher sie kommen.
//
// Handy: iPhones geben die Neigung erst nach einer Erlaubnis frei, und die darf nur nach einer
// Tipp erfragt werden. Deshalb zeigt dieses Skript am iPhone einen kleinen Knopf „Enable tilt“. Wird abgelehnt oder
// fehlt der Sensor, bleibt tilt auf 0: Dann steht alles still, sonst ändert sich nichts.
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

  // Handy: Neigung. Die Haltung beim ersten Messwert gilt als "gerade".
  let rest = null;
  const onTilt = (event) => {
    if (event.gamma === null || event.beta === null) return;
    if (!rest) rest = { gamma: event.gamma, beta: event.beta };
    tilt.x = clamp((event.gamma - rest.gamma) / 25);       // 25 Grad Neigung = voller Ausschlag
    tilt.y = clamp((event.beta - rest.beta) / 25);
  };
  const listen = () => window.addEventListener("deviceorientation", onTilt);

  if (window.matchMedia("(pointer: coarse)").matches && "DeviceOrientationEvent" in window) {
    if (typeof DeviceOrientationEvent.requestPermission === "function") {
      // iPhone: verlangt eine Erlaubnis per Tipp. Wegen des geringen Mehrwerts wird darauf verzichtet
      // (Entscheidung 14.11.): Dort bleibt tilt auf 0, alles steht still.
    } else {
      listen();                                             // Android fragt nicht
    }
  }
}

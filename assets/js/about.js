// about.js: die zwei Bewegungen der About-Seite.
//
// 1. Foto: Feli ist vom Nebel freigestellt und liegt als eigene Ebene über dem Hintergrund.
//    Beide verschieben sich leicht gegeneinander, mit der Maus (pointer.js).
// 2. E-Mail-Adresse: Die Buchstaben weichen der Bewegung der Maus ein wenig aus und kommen zur Ruhe,
//    sobald die Maus stillsteht. Auf dem Handy reagieren sie auf die Neigung.
//
// Außerdem setzt dieses Skript die Adresse erst im Browser zusammen (Schutz vor Spam-Sammlern)
// und macht sie zum Link, der das Mail-Programm öffnet. Bei reduzierter Bewegung steht alles still.

import { tilt } from "./pointer.js";

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ---------- E-Mail-Adresse zusammensetzen ----------
const mail = document.querySelector(".mail");
const address = `${mail.dataset.user}@${mail.dataset.domain}`;
mail.href = `mailto:${address}`;
mail.setAttribute("aria-label", `Write an email to ${address}`);
// Jeder Buchstabe bekommt ein eigenes Element, damit er sich einzeln bewegen kann.
// Der Text bleibt echter Text: markierbar und kopierbar.
mail.replaceChildren(...[...address].map((letter) => {
  const span = document.createElement("span");
  span.textContent = letter;
  span.setAttribute("aria-hidden", "true");
  return span;
}));
const letters = [...mail.children].map((element) => ({ element, x: 0, y: 0 }));

if (!calm) {
  const photo = document.querySelector(".portrait");
  let lookX = 0, lookY = 0;                          // geglättete Neigung für das Foto
  let mouse = { x: -9999, y: -9999 }, before = { x: 0, y: 0, tiltX: 0, tiltY: 0 };
  let pushX = 0, pushY = 0;                          // aktuelle Bewegung der Maus (oder des Handys)

  window.addEventListener("mousemove", (event) => (mouse = { x: event.clientX, y: event.clientY }));

  function frame() {
    // Foto: Hintergrund und Person verschieben sich gegenläufig (CSS liest --look-x und --look-y)
    lookX += (tilt.x - lookX) * 0.06;
    lookY += (tilt.y - lookY) * 0.06;
    photo.style.setProperty("--look-x", lookX.toFixed(4));
    photo.style.setProperty("--look-y", lookY.toFixed(4));

    // Buchstaben: Wie schnell bewegt sich die Maus gerade? Steht sie still, wird das zu null.
    const moved = mouse.x > -9999
      ? { x: mouse.x - before.x, y: mouse.y - before.y }
      : { x: (tilt.x - before.tiltX) * 600, y: (tilt.y - before.tiltY) * 600 };   // Handy: Änderung der Neigung
    before = { x: mouse.x, y: mouse.y, tiltX: tilt.x, tiltY: tilt.y };
    pushX += (moved.x - pushX) * 0.2;
    pushY += (moved.y - pushY) * 0.2;

    for (const letter of letters) {
      const box = letter.element.getBoundingClientRect();
      const distance = mouse.x > -9999
        ? Math.hypot(box.left + box.width / 2 - letter.x - mouse.x, box.top + box.height / 2 - letter.y - mouse.y)
        : 0;
      const near = Math.exp(-distance / 260);          // nur Buchstaben in der Nähe der Maus reagieren
      const wantX = Math.max(-16, Math.min(16, pushX * near * 0.9));
      const wantY = Math.max(-16, Math.min(16, pushY * near * 0.9));
      letter.x += (wantX - letter.x) * 0.12;
      letter.y += (wantY - letter.y) * 0.12;
      letter.element.style.transform = `translate(${letter.x.toFixed(2)}px, ${letter.y.toFixed(2)}px)`;
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* Nav-Farbe: hell, sobald der schwarze Contact-Block unter der Navigation liegt. */
{
  const nav = document.querySelector(".nav");
  const contact = document.getElementById("contact");
  if (nav && contact && "IntersectionObserver" in window) {
    const h = nav.offsetHeight || 56;
    new IntersectionObserver(([e]) => nav.classList.toggle("nav--on-dark", e.isIntersecting), {
      rootMargin: `0px 0px -${innerHeight - h}px 0px`,
    }).observe(contact);
  }
}

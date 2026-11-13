// nav.js: die Navigation verschwindet beim Herunterscrollen und kommt beim Hochscrollen zurück.
//
// So liegt sie beim Lesen nicht über dem Inhalt, ist aber mit einer kleinen Bewegung
// nach oben sofort wieder da. Ganz oben auf der Seite ist sie immer sichtbar.
// Mit der Tastatur bleibt sie erreichbar: Sobald ein Link darin den Fokus hat, zeigt CSS sie wieder.

const nav = document.querySelector(".nav");
let last = window.scrollY;

window.addEventListener("scroll", () => {
  const now = window.scrollY;
  if (Math.abs(now - last) < 8) return;            // kleines Zittern ignorieren
  nav.classList.toggle("nav--hidden", now > last && now > 80);
  last = now;
}, { passive: true });

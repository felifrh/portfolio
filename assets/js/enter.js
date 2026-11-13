// enter.js: der zweite Teil des Übergangs von der Startseite zur Projektseite.
//
// Auf der Startseite ist das angeklickte Bild an den oberen Rand gewachsen (home.js). Diese Seite
// beginnt deshalb mit dem großen Bild an genau dieser Stelle und lässt es dann ruhig an seinen
// Platz unter Titel und Eckdaten gleiten, die dabei einblenden. So sieht man den Anfang der Seite.
//
// Das Skript steht im <head> und läuft, bevor die Seite gezeichnet wird, damit nichts aufblitzt.
// Wer die Seite direkt öffnet oder vom Index kommt, sieht keinen Übergang.

(function () {
  var root = document.documentElement;
  try {
    if (sessionStorage.getItem("enter") !== location.href.split("#")[0]) return;
    sessionStorage.removeItem("enter");
  } catch (error) { return; }                 // z. B. wenn der Browser den Speicher sperrt

  root.classList.add("enter");                // CSS: großes Bild oben festhalten, Einleitung verbergen

  document.addEventListener("DOMContentLoaded", function () {
    var hero = document.querySelector(".hero");
    var intro = document.querySelector(".intro");
    root.classList.remove("enter");           // Bild steht wieder an seinem eigentlichen Platz ...
    var way = hero.getBoundingClientRect().top;
    // ... und wird von oben dorthin bewegt (nur 'transform', das läuft flüssig)
    hero.animate(
      [{ transform: "translateY(" + -way + "px)" }, { transform: "none" }],
      { duration: 1100, delay: 250, easing: "cubic-bezier(0.65, 0, 0.2, 1)", fill: "backwards" }
    );
    intro.animate(
      [{ opacity: 0, transform: "translateY(2rem)" }, { opacity: 1, transform: "none" }],
      { duration: 800, delay: 700, easing: "ease-out", fill: "backwards" }
    );
  });
})();

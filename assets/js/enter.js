// enter.js: sorgt dafür, dass eine Projektseite richtig beginnt.
//
// 1. Jede neu geöffnete Projektseite beginnt ganz oben (auch beim Wechsel über "Next" am Seitenende).
// 2. Zweiter Teil des Übergangs von der Startseite: Dort ist das angeklickte Bild an den oberen Rand
//    gewachsen (home.js). Diese Seite beginnt deshalb mit dem großen Bild an genau dieser Stelle und
//    lässt es dann ruhig an seinen Platz unter Titel und Eckdaten gleiten, die dabei einblenden.
//
// Das Skript steht im <head> und läuft, bevor die Seite gezeichnet wird, damit nichts aufblitzt.

(function () {
  var root = document.documentElement;

  // 1. Oben beginnen. Nur beim Zurück- und Vorwärtsgehen im Browser bleibt die alte Stelle erhalten.
  var navigation = performance.getEntriesByType("navigation")[0];
  if (!navigation || navigation.type !== "back_forward") {
    var toTop = function () { if (!location.hash) window.scrollTo(0, 0); };
    document.addEventListener("DOMContentLoaded", toTop);
    window.addEventListener("pageshow", toTop);
  }

  // 2. Kommen wir gerade von der Startseite? (home.js hat sich diese Adresse gemerkt)
  try {
    if (sessionStorage.getItem("enter") !== location.href.split("#")[0]) return;
    sessionStorage.removeItem("enter");
  } catch (error) { return; }                 // z. B. wenn der Browser den Speicher sperrt

  root.classList.add("enter");                // CSS: großes Bild oben festhalten, Einleitung verbergen

  document.addEventListener("DOMContentLoaded", function () {
    var hero = document.querySelector(".hero");
    var intro = document.querySelector(".intro");
    var image = hero.querySelector("img");
    var wait = new Promise(function (done) { setTimeout(done, 1200); });

    // Erst loslegen, wenn das Bild wirklich da ist (höchstens 1,2 Sekunden warten)
    Promise.race([image.decode().catch(function () {}), wait]).then(function () {
      root.classList.remove("enter");         // Bild steht wieder an seinem eigentlichen Platz ...
      var way = hero.getBoundingClientRect().top;
      // ... und wird von oben dorthin bewegt (nur 'transform', das läuft flüssig)
      hero.animate(
        [{ transform: "translateY(" + -way + "px)" }, { transform: "none" }],
        { duration: 1100, delay: 200, easing: "cubic-bezier(0.65, 0, 0.2, 1)", fill: "backwards" }
      );
      intro.animate(
        [{ opacity: 0, transform: "translateY(2rem)" }, { opacity: 1, transform: "none" }],
        { duration: 800, delay: 650, easing: "ease-out", fill: "backwards" }
      );
    });
  });
})();

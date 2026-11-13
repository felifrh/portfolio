// layers.js: lässt die Ebenen der Projektseite übereinanderschieben.
//
// Jede Ebene bleibt beim Scrollen stehen (position: sticky), die nächste schiebt sich darüber.
// Ist eine Ebene höher als das Fenster, bleibt sie erst stehen, wenn ihr Ende erreicht ist.
// So ist der Text immer bis zum Schluss lesbar. Dafür braucht CSS die Höhe jeder Ebene,
// und die kann nur JavaScript messen.

const layers = document.querySelectorAll(".layer");

function measure() {
  for (const layer of layers) {
    // Der durchsichtige Übergang (--edge) liegt im Stand oberhalb des Fensters,
    // sonst würde die Ebene darunter durchscheinen. Die Einleitung hat keinen Übergang.
    const edge = layer.classList.contains("layer--intro") ? 0 : parseFloat(getComputedStyle(layer).paddingTop);
    const stick = Math.min(-edge, window.innerHeight - layer.offsetHeight);
    layer.style.setProperty("--stick", `${stick}px`);
  }
}

// Neu messen, wenn sich Fenster oder Inhalt ändern (z. B. wenn Bilder fertig geladen sind).
const observer = new ResizeObserver(measure);
layers.forEach((layer) => observer.observe(layer));
window.addEventListener("resize", measure);

measure();
document.documentElement.classList.add("js-layers");

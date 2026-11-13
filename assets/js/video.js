// video.js: steuert die Videos auf den Projektseiten.
//
// "loop": läuft stumm in Schleife, sobald es im Bild ist, und hält an, wenn es das Bild verlässt.
//         Statt der Browser-Bedienelemente gibt es eine kleine Schaltfläche zum Anhalten.
// "controls": startet nie von selbst und behält die Bedienelemente; hält an, wenn es das Bild verlässt.
// Geladen wird ein Video erst, wenn es gebraucht wird (preload="none" im HTML).
// Bei reduzierter Bewegung startet nichts von selbst, alle Videos behalten ihre Bedienelemente.

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const videos = document.querySelectorAll("video");

for (const video of videos) {
  if (video.dataset.mode !== "loop" || calm) continue;

  video.removeAttribute("controls");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "video-toggle";
  button.textContent = "Pause";
  video.after(button);

  // Merkt sich, ob die Besucherin selbst angehalten hat. Dann startet das Video nicht wieder von allein.
  button.addEventListener("click", () => {
    video.dataset.stopped = video.paused ? "" : "yes";
    video.paused ? video.play() : video.pause();
  });
  video.addEventListener("play", () => (button.textContent = "Pause"));
  video.addEventListener("pause", () => (button.textContent = "Play"));
}

const observer = new IntersectionObserver((entries) => {
  for (const { target: video, isIntersecting } of entries) {
    const autoplay = video.dataset.mode === "loop" && !calm && !video.dataset.stopped;
    if (isIntersecting && autoplay) video.play().catch(() => {});   // Browser darf das Abspielen ablehnen
    if (!isIntersecting) video.pause();
  }
}, { threshold: 0.25 });

videos.forEach((video) => observer.observe(video));

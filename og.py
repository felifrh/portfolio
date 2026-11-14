#!/usr/bin/env python3
"""
og.py: erzeugt die Vorschaubilder zum Teilen (1200 x 630) und das Favicon.

Aufruf:   python3 og.py
Eingabe:  content/projects/*.json (Cover und Fokusbereich), assets/media/ (die größten WebP-Dateien)
Ausgabe:  assets/og/<slug>.jpg, assets/og/default.jpg, favicon.svg, favicon-32.png, apple-touch-icon.png
Braucht Pillow. Läuft nur, wenn sich ein Cover oder das Favicon ändert.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
MEDIA = json.loads((ROOT / "assets/media/manifest.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets/og"
OUT.mkdir(parents=True, exist_ok=True)
RATIO = 1200 / 630


def og_image(project):
    cover = project["cover"]
    info = MEDIA[f"{project['slug']}/{cover['file']}"]
    width = max(info["widths"])
    path = ROOT / f"assets/media/{project['slug']}/{info['name']}-{width}.webp"
    img = Image.open(path).convert("RGB")
    s = img.width / info["w"]                       # Fokus liegt in Pixeln des Originals
    x0, y0, x1, y1 = (v * s for v in cover["focus"])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = x1 - x0, y1 - y0
    if w / h < RATIO: w = h * RATIO                 # auf 1200:630 erweitern, nie verkleinern
    else:             h = w / RATIO
    if w > img.width:  w, h = img.width, img.width / RATIO
    if h > img.height: w, h = img.height * RATIO, img.height
    left = min(max(cx - w / 2, 0), img.width - w)
    top = min(max(cy - h / 2, 0), img.height - h)
    crop = img.crop((round(left), round(top), round(left + w), round(top + h))).resize((1200, 630), Image.LANCZOS)
    crop.save(OUT / f"{project['slug']}.jpg", quality=82, optimize=True)


def favicon():
    """Milchglas-Scheibe wie der Mauszeiger: Flieder auf Schwarz."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="14" fill="#0e0e10"/>'
           '<defs><radialGradient id="g" cx="35%" cy="30%" r="80%">'
           '<stop offset="0" stop-color="#d9deff"/><stop offset="1" stop-color="#a9b2ff"/></radialGradient></defs>'
           '<circle cx="32" cy="32" r="17" fill="url(#g)"/></svg>')
    (ROOT / "favicon.svg").write_text(svg, encoding="utf-8")
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
        S = size * 4
        im = Image.new("RGB", (S, S), "#0e0e10")
        r = S * 17 / 64
        disc = Image.new("RGB", (S, S), "#a9b2ff")
        hi = Image.new("L", (S, S), 0)
        ImageDraw.Draw(hi).ellipse([S * .22, S * .17, S * .62, S * .57], fill=110)
        disc.paste(Image.new("RGB", (S, S), "#d9deff"), mask=hi.filter(ImageFilter.GaussianBlur(S * .08)))
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=255)
        im.paste(disc, mask=mask)
        im.resize((size, size), Image.LANCZOS).save(ROOT / name)


if __name__ == "__main__":
    projects = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "content/projects").glob("*.json")]
    for p in projects:
        og_image(p)
    (OUT / "default.jpg").write_bytes((OUT / "equal-matter.jpg").read_bytes())
    favicon()
    print(len(projects), "Vorschaubilder, Favicon geschrieben")

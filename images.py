#!/usr/bin/env python3
"""
images.py: bringt die Bilder aus dem Vault in Webgröße ins Repository.

Aufruf:   python3 images.py "/Pfad/zum/Vault/00_Allgemein/Attachements"
Eingabe:  die Bildnamen, die in content/projects/*.json stehen (cover.file, media[].file)
Ausgabe:  assets/media/<slug>/<name>-<breite>.webp  und  assets/media/manifest.json

Warum so: Nur Bilder, die in einer Datendatei genannt sind, landen im öffentlichen
Repository. Die Originale (bis 15 MB) bleiben im Vault. Beim Neuspeichern fallen alle
Metadaten weg (EXIF, GPS, Kameradaten). Braucht Pillow:  pip3 install pillow
"""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
OUT = ROOT / "assets" / "media"
WIDTHS = [640, 1200, 2000]      # Breiten für srcset
MAX_EDGE = 2400                 # längste Kante, PRD Abschnitt 9
Image.MAX_IMAGE_PIXELS = None   # die Originale sind groß, das ist gewollt


def clean_name(filename):
    """'ddw26_36_FFerch.jpg' -> 'ddw26-36-fferch' (sprechende, sichere Dateinamen)."""
    return re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")


def wanted_files(project):
    """Alle Bilddateien, die ein Projekt nennt (Cover und Abschnitte)."""
    files = [project["cover"]["file"]]
    for section in project["sections"]:
        files += [m["file"] for m in section.get("media", []) if m.get("type") != "video"]
    return files


def main(source_dir):
    source_dir = Path(source_dir)
    manifest = {}
    for path in sorted((ROOT / "content" / "projects").glob("*.json")):
        project = json.loads(path.read_text(encoding="utf-8"))
        slug = project["slug"]
        (OUT / slug).mkdir(parents=True, exist_ok=True)
        for filename in wanted_files(project):
            found = list(source_dir.rglob(filename))
            if not found:
                print(f"FEHLT  {slug}: {filename}")
                continue
            image = ImageOps.exif_transpose(Image.open(found[0])).convert("RGB")
            w, h = image.size
            # Breiten so begrenzen, dass keine Kante über MAX_EDGE geht und nichts vergrößert wird
            # Ausnahme Cover: Es füllt das ganze Fenster und wird dabei vergrößert,
            # deshalb zählt bei ihm nur die Breite, auch im Hochformat.
            is_cover = filename == project["cover"]["file"]
            limit = w if is_cover else min(w, int(MAX_EDGE * min(1, w / h)))
            widths = sorted({min(x, limit) for x in WIDTHS})
            name = clean_name(filename)
            for width in widths:
                target = OUT / slug / f"{name}-{width}.webp"
                if not target.exists():
                    resized = image.resize((width, round(h * width / w)), Image.LANCZOS)
                    resized.save(target, "WEBP", quality=80, method=6)  # ohne exif= : keine Metadaten
            manifest[f"{slug}/{filename}"] = {"name": name, "w": w, "h": h, "widths": widths}
            print(f"ok     {slug}: {filename} -> {widths}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

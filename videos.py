#!/usr/bin/env python3
"""
videos.py: bringt die Videos aus dem Vault in Webgröße ins Repository.

Aufruf:   python3 videos.py "/Pfad/zum/Vault/00_Allgemein/Attachements"
Eingabe:  Medien mit "type": "video" in content/projects/*.json (auch animierte GIFs)
Ausgabe:  assets/media/<slug>/<name>.mp4, <name>-poster.webp, Einträge in assets/media/manifest.json

Warum so: Die Videos laufen direkt auf der Seite, ohne fremden Player (PRD 9.1). H.264 in MP4
spielt jeder Browser. "mode": "loop" läuft stumm in Schleife, der Ton wird deshalb entfernt.
"mode": "controls" behält den Ton und bekommt die Bedienelemente des Browsers.
Braucht ffmpeg (macOS: brew install ffmpeg) und Pillow.
"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
OUT = ROOT / "assets" / "media"
MAX_EDGE = 1280     # längste Kante in Pixeln
QUALITY = "27"      # ffmpeg -crf: kleiner = besser und größer


def clean_name(filename):
    return re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")


def main(source_dir):
    source_dir = Path(source_dir)
    manifest_file = OUT / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}
    for path in sorted((ROOT / "content" / "projects").glob("*.json")):
        project = json.loads(path.read_text(encoding="utf-8"))
        slug = project["slug"]
        videos = [m for s in project["sections"] for m in s.get("media", []) if m.get("type") == "video"]
        for item in videos:
            found = list(source_dir.rglob(item["file"]))
            if not found:
                print(f"FEHLT  {slug}: {item['file']}")
                continue
            (OUT / slug).mkdir(parents=True, exist_ok=True)
            name = clean_name(item["file"])
            target, poster = OUT / slug / f"{name}.mp4", OUT / slug / f"{name}-poster.webp"
            if not target.exists():
                # Verkleinern (nie vergrößern), gerade Pixelmaße, Metadaten entfernen, schneller Start im Browser
                scale = (f"scale='if(gt(iw,ih),min({MAX_EDGE},iw),-2)':'if(gt(iw,ih),-2,min({MAX_EDGE},ih))',"
                         "scale=trunc(iw/2)*2:trunc(ih/2)*2")
                audio = ["-an"] if item["mode"] == "loop" else ["-c:a", "aac", "-b:a", "96k"]
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(found[0]), "-vf", scale,
                                "-c:v", "libx264", "-crf", QUALITY, "-preset", "slow", "-pix_fmt", "yuv420p",
                                "-map_metadata", "-1", "-movflags", "+faststart", *audio, str(target)], check=True)
            # Poster: ein Standbild, das gezeigt wird, bevor das Video lädt
            frame = OUT / slug / f"{name}-poster.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(target),
                            "-frames:v", "1", str(frame)], check=True)
            image = Image.open(frame).convert("RGB")
            image.save(poster, "WEBP", quality=78, method=6)
            frame.unlink()
            manifest[f"{slug}/{item['file']}"] = {"name": name, "w": image.width, "h": image.height, "video": True}
            print(f"ok     {slug}: {item['file']} -> {target.stat().st_size / 1e6:.1f} MB")
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

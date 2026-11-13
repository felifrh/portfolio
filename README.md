# feliferch.com

Portfolio-Website von Felicitas Ferch. Reines HTML, CSS und JavaScript, kein Framework.
Die Seiten werden von einem kleinen Python-Skript aus Datendateien erzeugt und von GitHub Pages
so ausgeliefert, wie sie hier liegen.

## Was liegt wo

| Datei oder Ordner | Zweck |
|---|---|
| `content/site.json` | Name der Seite und die zentrale Tag-Liste. Ein neuer Tag wird nur hier ergänzt. |
| `content/projects/<slug>.json` | Ein Projekt: Titel, Jahr, Tags, Eckdaten, Cover mit Fokusbereich, Abschnitte, Ausstellungen. |
| `build.py` | Erzeugt aus den Datendateien alle HTML-Seiten und `assets/css/covers.css`. |
| `images.py` | Holt die genannten Bilder aus dem Vault, verkleinert sie, entfernt Metadaten. |
| `assets/css/site.css` | Die ganze Gestaltung. Farben, Schriften, Abstände stehen oben als Variablen. |
| `assets/css/covers.css` | Erzeugt. Bildausschnitte der Cover. Nicht von Hand ändern. |
| `assets/js/layers.js` | Projektseite: Ebenen schieben sich übereinander. |
| `assets/js/filter.js` | Index: Tag-Filter, Zustand in der Adresse. |
| `assets/js/preview.js` | Index: Cover folgt der Maus. |
| `assets/media/` | Erzeugt. Bilder in Webgröße und `manifest.json` (Maße der Bilder). |
| `index.html`, `index/`, `work/`, `about/`, `imprint/`, `privacy/` | Erzeugt. Die fertigen Seiten. |

## Ein Projekt hinzufügen oder ändern

1. `content/projects/<slug>.json` anlegen (am einfachsten eine vorhandene Datei kopieren).
2. Bilder holen: `python3 images.py "/Pfad/zum/Vault/00_Allgemein/Attachements"`
   (einmalig vorher: `pip3 install pillow`)
3. Seiten erzeugen: `python3 build.py`
4. Ansehen: `python3 -m http.server` und im Browser `http://localhost:8000` öffnen.
5. Alt-Texte lesen, dann alles committen (Datendatei, Bilder, erzeugte Seiten).

Texte ändern: nur Schritt 3 bis 5.

## Felder einer Projektdatei

- `sortKey` (jüngstes Jahr) und `order` bestimmen die Reihenfolge im Index, `homeOrder` die auf Home.
- `tags`: höchstens zwei, mit den `id`s aus `content/site.json`.
- `cover.focus`: Bildausschnitt als `[x0, y0, x1, y1]` in Pixeln des Originalbildes.
- `sections`: 2 bis 4 Abschnitte, je `label`, `text` (Liste von Absätzen) und `media` (Bilder mit `alt`).
- `consent`: Hinweis zum Einverständnis gezeigter Personen. Erscheint nicht auf der Seite.

## Nicht ins Repository

Originalbilder, Notizen aus dem Vault, alles Private. Das Repository ist öffentlich.

## Schriften

Instrument Sans (SIL Open Font License, siehe `assets/fonts/InstrumentSans-OFL.txt`).
DM Mono (SIL Open Font License) als Platzhalter, bis die Webfont-Lizenz von Aether Mono geklärt ist.

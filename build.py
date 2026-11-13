#!/usr/bin/env python3
"""
build.py: erzeugt alle HTML-Seiten aus den Datendateien.

Aufruf:   python3 build.py
Eingabe:  content/site.json, content/projects/*.json, assets/media/manifest.json
          (das Manifest schreiben images.py und videos.py: Maße aller Bilder und Videos)
Ausgabe:  index.html (Home), index/index.html (Index), work/<slug>/index.html (Projekte),
          assets/css/covers.css (Bildausschnitte der Cover)

Warum so: Navigation, Fußzeile und Seitenkopf stehen nur hier, einmal. Ein neues Projekt
ist eine neue Datei in content/projects/. Das Skript braucht nur Python, keine Pakete.
Die erzeugten Dateien werden mit committet, GitHub Pages liefert sie ohne Bauschritt aus.
"""
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
SITE = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
MEDIA = json.loads((ROOT / "assets/media/manifest.json").read_text(encoding="utf-8"))
TAGS = {tag["id"]: tag["label"] for tag in SITE["tags"]}


# ---------- Daten laden ----------

def load_projects():
    """Alle Projekte, sortiert wie im Index: jüngstes Jahr zuerst, bei Gleichstand 'order' (E4)."""
    projects = [json.loads(p.read_text(encoding="utf-8"))
                for p in (ROOT / "content/projects").glob("*.json")]
    for project in projects:
        unknown = [t for t in project["tags"] if t not in TAGS]
        assert not unknown, f"{project['slug']}: unbekannter Tag {unknown} (siehe content/site.json)"
        assert len(project["tags"]) <= 2, f"{project['slug']}: höchstens zwei Tags"
    return sorted(projects, key=lambda p: (-p["sortKey"], p.get("order", 0)))


# ---------- Bausteine ----------

def picture(slug, item, sizes, lazy=True):
    """<img> mit mehreren Breiten. Breite und Höhe stehen dabei, damit beim Laden nichts springt."""
    info = MEDIA[f"{slug}/{item['file']}"]
    base = f"{{root}}assets/media/{slug}/{info['name']}"
    srcset = ", ".join(f"{base}-{w}.webp {w}w" for w in info["widths"])
    loading = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high" decoding="sync"'
    return (f'<img src="{base}-{info["widths"][-1]}.webp" srcset="{srcset}" sizes="{sizes}" '
            f'width="{info["w"]}" height="{info["h"]}" alt="{e(item["alt"])}"{loading}>')


def video(slug, item):
    """<video>, das direkt auf der Seite läuft. Im HTML stehen immer die Bedienelemente des Browsers,
    damit es auch ohne JavaScript bedienbar ist. video.js macht aus "loop" eine stumme Schleife."""
    info = MEDIA[f"{slug}/{item['file']}"]
    base = f"{{root}}assets/media/{slug}/{info['name']}"
    loop = " muted loop" if item["mode"] == "loop" else ""
    return (f'<video data-mode="{item["mode"]}" controls playsinline preload="none"{loop} '
            f'poster="{base}-poster.webp" width="{info["w"]}" height="{info["h"]}" '
            f'aria-label="{e(item["alt"])}"><source src="{base}.mp4" type="video/mp4"></video>')


def figure(slug, item):
    """Ein Bild oder Video eines Abschnitts. Kleine Bilder (unter 1000 px) stehen zu zweit nebeneinander,
    statt unscharf auf volle Breite gezogen zu werden."""
    if item.get("type") == "video":
        return f'<figure>{video(slug, item)}</figure>'
    small = ' class="small"' if MEDIA[f"{slug}/{item['file']}"]["w"] < 1000 else ""
    return f'<figure{small}>{picture(slug, item, "(min-width: 900px) 55vw, 100vw")}</figure>'


def cover(project, sizes, lazy=True, extra=""):
    """Cover als Ausschnitt: das volle Bild liegt in einem Rahmen, covers.css schiebt es zurecht.
    'data-ratio' ist das Seitenverhältnis des Fokusbereichs (home.js braucht es für den Klick-Übergang)."""
    x0, y0, x1, y1 = project["cover"]["focus"]
    return (f'<span class="cover cover--{project["slug"]} {extra}" data-ratio="{(x1 - x0) / (y1 - y0):.4f}">'
            f'{picture(project["slug"], project["cover"], sizes, lazy)}</span>')


def tag_labels(project):
    return " · ".join(TAGS[t] for t in project["tags"])


def page(root, title, description, body, body_class="", scripts=(), early_script=""):
    """Das Gerüst jeder Seite. 'root' ist der Weg zurück zur obersten Ebene, z. B. '../../'."""
    script_tags = "\n".join(f'  <script type="module" src="{root}assets/js/{s}"></script>'
                            for s in ("nav.js", *scripts))
    # Ein "frühes" Skript läuft, bevor die Seite gezeichnet wird (nur enter.js auf den Projektseiten).
    early = f'  <script src="{root}assets/js/{early_script}"></script>\n' if early_script else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="preload" href="{root}assets/fonts/InstrumentSans-Variable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{root}assets/css/site.css">
  <link rel="stylesheet" href="{root}assets/css/covers.css">
{early}{script_tags}
</head>
<body class="{body_class}">
  <a class="skip" href="#main">Skip to content</a>
  <header class="nav">
    <a class="nav__name" href="{root}">{e(SITE["name"])}</a>
    <nav aria-label="Main">
      <a href="{root}index/">Index</a>
      <a href="{root}about/">About</a>
      <a href="{root}about/#contact">Contact</a>
    </nav>
  </header>
{body}
</body>
</html>
"""
    return html.replace("{root}", root)


FOOTER = """<footer class="footer">
      <span>© Felicitas Ferch</span>
      <a href="{root}imprint/">Imprint</a>
      <a href="{root}privacy/">Privacy</a>
    </footer>"""


def write(path, html):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    print("geschrieben:", path)


# ---------- Seiten ----------

def project_page(project, previous, following):
    slug = project["slug"]
    facts = "\n".join(f"        <div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in project["facts"].items())

    layers = []
    for number, section in enumerate(project["sections"], start=1):
        text = "\n".join(f"          <p>{e(p)}</p>" for p in section["text"])
        media = "\n".join(f"          {figure(slug, m)}" for m in section.get("media", []))
        layers.append(f"""    <section class="layer" aria-labelledby="s{number}">
      <h2 class="layer__label" id="s{number}">{number:02d} / {e(section["label"])}</h2>
      <div class="layer__grid">
        <div class="layer__text">
{text}
        </div>
        <div class="layer__media">
{media}
        </div>
      </div>
    </section>""")

    last = len(project["sections"]) + 1
    exhibitions = "".join(f"<li>{e(x)}</li>" for x in project.get("exhibitions", []))
    links = "".join(f'<li><a href="{e(l["url"])}" rel="noopener">{e(l["label"])}</a></li>' for l in project.get("links", []))
    pager = ""
    if previous:
        pager += f'<a class="pager__link" href="{{root}}work/{previous["slug"]}/"><span>Previous</span>{e(previous["title"])}</a>'
    if following:
        pager += f'<a class="pager__link pager__link--next" href="{{root}}work/{following["slug"]}/"><span>Next</span>{e(following["title"])}</a>'

    body = f"""  <main id="main" class="layers">
    <header class="layer layer--intro">
      <div class="intro">
        <p class="intro__tags">{e(tag_labels(project))}</p>
        <h1 class="intro__title">{e(project["title"])}</h1>
        <p class="intro__line">{e(project["oneLiner"])}</p>
        <dl class="facts">
{facts}
        </dl>
      </div>
      {cover(project, "150vw", lazy=False, extra="hero")}
    </header>
{chr(10).join(layers)}
    <section class="layer layer--end" aria-labelledby="s{last}">
      <h2 class="layer__label" id="s{last}">{last:02d} / Exhibitions &amp; links</h2>
      <div class="end">
        {f'<div><h3>Exhibitions &amp; presentations</h3><ul>{exhibitions}</ul></div>' if exhibitions else ''}
        {f'<div><h3>Links</h3><ul>{links}</ul></div>' if links else ''}
      </div>
      <nav class="pager" aria-label="Projects">{pager}<a class="pager__link pager__link--all" href="{{root}}index/"><span>All projects</span>Index</a></nav>
    {FOOTER}
    </section>
  </main>"""
    title = f'{project["title"]} – {SITE["name"]}'
    return page("../../", title, project["oneLiner"], body, "page-project", scripts=["layers.js", "video.js"],
                early_script="enter.js")


def project_rows(projects, sizes="(min-width: 900px) 22rem, 5rem"):
    """Die Projektliste. Sie steht als normale Liste im HTML und ist ohne JavaScript benutzbar.
    'sizes' sagt dem Browser, wie breit das Cover gezeigt wird (Index klein, Home groß)."""
    rows = []
    for number, p in enumerate(projects, start=1):
        rows.append(f"""      <li class="row" data-tags="{' '.join(p['tags'])}">
        <a href="{{root}}work/{p['slug']}/">
          <span class="row__num">{number:02d}</span>
          {cover(p, sizes)}
          <span class="row__title">{e(p['title'])}</span>
          <span class="row__meta">{e(p['year'])}<br>{e(tag_labels(p))}</span>
        </a>
      </li>""")
    return "\n".join(rows)


def index_page(projects):
    buttons = '<button type="button" data-tag="" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" data-tag="{tag["id"]}" aria-pressed="false">{e(tag["label"])}</button>'
        for tag in SITE["tags"])
    body = f"""  <main id="main" class="index">
    <h1 class="visually-hidden">Index of projects</h1>
    <div class="filter" role="group" aria-label="Filter projects by tag">{buttons}</div>
    <ol class="rows">
{project_rows(projects)}
    </ol>
    {FOOTER}
  </main>"""
    return page("../", f'Index – {SITE["name"]}', "All projects by Felicitas Ferch.", body, "page-index",
                scripts=["filter.js", "preview.js"])


def home_page(projects):
    """Home ist dieselbe Liste wie der Index, sortiert nach 'homeOrder'. home.js legt die Listenpunkte
    auf einen Kreisbogen; ohne JavaScript und bei reduzierter Bewegung bleibt es die Liste."""
    ordered = sorted(projects, key=lambda p: p.get("homeOrder", 99))
    body = f"""  <main id="main" class="index home">
    <h1 class="visually-hidden">{e(SITE["name"])}</h1>
    <div class="home__stage">
      <ol class="rows">
{project_rows(ordered, "(min-width: 900px) 50vw, 80vw")}
      </ol>
      <p class="home__label" aria-hidden="true"></p>
    </div>
    {FOOTER}
  </main>"""
    return page("./", SITE["name"], SITE["description"], body, "page-home", scripts=["home.js"])


def stub_page(folder, title):
    """Platzhalter für Seiten späterer Phasen (About, Imprint, Privacy), damit kein Link ins Leere führt."""
    body = f"""  <main id="main" class="stub">
    <h1>{e(title)}</h1>
    <p>This page is not built yet.</p>
    {FOOTER}
  </main>"""
    return page("../", f'{title} – {SITE["name"]}', title, body)


def covers_css(projects):
    """Bildausschnitt der Cover. Der Fokusbereich (x0, y0, x1, y1 in Pixeln des Originals) füllt
    den Rahmen immer ganz aus, egal welches Format der Rahmen hat (Index, Projektseite, später Home).
    cqw und cqh sind Prozent der Rahmenbreite und Rahmenhöhe."""
    rules = ["/* Erzeugt von build.py aus cover.focus. Nicht von Hand ändern. */"]
    for p in projects:
        info = MEDIA[f"{p['slug']}/{p['cover']['file']}"]
        W, H = info["w"], info["h"]
        x0, y0, x1, y1 = p["cover"]["focus"]
        fw, fh = (x1 - x0) / W, (y1 - y0) / H          # Anteil des Fokusbereichs am Bild
        cx, cy = (x0 + x1) / 2 / W, (y0 + y1) / 2 / H    # Mitte des Fokusbereichs
        rules.append(f""".cover--{p['slug']} img {{
  --w: max(100cqw / {fw:.4f}, 100cqh / {fh:.4f} * {W / H:.4f});   /* Bildbreite: Fokus füllt den Rahmen */
  --h: calc(var(--w) / {W / H:.4f});
  width: var(--w);
  left: clamp(100cqw - var(--w), 50cqw - {cx:.4f} * var(--w), 0px);   /* Fokus mittig, Bild nie über den Rand */
  top: clamp(100cqh - var(--h), 50cqh - {cy:.4f} * var(--h), 0px);
}}""")
    return "\n".join(rules) + "\n"


# ---------- Ablauf ----------

def main():
    projects = load_projects()
    write("assets/css/covers.css", covers_css(projects))
    for i, project in enumerate(projects):
        previous = projects[i - 1] if i > 0 else None
        following = projects[i + 1] if i < len(projects) - 1 else None
        write(f"work/{project['slug']}/index.html", project_page(project, previous, following))
    write("index/index.html", index_page(projects))
    write("index.html", home_page(projects))
    for folder, title in [("about", "About"), ("imprint", "Imprint"), ("privacy", "Privacy")]:
        write(f"{folder}/index.html", stub_page(folder, title))


if __name__ == "__main__":
    main()

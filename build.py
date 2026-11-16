#!/usr/bin/env python3
"""
build.py: erzeugt alle HTML-Seiten aus den Datendateien.

Aufruf:   python3 build.py
Eingabe:  content/site.json, content/projects/*.json, assets/media/manifest.json
          (das Manifest schreiben images.py und videos.py: Maße aller Bilder und Videos)
Ausgabe:  index.html (Home), index/index.html (Index), work/<slug>/index.html (Projekte), about/index.html,
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
ABOUT = json.loads((ROOT / "content/about.json").read_text(encoding="utf-8"))
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


def preload_cover(project):
    """Das große Bild oben auf der Projektseite schon im <head> anfordern, damit es beim Übergang von Home da ist."""
    info = MEDIA[f"{project['slug']}/{project['cover']['file']}"]
    base = f"{{root}}assets/media/{project['slug']}/{info['name']}"
    srcset = ", ".join(f"{base}-{w}.webp {w}w" for w in info["widths"])
    return f'  <link rel="preload" as="image" imagesrcset="{srcset}" imagesizes="150vw" fetchpriority="high">\n'


def tag_labels(project):
    return " · ".join(TAGS[t] for t in project["tags"])


def asset_version():
    """Kurzer Stempel aus dem Inhalt aller CSS- und JS-Dateien. Er hängt als '?v=...' an den Links, damit der
    Browser nach jeder Änderung die neuen Dateien holt und nichts Altes aus dem Zwischenspeicher nimmt
    (GitHub Pages erlaubt bis zu 10 Minuten Zwischenspeicher). Die Dateien, die andere Skripte laden
    (z. B. pointer.js), ändern sich selten und haben keinen eigenen Stempel."""
    import hashlib
    digest = hashlib.sha1()
    for path in sorted((ROOT / "assets").glob("css/*.css")) + sorted((ROOT / "assets").glob("js/*.js")):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:8]


def page(root, title, description, body, body_class="", scripts=(), early_script="", head_extra="", path=None, og_image="assets/og/default.jpg", home_href=""):
    """Das Gerüst jeder Seite. 'root' ist der Weg zurück zur obersten Ebene, z. B. '../../'."""
    v = asset_version()
    script_tags = "\n".join(f'  <script type="module" src="{root}assets/js/{s}?v={v}"></script>'
                            for s in ("nav.js", "cursor.js", *scripts))
    # Ein "frühes" Skript läuft, bevor die Seite gezeichnet wird (nur enter.js auf den Projektseiten).
    early = f'  <script src="{root}assets/js/{early_script}?v={v}"></script>\n' if early_script else ""
    # Teilen: Open Graph und Twitter Card. Adressen müssen absolut sein, deshalb SITE["url"].
    share = ""
    if path is not None:
        url, image = SITE["url"] + path, SITE["url"] + "/" + og_image
        share = (f'  <link rel="canonical" href="{url}">\n'
                 f'  <meta property="og:type" content="website">\n  <meta property="og:site_name" content="{e(SITE["name"])}">\n'
                 f'  <meta property="og:title" content="{e(title)}">\n  <meta property="og:description" content="{e(description)}">\n'
                 f'  <meta property="og:url" content="{url}">\n  <meta property="og:image" content="{image}">\n'
                 f'  <meta property="og:image:width" content="1200">\n  <meta property="og:image:height" content="630">\n'
                 f'  <meta name="twitter:card" content="summary_large_image">\n')
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; base-uri 'self'; form-action 'none'">
  <meta name="referrer" content="strict-origin-when-cross-origin">
{share}  <link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{root}favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
  <link rel="preload" href="{root}assets/fonts/InstrumentSans-Variable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{root}assets/css/site.css?v={v}">
  <link rel="stylesheet" href="{root}assets/css/covers.css?v={v}">
{head_extra}{early}{script_tags}
</head>
<body class="{body_class}">
  <a class="skip" href="#main">Skip to content</a>
  <header class="nav">
    <a class="nav__name" href="{root}{home_href}">{e(SITE["name"])}</a>
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
      <a href="{root}legal/">Legal</a>
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
                path=f"/work/{slug}/", og_image=f"assets/og/{slug}.jpg", head_extra=preload_cover(project),
                early_script="enter.js", home_href=f"?at={slug}")


def project_rows(projects, sizes="(min-width: 900px) 22rem, 5rem", cursor_label=False):
    """Die Projektliste. Sie steht als normale Liste im HTML und ist ohne JavaScript benutzbar.
    'sizes' sagt dem Browser, wie breit das Cover gezeigt wird (Index klein, Home groß).
    'data-cursor' macht den Mauszeiger über der Zeile groß; mit 'cursor_label' steht der Einzeiler (oneLiner) daneben."""
    rows = []
    for number, p in enumerate(projects, start=1):
        rows.append(f"""      <li class="row" data-tags="{' '.join(p['tags'])}">
        <a href="{{root}}work/{p['slug']}/" data-cursor="{e(p['oneLiner']) if cursor_label else ''}">
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
                scripts=["filter.js", "preview.js"], path="/index/")


def home_page(projects):
    """Home ist dieselbe Liste wie der Index, sortiert nach 'homeOrder'. home.js legt die Listenpunkte
    auf einen Kreisbogen; ohne JavaScript und bei reduzierter Bewegung bleibt es die Liste."""
    ordered = sorted(projects, key=lambda p: p.get("homeOrder", 99))
    body = f"""  <main id="main" class="index home">
    <h1 class="visually-hidden">{e(SITE["name"])}</h1>
    <div class="home__stage">
      <ol class="rows">
{project_rows(ordered, "(min-width: 900px) 50vw, 80vw", cursor_label=True)}
      </ol>
      <p class="home__label" aria-hidden="true"></p>
    </div>
    {FOOTER}
  </main>"""
    return page("./", SITE["name"], SITE["description"], body, "page-home", scripts=["home.js"], path="/")


def about_page():
    """About und Contact auf einer Seite. Der Inhalt steht in content/about.json."""
    about = json.loads((ROOT / "content/about.json").read_text(encoding="utf-8"))
    paragraphs = "\n".join(f"        <p>{e(p)}</p>" for p in about["text"])
    blocks = []
    for section in about["sections"]:
        items = []
        for item in section["items"]:
            line = f'          <li><span class="cv__lead">{e(item["lead"])}</span>'
            if item["meta"]:
                line += f'<span class="cv__meta">{e(item["meta"])}</span>'
            if item["text"]:
                line += f'<span class="cv__text">{e(item["text"])}</span>'
            items.append(line + "</li>")
        items = "\n".join(items)
        blocks.append(f"""      <section class="cv__block">
        <h2>{e(section["title"])}</h2>
        <ul>
{items}
        </ul>
      </section>""")
    contact = about["contact"]
    links = "".join(f'<li><a href="{e(l["url"])}" rel="noopener">{e(l["label"])}</a></li>' for l in contact["links"])
    media = "{root}assets/media/about"
    body = f"""  <main id="main" class="about">
    <h1 class="visually-hidden">About {e(SITE["name"])}</h1>
    <figure class="portrait">
      <img class="portrait__fog" src="{media}/fog-1800.webp" srcset="{media}/fog-900.webp 900w, {media}/fog-1800.webp 1800w"
           sizes="100vw" width="1800" height="1193" alt="{e(about["photoAlt"])}" fetchpriority="high">
      <img class="portrait__feli" src="{media}/feli-1800.webp" srcset="{media}/feli-900.webp 900w, {media}/feli-1800.webp 1800w"
           sizes="100vw" width="1800" height="1193" alt="" aria-hidden="true">
    </figure>
    <div class="about__text">
{paragraphs}
      <p class="about__cv"><a href="{{root}}assets/{e(about["cv"]["file"])}">{e(about["cv"]["label"])}</a></p>
    </div>
    <div class="cv">
{chr(10).join(blocks)}
    </div>
    <section class="contact" id="contact" aria-labelledby="contact-title">
      <h2 class="contact__label" id="contact-title">Contact</h2>
      <p class="contact__text">{e(contact["text"])}</p>
      <a class="mail" href="#contact" data-user="{e(contact["emailUser"])}" data-domain="{e(contact["emailDomain"])}">{e(contact["emailUser"])} [at] {e(contact["emailDomain"])}</a>
      <ul class="contact__links">{links}</ul>
    {FOOTER}
    </section>
  </main>"""
    return page("../", f'About – {SITE["name"]}', SITE["description"], body, "page-about", scripts=["about.js"], path="/about/")


def mail_entities():
    """Adresse als HTML-Zeichencodes: im Browser normaler, markierbarer Text, im Quelltext nicht als Klartext."""
    address = ABOUT["contact"]["emailUser"] + "@" + ABOUT["contact"]["emailDomain"]
    return "".join(f"&#{ord(c)};" for c in address)


LEGAL_TEXT = """
    <h2 id="imprint">Imprint</h2>
    <h3>Provider (§ 5 DDG)</h3>
    <p>Felicitas Ferch<br>Freelance designer<br>Hohenstaufenstr. 34<br>75177 Pforzheim<br>Germany</p>
    <h3>Contact</h3>
    <p>Email: <a href="mailto:{mail}">{mail}</a></p>
    <h3>Responsible for content (§ 18 (2) MStV)</h3>
    <p>Felicitas Ferch, address as above.</p>
    <h3>Content and links</h3>
    <p>I create the content of this website with care but cannot guarantee that it is complete, correct or up to date at all times. The website links to external websites (for example Instagram, LinkedIn and Vimeo). I have no influence on their content and am not responsible for it. At the time of linking I saw no illegal content.</p>
    <h3>Copyright</h3>
    <p>Texts, images and videos on this website are, unless stated otherwise, by Felicitas Ferch or by the people named in the project credits. Please ask before reusing them.</p>

    <h2 id="privacy">Privacy</h2>
    <h3>In short</h3>
    <p>This website does not use cookies, analytics, tracking, contact forms, external fonts, external scripts or embedded third-party content. Fonts, images and videos are hosted on the same server as the pages.</p>
    <h3>Controller</h3>
    <p>Felicitas Ferch, Hohenstaufenstr. 34, 75177 Pforzheim, Germany. Email: <a href="mailto:{mail}">{mail}</a>. I have not appointed a data protection officer.</p>
    <h3>Hosting</h3>
    <p>The website is hosted on GitHub Pages, a service of GitHub, Inc. (USA, part of Microsoft). When you open a page, GitHub's servers receive technical data that your browser sends anyway, such as your IP address, the time of the request, the page requested and the browser type, and store it in server log files. I have no access to these logs. The legal basis is my legitimate interest in providing the website securely (Art. 6(1)(f) GDPR). GitHub states that it transfers personal data from the EEA to the USA on the basis of the EU–U.S. Data Privacy Framework and standard contractual clauses. Without this processing the website cannot be delivered. GitHub's own privacy statement explains how long it keeps its logs.</p>
    <h3>Domain</h3>
    <p>The domain feliferch.com is registered with Checkdomain. Checkdomain handles the domain name system; visitors' browsers may query it to find this website.</p>
    <h3>Data in your browser</h3>
    <p>The website stores nothing on your device and does not access its sensors.</p>
    <h3>External links</h3>
    <p>Links to other websites (for example Instagram, LinkedIn and Vimeo) are plain links. Data is only sent to those providers if you click one, and their own privacy statements then apply.</p>
    <h3>Email</h3>
    <p>If you write to me, I process your address and message to answer you. I delete them when the conversation is finished, unless I am required to keep them. The legal basis is Art. 6(1)(b) or (f) GDPR. You are not obliged to write to me.</p>
    <h3>Your rights</h3>
    <p>You have the right to access, correction, deletion, restriction of processing, data portability and objection. You can also complain to a data protection authority, for example the State Commissioner for Data Protection and Freedom of Information of Baden-Württemberg (LfDI Baden-Württemberg). I do not use automated decision-making or profiling.</p>
    <p class="legal-doc__date">Last updated: November 2026</p>
"""


def legal_page():
    body = f"""  <main id="main" class="legal-doc">
    <h1>Legal</h1>
    <p class="legal-doc__toc"><a href="#imprint">Imprint</a> · <a href="#privacy">Privacy</a></p>
{LEGAL_TEXT.replace("{mail}", mail_entities())}
    {FOOTER}
  </main>"""
    return page("../", f'Legal – {SITE["name"]}', "Imprint (Impressum) and privacy information for feliferch.com. The website sets no cookies and does not track visitors.", body, path="/legal/")


def redirect_page(target, title):
    """Die alten Adressen /imprint/ und /privacy/ leiten auf die gemeinsame Seite weiter."""
    url = SITE["url"] + target
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{e(title)}</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="{url}">
  <meta http-equiv="refresh" content="0; url={target}">
</head>
<body>
  <p><a href="{target}">{e(title)}</a></p>
</body>
</html>
"""


def not_found_page():
    """404. Liegt im Hauptordner; GitHub Pages zeigt sie unter jeder unbekannten Adresse. Adressen beginnen
    deshalb mit '/', nicht mit '../' (gilt auf der eigenen Domain, nicht in der Vorschau unter einem Unterordner)."""
    body = f"""  <main id="main" class="stub legal">
    <p class="mono">404</p>
    <h1>This page does not exist.</h1>
    <p>The address may have changed, or it was never there. <a href="/">Back to the start</a> or <a href="/index/">see all projects</a>.</p>
    {FOOTER}
  </main>"""
    return page("/", f'Page not found – {SITE["name"]}', "This page does not exist.", body)


def sitemap(projects):
    paths = ["/", "/index/", "/about/", "/legal/"] + [f"/work/{p['slug']}/" for p in projects]
    rows = "\n".join(f"  <url><loc>{SITE['url']}{p}</loc></url>" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


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
    write("about/index.html", about_page())
    write("legal/index.html", legal_page())
    write("imprint/index.html", redirect_page("/legal/#imprint", "Imprint"))
    write("privacy/index.html", redirect_page("/legal/#privacy", "Privacy"))
    write("404.html", not_found_page())
    write("sitemap.xml", sitemap(projects))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")


if __name__ == "__main__":
    main()

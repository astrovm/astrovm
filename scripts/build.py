"""Builds the profile images and the projects section of the README.

Projects come from data/projects.toml in astrovm.github.io, so the list
here always matches 4st.li/projects. Everything is drawn as SVG in the
site colors and font, so it looks like the site on GitHub.
"""

import base64
import html
import re
import sys
import textwrap
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "profile"
PROJECTS_URL = "https://raw.githubusercontent.com/astrovm/astrovm.github.io/main/data/projects.toml"
IMAGE_URL = "https://4st.li/images/projects/{}.webp"

# Same colors as static/terminal.css and the project cards on 4st.li.
BG = "#211f2b"
FG = "#eceae5"
ACCENT = "#f462c6"
CARD = "#292732"
BORDER = "#393741"
MUTED = "#868488"
CONTAIN = "#3a273e"

# Fira Code is 0.6em wide per character.
CHAR = 0.6


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "astrovm-profile"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def data_uri(mime, data):
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


FONT = data_uri("font/woff2", (ROOT / "assets/FiraCode.woff2").read_bytes())
STYLE = f"""<style>
@font-face {{ font-family: "Fira Code"; src: url({FONT}) format("woff2"); font-weight: 300 700; }}
text {{ font-family: "Fira Code", Monaco, Consolas, "Ubuntu Mono", monospace; }}
</style>"""


def esc(text):
    return html.escape(text, quote=True)


def write(path, svg):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)


# Header: a terminal that types itself, with oneko running in to nap.

PROMPT = "astro@web:~$ "
LINES = [
    ("cmd", "whoami"),
    ("out", "astro, buenos aires"),
    ("cmd", "cat motd"),
    ("out", "everything's computer."),
    ("out", "prepare for unforeseen consequences."),
]
TYPE_SPEED = 0.07  # seconds per character


def typed(x, y, size, text, begin, color):
    """Text that shows up one character at a time, starting at `begin`."""
    width = size * CHAR
    # The last step is a bit wider, so letters like "d" aren't cut off.
    steps = ";".join(f"{i * width + (4 if i == len(text) else 0):.1f}" for i in range(len(text) + 1))
    dur = TYPE_SPEED * len(text)
    clip = f"t{x}-{y}"
    return f"""<clipPath id="{clip}"><rect x="{x}" y="{y - size}" width="0" height="{size * 1.5}">
<animate attributeName="width" values="{steps}" dur="{dur:.2f}s" begin="{begin:.2f}s" calcMode="discrete" fill="freeze"/>
</rect></clipPath>
<text x="{x}" y="{y}" font-size="{size}" fill="{color}" clip-path="url(#{clip})" xml:space="preserve">{esc(text)}</text>""", begin + dur


def appear(element, begin):
    return f"""<g opacity="0">{element}<set attributeName="opacity" to="1" begin="{begin:.2f}s" fill="freeze"/></g>"""


def sprite(col, row, extra=""):
    """One 32px frame from oneko.gif."""
    return f"""<svg width="32" height="32" viewBox="{col * 32} {row * 32} 32 32" {extra}><image href="{CAT}" width="256" height="128" style="image-rendering: pixelated"/></svg>"""


def flip(frames, dur, begin="0s", end=None):
    """Swaps between sprite frames forever, like oneko.js does."""
    n = len(frames)
    out = []
    for i, (col, row) in enumerate(frames):
        values = ";".join("visible" if j == i else "hidden" for j in range(n))
        out.append(
            f"""<g visibility="hidden"><animate attributeName="visibility" values="{values}" dur="{dur * n}s" begin="{begin}" {f'end="{end}"' if end else ''} calcMode="discrete" repeatCount="indefinite"/>{sprite(col, row)}</g>"""
        )
    return "".join(out)


def header():
    w, h, size = 860, 340, 16
    x, y, gap = 32, 104, 30
    parts = []
    t = 0.6
    for i, (kind, text) in enumerate(LINES):
        if kind == "cmd":
            if i:
                y += 12
            parts.append(appear(f'<text x="{x}" y="{y}" font-size="{size}" fill="{ACCENT}" font-weight="700" xml:space="preserve">{esc(PROMPT)}</text>', t))
            el, t = typed(x + len(PROMPT) * size * CHAR, y, size, text, t + 0.3, FG)
            parts.append(el)
            t += 0.4
        else:
            parts.append(appear(f'<text x="{x}" y="{y}" font-size="{size}" fill="{FG}" xml:space="preserve">{esc(text)}</text>', t))
            t += 0.15
        y += gap
    # Last prompt with a blinking block cursor.
    y += 12
    parts.append(appear(f'<text x="{x}" y="{y}" font-size="{size}" fill="{ACCENT}" font-weight="700" xml:space="preserve">{esc(PROMPT)}</text>', t))
    cx = x + len(PROMPT) * size * CHAR
    parts.append(
        f"""<rect x="{cx}" y="{y - size + 2}" width="{size * CHAR}" height="{size + 2}" fill="{FG}" opacity="0">
<animate attributeName="opacity" values="1;0" dur="1s" begin="{t:.2f}s" calcMode="discrete" repeatCount="indefinite"/></rect>"""
    )

    # oneko runs in from the left along the bottom and falls asleep.
    run_end = t + 3.5
    cat_y = h - 32 - 24
    stop_x = w - 32 - 40
    cat = f"""<g transform="translate(-40 {cat_y})">
<animateTransform attributeName="transform" type="translate" from="-40 {cat_y}" to="{stop_x} {cat_y}" begin="{t:.2f}s" dur="3.5s" fill="freeze"/>
<g visibility="visible"><set attributeName="visibility" to="hidden" begin="{run_end:.2f}s" fill="freeze"/>{flip([(3, 0), (3, 1)], 0.15)}</g>
<g visibility="hidden"><set attributeName="visibility" to="visible" begin="{run_end:.2f}s" fill="freeze"/>{flip([(2, 0), (2, 1)], 0.6)}</g>
</g>"""

    logo_w = len("astro@web") * size * CHAR + 20
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="astro@web: astro, buenos aires. everything's computer. prepare for unforeseen consequences.">
{STYLE}
<rect x="6" y="6" width="{w - 12}" height="{h - 12}" fill="{ACCENT}"/>
<rect x="1" y="1" width="{w - 12}" height="{h - 12}" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>
<rect x="{x}" y="28" width="{logo_w}" height="30" fill="{ACCENT}"/>
<text x="{x + 10}" y="49" font-size="{size}" font-weight="700" fill="{BG}">astro@web</text>
<text x="{w - 32 - 12}" y="49" font-size="13" fill="{MUTED}" text-anchor="end">buenos aires · ar</text>
{''.join(parts)}
{cat}
</svg>
"""


# Link buttons, like the buttons on 4st.li.

LINKS = [
    ("4st.li", "https://4st.li/"),
    ("blog", "https://4st.li/blog/"),
    ("projects", "https://4st.li/projects/"),
    ("configs", "https://4st.li/configs/"),
    ("contact", "https://4st.li/contact/"),
    ("x", "https://x.com/astrovm"),
]


def button(label):
    size = 15
    w, h = round(len(label) * size * CHAR + 36), 38
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w + 4}" height="{h + 4}" viewBox="0 0 {w + 4} {h + 4}" role="img" aria-label="{esc(label)}">
{STYLE}
<rect x="4" y="4" width="{w}" height="{h}" fill="{ACCENT}"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="{BG}" stroke="{ACCENT}" stroke-width="2"/>
<text x="{(w) / 2}" y="{h / 2 + 5}" font-size="{size}" font-weight="700" fill="{ACCENT}" text-anchor="middle">{esc(label)}</text>
</svg>
"""


# Section titles as prompt lines.

HEADINGS = {
    "projects": "ls ~/projects",
    "posts": "tail ~/blog",
    "stats": "cat ~/stats",
}


def heading(command):
    size = 17
    w = round((len(PROMPT) + len(command)) * size * CHAR + 4)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="30" viewBox="0 0 {w} 30" role="img" aria-label="{esc(command)}">
{STYLE}
<text x="0" y="21" font-size="{size}" xml:space="preserve"><tspan fill="{ACCENT}" font-weight="700">{esc(PROMPT)}</tspan><tspan fill="{MUTED}">{esc(command)}</tspan></text>
</svg>
"""


# Project cards, like the ones on 4st.li/projects.

CARD_W, IMG_H, PAD = 300, 188, 14
NAME, DESC, HOST = 15, 12, 11
DESC_LINES = 3


def card(project, image):
    host = urlparse(project["url"])
    host = (host.netloc + host.path).rstrip("/")
    lines = textwrap.wrap(project["en"], int((CARD_W - 2 * PAD) / (DESC * CHAR)))[:DESC_LINES]
    h = IMG_H + PAD + NAME + 10 + DESC_LINES * DESC * 1.45 + 8 + HOST + PAD
    contain = project.get("fit") == "contain"
    img = (
        f'<rect x="1" y="1" width="{CARD_W - 2}" height="{IMG_H}" fill="{CONTAIN}"/>'
        f'<image href="{image}" x="20" y="20" width="{CARD_W - 40}" height="{IMG_H - 40}" preserveAspectRatio="xMidYMid meet"/>'
        if contain
        else f'<image href="{image}" x="1" y="1" width="{CARD_W - 2}" height="{IMG_H}" preserveAspectRatio="xMidYMin slice"/>'
    )
    y = IMG_H + PAD + NAME
    desc = "".join(
        f'<text x="{PAD}" y="{y + 10 + (i + 1) * DESC * 1.45 - 4:.1f}" font-size="{DESC}" fill="{FG}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{h:.0f}" viewBox="0 0 {CARD_W} {h:.0f}" role="img" aria-label="{esc(project['name'])}: {esc(project['en'])}">
{STYLE}
<clipPath id="c"><rect x="1" y="1" width="{CARD_W - 2}" height="{IMG_H}"/></clipPath>
<rect x="1" y="1" width="{CARD_W - 2}" height="{h - 2:.0f}" fill="{CARD}"/>
<g clip-path="url(#c)">{img}</g>
<line x1="1" y1="{IMG_H + 1}" x2="{CARD_W - 1}" y2="{IMG_H + 1}" stroke="{BORDER}" stroke-width="2"/>
<rect x="1" y="1" width="{CARD_W - 2}" height="{h - 2:.0f}" fill="none" stroke="{BORDER}" stroke-width="2"/>
<text x="{PAD}" y="{y}" font-size="{NAME}" font-weight="700" fill="{ACCENT}">{esc(project['name'])}</text>
{desc}
<text x="{PAD}" y="{h - PAD:.0f}" font-size="{HOST}" fill="{MUTED}">{esc(host)}</text>
</svg>
"""


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def projects_section(projects):
    # Start clean, so projects removed from the site go away here too.
    for old in (OUT / "projects").glob("*.svg"):
        old.unlink()
    cards = []
    for p in projects:
        name = slug(p["name"])
        image = data_uri("image/webp", fetch(IMAGE_URL.format(p["image"])))
        write(OUT / "projects" / f"{name}.svg", card(p, image))
        cards.append(f'<a href="{esc(p["url"])}"><img src="profile/projects/{name}.svg" alt="{esc(p["name"])}: {esc(p["en"])}" width="32%"></a>')
    return '<p align="center">\n' + "\n".join(cards) + "\n</p>"


def replace_section(readme, name, body):
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    if not pattern.search(readme):
        sys.exit(f"README is missing the {name} markers")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", readme)


CAT = data_uri("image/gif", (ROOT / "assets/oneko.gif").read_bytes())


def main():
    projects = tomllib.loads(fetch(PROJECTS_URL).decode())["projects"]
    write(OUT / "header.svg", header())
    for label, _ in LINKS:
        write(OUT / "links" / f"{slug(label)}.svg", button(label))
    for name, command in HEADINGS.items():
        write(OUT / "headings" / f"{name}.svg", heading(command))
    links = "\n".join(f'<a href="{url}"><img src="profile/links/{slug(label)}.svg" alt="{label}" height="42"></a>' for label, url in LINKS)

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    readme = replace_section(readme, "LINKS", f'<p align="center">\n{links}\n</p>')
    readme = replace_section(readme, "PROJECTS", projects_section(projects))
    readme_path.write_text(readme)


if __name__ == "__main__":
    main()

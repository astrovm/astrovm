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
PROMPT = "astro@web:~$ "


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


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def write(path, svg):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)


# Link buttons, like the buttons on 4st.li.

LINKS = [
    ("4st.li", "https://4st.li/"),
    ("blog", "https://4st.li/blog/"),
    ("configs", "https://4st.li/configs/"),
    ("contact", "https://4st.li/contact/"),
    ("x", "https://x.com/astrovm"),
]


def button(label):
    size = 14
    w, h = round(len(label) * size * CHAR + 28), 32
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w + 4}" height="{h + 4}" viewBox="0 0 {w + 4} {h + 4}" role="img" aria-label="{esc(label)}">
{STYLE}
<rect x="4" y="4" width="{w}" height="{h}" fill="{ACCENT}"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="{BG}" stroke="{ACCENT}" stroke-width="2"/>
<text x="{w / 2}" y="{h / 2 + 5}" font-size="{size}" font-weight="700" fill="{ACCENT}" text-anchor="middle">{esc(label)}</text>
</svg>
"""


# Section titles as prompt lines.

HEADINGS = {
    "projects": "ls ~/projects",
    "posts": "tail ~/blog",
    "stats": "cat ~/stats",
}


def heading(command):
    size = 16
    w = round((len(PROMPT) + len(command)) * size * CHAR + 4)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="28" viewBox="0 0 {w} 28" role="img" aria-label="{esc(command)}">
{STYLE}
<text x="0" y="20" font-size="{size}" xml:space="preserve"><tspan fill="{ACCENT}" font-weight="700">{esc(PROMPT)}</tspan><tspan fill="{MUTED}">{esc(command)}</tspan></text>
</svg>
"""


# Small project cards: thumbnail on the left, name and description on the right.

CARD_W, CARD_H = 400, 76
THUMB_W = 120
PAD = 12
NAME, DESC = 14, 11


def card(project, image):
    x = THUMB_W + PAD
    lines = textwrap.wrap(project["en"], int((CARD_W - x - PAD) / (DESC * CHAR)))
    if len(lines) > 2:
        lines = [lines[0], textwrap.shorten(" ".join(lines[1:]), int((CARD_W - x - PAD) / (DESC * CHAR)), placeholder="…")]
    contain = project.get("fit") == "contain"
    img = (
        f'<rect x="1" y="1" width="{THUMB_W}" height="{CARD_H - 2}" fill="{CONTAIN}"/>'
        f'<image href="{image}" x="10" y="8" width="{THUMB_W - 18}" height="{CARD_H - 16}" preserveAspectRatio="xMidYMid meet"/>'
        if contain
        else f'<image href="{image}" x="1" y="1" width="{THUMB_W}" height="{CARD_H - 2}" preserveAspectRatio="xMidYMin slice"/>'
    )
    desc = "".join(
        f'<text x="{x}" y="{46 + i * 15}" font-size="{DESC}" fill="{FG}">{esc(line)}</text>' for i, line in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="{esc(project['name'])}: {esc(project['en'])}">
{STYLE}
<clipPath id="c"><rect x="1" y="1" width="{THUMB_W}" height="{CARD_H - 2}"/></clipPath>
<rect x="1" y="1" width="{CARD_W - 2}" height="{CARD_H - 2}" fill="{CARD}"/>
<g clip-path="url(#c)">{img}</g>
<line x1="{THUMB_W + 1}" y1="1" x2="{THUMB_W + 1}" y2="{CARD_H - 1}" stroke="{BORDER}" stroke-width="2"/>
<rect x="1" y="1" width="{CARD_W - 2}" height="{CARD_H - 2}" fill="none" stroke="{BORDER}" stroke-width="2"/>
<text x="{x}" y="26" font-size="{NAME}" font-weight="700" fill="{ACCENT}">{esc(project['name'])}</text>
{desc}
</svg>
"""


def projects_section(projects):
    # Start clean, so projects removed from the site go away here too.
    for old in (OUT / "projects").glob("*.svg"):
        old.unlink()
    cards = []
    for p in projects:
        name = slug(p["name"])
        image = data_uri("image/webp", fetch(IMAGE_URL.format(p["image"])))
        write(OUT / "projects" / f"{name}.svg", card(p, image))
        cards.append(f'<a href="{esc(p["url"])}"><img src="profile/projects/{name}.svg" alt="{esc(p["name"])}: {esc(p["en"])}" width="49%"></a>')
    return "<p>\n" + "\n".join(cards) + "\n</p>"


def replace_section(readme, name, body):
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    if not pattern.search(readme):
        sys.exit(f"README is missing the {name} markers")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", readme)


def main():
    projects = tomllib.loads(fetch(PROJECTS_URL).decode())["projects"]
    for label, _ in LINKS:
        write(OUT / "links" / f"{slug(label)}.svg", button(label))
    for name, command in HEADINGS.items():
        write(OUT / "headings" / f"{name}.svg", heading(command))
    links = "\n".join(f'<a href="{url}"><img src="profile/links/{slug(label)}.svg" alt="{label}" height="36"></a>' for label, url in LINKS)

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    readme = replace_section(readme, "LINKS", f"<p>\n{links}\n</p>")
    readme = replace_section(readme, "PROJECTS", projects_section(projects))
    readme_path.write_text(readme)


if __name__ == "__main__":
    main()

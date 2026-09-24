"""Build a single-page HTML gallery of all previews (previews/index.html) with downscaled embedded images,
plus previews/contact_sheet.png. Used for the shareable artifact page and the README."""
from __future__ import annotations

import base64
import io
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREV = os.path.join(ROOT, "previews")
SCHEM = os.path.join(ROOT, "schematics")


def _data_uri(path: str, max_w: int = 1400, quality: int = 82) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def load_catalog():
    path = os.path.join(ROOT, "catalog.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")


def iso_path(n):
    return os.path.join(PREV, n + "_iso.png")


def plan_path(n):
    return os.path.join(PREV, n + "_plan.png")


def build_html(out: str = os.path.join(PREV, "index.html")) -> str:
    catalog = load_catalog()
    try:
        summary = json.load(open(os.path.join(PREV, "_summary.json")))
    except Exception:
        summary = {}
    names = [n for n in catalog if os.path.exists(os.path.join(SCHEM, n + ".schem"))]
    names += sorted(f[:-6] for f in os.listdir(SCHEM) if f.endswith(".schem") and not f.startswith("_") and f[:-6] not in catalog)
    total_blocks = sum(summary.get(n, {}).get("stats", {}).get("blocks", 0) for n in names)
    order = ["Vaisseaux écrasés", "Labos abandonnés", "Ville tech des salopards", "Camps d'exploration", "Bonus"]
    by_cat = {c: [] for c in order}
    for n in names:
        m = catalog.get(n, {})
        by_cat.setdefault(m.get("category", "Bonus"), []).append(n)
    sections = []
    for c in order:
        items = [n for n in by_cat.get(c, []) if os.path.exists(os.path.join(PREV, n + "_iso.png"))]
        if not items:
            continue
        cards_html = []
        for n in items:
            meta = catalog.get(n, {})
            st = summary.get(n, {}).get("stats", {})
            size = "×".join(str(v) for v in st.get("size", [])) if st else ""
            blocks = f"{st.get('blocks', 0):,}".replace(",", "\u202f") if st else ""
            cards_html.append(f"""
<article class="card" id="{n}">
  <header><h3>{meta.get('title', n)}</h3>
    <div class="meta"><code>{n}.schem</code><span>{size}</span><span>{blocks} blocs</span><span class="paste">{meta.get('paste', '')}</span></div>
  </header>
  <p>{meta.get('fr', '')}</p>
  <img src="{_data_uri(iso_path(n))}" alt="Rendu isométrique de {meta.get('title', n)}" loading="lazy">
  <details><summary>Vue de dessus</summary><img src="{_data_uri(plan_path(n), 700)}" alt="Vue de dessus de {meta.get('title', n)}" loading="lazy"></details>
</article>""")
        sections.append(f"""<section class="cat" id="{slug(c)}"><h2>{c}</h2><div class="cards">{''.join(cards_html)}</div></section>""")
    nav = "".join(f'<a href="#{slug(c)}">{c}</a>' for c in order if by_cat.get(c))
    html = f"""<title>Schematics Neige</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Manrope:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
:root{{--bg:#f6f2f8;--card:#fffdff;--ink:#2a2236;--muted:#75688a;--accent:#7f63c9;--accent2:#c97fb0;--line:#e4d9ee;--chip:#efe8f7;
  --display:"Sora",system-ui,sans-serif;--body:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#171220;--card:#211a2c;--ink:#efe7f7;--muted:#a898bd;--accent:#b79cf2;--accent2:#e39ccb;--line:#362c47;--chip:#2c2439;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#171220;--card:#211a2c;--ink:#efe7f7;--muted:#a898bd;--accent:#b79cf2;--accent2:#e39ccb;--line:#362c47;--chip:#2c2439;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font:16px/1.55 var(--body);padding:0 16px}}
.wrap{{max-width:1080px;margin:0 auto;padding-block:28px 60px}}
h1{{font:700 clamp(1.7rem,4vw,2.4rem)/1.1 var(--display);margin:0 0 8px;text-wrap:balance}}
.lead{{color:var(--muted);max-width:70ch;margin:0 0 18px}}
.stats{{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:.9rem;margin:0 0 22px;font-variant-numeric:tabular-nums}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 34px}}
nav a{{color:var(--accent);text-decoration:none;background:var(--chip);border-radius:999px;padding:6px 14px;font-size:.9rem;font-weight:600}}
nav a:focus-visible,summary:focus-visible{{outline:2px solid var(--accent2);outline-offset:2px}}
.cat h2{{font:600 1.35rem/1.2 var(--display);margin:0 0 14px;padding-top:8px;border-top:1px solid var(--line)}}
.cards{{display:grid;gap:22px;margin:0 0 36px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px}}
.card h3{{font:600 1.15rem/1.25 var(--display);margin:0 0 6px}}
.meta{{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;color:var(--muted);font-size:.85rem;font-variant-numeric:tabular-nums}}
.meta code{{font:.85rem var(--mono);color:var(--accent)}}
.meta .paste{{color:var(--accent2);font-weight:600}}
.card p{{margin:10px 0 14px;color:var(--ink)}}
.card img{{width:100%;height:auto;max-width:100%;border-radius:10px;display:block;border:1px solid var(--line)}}
details{{margin-top:12px}} summary{{cursor:pointer;color:var(--accent);font-weight:600}}
details img{{margin-top:10px;max-width:520px}}
footer{{color:var(--muted);font-size:.85rem;margin-top:30px;border-top:1px solid var(--line);padding-top:14px}}
@media (prefers-reduced-motion:no-preference){{a{{transition:opacity .15s}}}}
</style>
<div class="wrap">
<h1>Schematics Neige</h1>
<p class="lead">Pack de {len(names)} structures vanilla 1.20.1 (format Sponge .schem, WorldEdit / FAWE / Litematica) pour le monde enneigé au ciel rose : vaisseaux écrasés, laboratoires abandonnés, ville tech des salopards, camps d'exploration et bonus. Les rendus sont isométriques et sans textures : en jeu, avec les textures et les shaders, tout est plus riche.</p>
<div class="stats"><span>{len(names)} schematics</span><span>{total_blocks:,} blocs au total</span><span>tous les blocs sont vanilla 1.20.1</span></div>
<nav>{nav}</nav>
{''.join(sections)}
<footer>Rendu : rot 0 = caméra au sud-est, rot 1 = nord-est, rot 2 = nord-ouest, rot 3 = sud-ouest. Vue de dessus : nord en haut, est à droite. Généré avec les outils du dépôt (<code>python3 -m tools.gallery</code>).</footer>
</div>
"""
    with open(out, "w") as f:
        f.write(html)
    return out


def contact_sheet(out: str = os.path.join(PREV, "contact_sheet.png"), cols: int = 3, cell: int = 640) -> str:
    names = sorted(f[:-6] for f in os.listdir(SCHEM) if f.endswith(".schem") and not f.startswith("_"))
    imgs = []
    for n in names:
        p = os.path.join(PREV, n + "_iso.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        # take the first rotation (top-left quadrant)
        im = im.crop((0, 0, im.width // 2, im.height // 2))
        im.thumbnail((cell, cell))
        imgs.append((n, im))
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 24)), (214, 200, 214))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for i, (n, im) in enumerate(imgs):
        x, y = (i % cols) * cell, (i // cols) * (cell + 24)
        sheet.paste(im, (x + (cell - im.width) // 2, y + 24 + (cell - im.height) // 2))
        d.text((x + 8, y + 2), n, fill=(40, 30, 50), font=font)
    sheet.save(out, optimize=True)
    return out


if __name__ == "__main__":
    print(build_html())
    print(contact_sheet())

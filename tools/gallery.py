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


def build_html(out: str = os.path.join(PREV, "index.html")) -> str:
    catalog = load_catalog()
    names = sorted(f[:-6] for f in os.listdir(SCHEM) if f.endswith(".schem") and not f.startswith("_"))
    cards = []
    for n in names:
        iso = os.path.join(PREV, n + "_iso.png")
        plan = os.path.join(PREV, n + "_plan.png")
        if not os.path.exists(iso):
            continue
        meta = catalog.get(n, {})
        size = meta.get("size", "")
        desc = meta.get("fr", "")
        cat = meta.get("category", "")
        cards.append(f"""
<section class="card" id="{n}" data-cat="{cat}">
  <header><h2>{meta.get('title', n)}</h2><code>{n}.schem</code><span class="size">{size}</span></header>
  <p>{desc}</p>
  <img src="{_data_uri(iso)}" alt="{n} isometric" loading="lazy">
  <details><summary>Vue de dessus</summary><img src="{_data_uri(plan, 700)}" alt="{n} plan" loading="lazy"></details>
</section>""")
    html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Schematics Neige</title>
<style>
:root{{--bg:#f3eef6;--card:#ffffff;--ink:#2a2233;--muted:#6f6478;--accent:#8a5cc7;--line:#e2d8ea}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#1b1622;--card:#251e2e;--ink:#efe7f5;--muted:#a898b8;--accent:#c9a6ff;--line:#3a3046}}}}
:root[data-theme="dark"]{{--bg:#1b1622;--card:#251e2e;--ink:#efe7f5;--muted:#a898b8;--accent:#c9a6ff;--line:#3a3046}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:24px 16px}} h1{{font-size:1.8rem;margin:0 0 4px}} .lead{{color:var(--muted);margin:0 0 20px}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 24px}} nav a{{color:var(--accent);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:.9rem}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:0 0 20px}}
.card header{{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline}} .card h2{{font-size:1.2rem;margin:0}}
.card code{{color:var(--accent);font-size:.9rem}} .size{{color:var(--muted);font-size:.85rem}} .card p{{color:var(--muted);margin:6px 0 12px}}
.card img{{width:100%;height:auto;border-radius:10px;display:block}} details{{margin-top:10px}} summary{{cursor:pointer;color:var(--accent)}}
</style></head><body><main>
<h1>Schematics « Neige »</h1>
<p class="lead">{len(cards)} structures vanilla 1.20.1 (format Sponge .schem) pour le monde enneigé : vaisseaux écrasés, labos abandonnés, ville tech des salopards, camps d'exploration et bonus. Rendu isométrique approximatif (sans textures).</p>
<nav>{''.join(f'<a href="#{n}">{catalog.get(n, {}).get("title", n)}</a>' for n in names if os.path.exists(os.path.join(PREV, n + "_iso.png")))}</nav>
{''.join(cards)}
</main></body></html>"""
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

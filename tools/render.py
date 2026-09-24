"""
Isometric preview renderer (no Minecraft assets needed). Produces PNGs used to visually check builds.

render_views(schem, "previews/name")  ->  previews/name_iso.png (4 rotations) + previews/name_plan.png (top view)
render_iso(schem, rot=0, tw=16)       ->  PIL.Image of one rotation

Rotation 0 looks at the build from the south-east corner: the +x (east) face is drawn on the right,
the +z (south) face on the left. Rotation k rotates the build k*90 degrees clockwise before rendering, so the
camera sits at the NE corner for rot 1, NW for rot 2 and SW for rot 3 (all four sides are visible).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .schem import Schematic, AIR
from .colors import block_color, is_transparent, is_emissive

BG_TOP = (168, 146, 176)
BG_BOTTOM = (214, 200, 214)
LIGHT_TOP, LIGHT_RIGHT, LIGHT_LEFT = 1.0, 0.80, 0.60


def _shape_boxes(block: str) -> List[Tuple[float, float, float, float, float, float]]:
    """Return sub-boxes (x0,y0,z0,x1,y1,z1) in unit-cube coordinates approximating the block's shape."""
    name = block.split("[")[0]
    short = name.split(":", 1)[-1]
    props: Dict[str, str] = {}
    if "[" in block:
        for kv in block[block.index("[") + 1:-1].split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                props[k] = v
    if short.endswith("_stairs"):
        half = props.get("half", "bottom")
        f = props.get("facing", "north")
        base = (0, 0, 0, 1, 0.5, 1) if half == "bottom" else (0, 0.5, 0, 1, 1, 1)
        ylo, yhi = (0.5, 1) if half == "bottom" else (0, 0.5)
        side = {"north": (0, 0, 1, 0.5), "south": (0, 0.5, 1, 1), "west": (0, 0, 0.5, 1), "east": (0.5, 0, 1, 1)}[f]
        step = (side[0], ylo, side[1], side[2], yhi, side[3])
        return [base, step]
    if short.endswith("_slab"):
        t = props.get("type", "bottom")
        return [(0, 0, 0, 1, 1, 1)] if t == "double" else ([(0, 0, 0, 1, 0.5, 1)] if t == "bottom" else [(0, 0.5, 0, 1, 1, 1)])
    if short == "snow":
        n = int(props.get("layers", "1"))
        return [(0, 0, 0, 1, n / 8, 1)]
    if short.endswith("_carpet") or short in ("moss_carpet", "pink_petals", "lily_pad") or short.endswith("_pressure_plate"):
        return [(0, 0, 0, 1, 0.07, 1)]
    if short.endswith("_trapdoor"):
        if props.get("open", "false") == "true":
            f = props.get("facing", "north")
            return [{"north": (0, 0, 0.8, 1, 1, 1), "south": (0, 0, 0, 1, 1, 0.2), "west": (0.8, 0, 0, 1, 1, 1), "east": (0, 0, 0, 0.2, 1, 1)}[f]]
        return [(0, 0, 0, 1, 0.19, 1)] if props.get("half", "bottom") == "bottom" else [(0, 0.81, 0, 1, 1, 1)]
    if short.endswith("_door"):
        f = props.get("facing", "north")
        return [{"north": (0, 0, 0, 1, 1, 0.19), "south": (0, 0, 0.81, 1, 1, 1), "west": (0, 0, 0, 0.19, 1, 1), "east": (0.81, 0, 0, 1, 1, 1)}[f]]
    if short.endswith("_fence") or short.endswith("_wall") or short == "iron_bars" or short.endswith("glass_pane") or short.endswith("_fence_gate"):
        boxes = [(0.375, 0, 0.375, 0.625, 1, 0.625)] if not short.endswith("glass_pane") and short != "iron_bars" else []
        thin = 0.44 if short.endswith("_wall") else 0.4375
        if props.get("north") in ("true", "low", "tall"):
            boxes.append((thin, 0, 0, 1 - thin, 0.9 if short.endswith("_fence") else 1, 0.5))
        if props.get("south") in ("true", "low", "tall"):
            boxes.append((thin, 0, 0.5, 1 - thin, 0.9 if short.endswith("_fence") else 1, 1))
        if props.get("west") in ("true", "low", "tall"):
            boxes.append((0, 0, thin, 0.5, 0.9 if short.endswith("_fence") else 1, 1 - thin))
        if props.get("east") in ("true", "low", "tall"):
            boxes.append((0.5, 0, thin, 1, 0.9 if short.endswith("_fence") else 1, 1 - thin))
        if not boxes:
            boxes = [(0.4375, 0, 0.4375, 0.5625, 1, 0.5625)]
        return boxes
    if short in ("end_rod", "lightning_rod", "chain", "torch", "soul_torch", "redstone_torch", "wall_torch", "soul_wall_torch",
                 "redstone_wall_torch", "candle", "lever", "pointed_dripstone", "bamboo", "sugar_cane", "scaffolding",
                 "ladder", "tripwire_hook", "brewing_stand") or short.endswith("_candle"):
        ax = props.get("axis", "y")
        if short == "chain" and ax != "y":
            return [(0, 0.4, 0.4, 1, 0.6, 0.6)] if ax == "x" else [(0.4, 0.4, 0, 0.6, 0.6, 1)]
        f = props.get("facing", "up")
        if short in ("end_rod", "lightning_rod") and f in ("north", "south", "east", "west"):
            return [(0.4, 0.4, 0, 0.6, 0.6, 1)] if f in ("north", "south") else [(0, 0.4, 0.4, 1, 0.6, 0.6)]
        h = 1.0 if short in ("end_rod", "lightning_rod", "chain", "bamboo", "sugar_cane", "scaffolding", "ladder", "pointed_dripstone") else 0.6
        return [(0.42, 0, 0.42, 0.58, h, 0.58)]
    if short in ("lantern", "soul_lantern"):
        return [(0.3, 0.0 if props.get("hanging", "false") == "false" else 0.2, 0.3, 0.7, 0.55 if props.get("hanging", "false") == "false" else 0.75, 0.7)]
    if short.endswith("_head") or short.endswith("_skull") or short == "flower_pot" or short == "decorated_pot" or short == "sea_pickle":
        return [(0.25, 0, 0.25, 0.75, 0.5, 0.75)]
    if short in ("amethyst_cluster", "large_amethyst_bud", "medium_amethyst_bud", "small_amethyst_bud"):
        return [(0.2, 0, 0.2, 0.8, 0.7, 0.8)]
    if short in ("campfire", "soul_campfire", "cauldron", "water_cauldron", "powder_snow_cauldron", "hopper", "composter",
                 "anvil", "chipped_anvil", "damaged_anvil", "grindstone", "bell", "lectern", "enchanting_table", "daylight_detector",
                 "stonecutter", "cake", "conduit", "beacon", "end_portal_frame", "respawn_anchor", "chest", "trapped_chest",
                 "ender_chest", "sculk_sensor", "calibrated_sculk_sensor", "sculk_shrieker", "turtle_egg", "sniffer_egg", "bed") or short.endswith("_bed"):
        hh = {"campfire": 0.45, "soul_campfire": 0.45, "daylight_detector": 0.4, "stonecutter": 0.6, "cake": 0.5, "sculk_sensor": 0.5,
              "calibrated_sculk_sensor": 0.5, "sculk_shrieker": 0.5, "enchanting_table": 0.75, "end_portal_frame": 0.8, "bed": 0.56,
              "lectern": 0.9, "chest": 0.88, "trapped_chest": 0.88, "ender_chest": 0.88, "bell": 0.8}.get(short, 0.9)
        pad = 0.06 if short in ("chest", "trapped_chest", "ender_chest") else 0.0
        return [(pad, 0, pad, 1 - pad, hh, 1 - pad)]
    if short in ("short_grass", "grass", "fern", "tall_grass", "large_fern", "dead_bush", "sweet_berry_bush", "cobweb", "vine",
                 "glow_lichen", "sculk_vein", "seagrass", "kelp", "hanging_roots", "weeping_vines", "twisting_vines", "crimson_roots",
                 "warped_roots", "nether_sprouts", "mangrove_propagule", "torchflower", "pitcher_plant", "spore_blossom", "azalea",
                 "flowering_azalea", "big_dripleaf", "small_dripleaf", "cave_vines", "wither_rose", "poppy", "dandelion", "allium",
                 "azure_bluet", "blue_orchid", "cornflower", "lily_of_the_valley", "oxeye_daisy", "red_tulip", "orange_tulip",
                 "white_tulip", "pink_tulip", "sunflower", "lilac", "rose_bush", "peony", "brown_mushroom", "red_mushroom",
                 "crimson_fungus", "warped_fungus", "frogspawn", "redstone_wire", "rail", "powered_rail", "detector_rail",
                 "activator_rail", "tripwire", "wheat", "carrots", "potatoes", "beetroots", "nether_wart", "cactus") or short.endswith("_sapling"):
        if short in ("redstone_wire", "rail", "powered_rail", "detector_rail", "activator_rail", "tripwire", "vine", "glow_lichen", "sculk_vein"):
            return [(0, 0, 0, 1, 0.08, 1)]
        return [(0.25, 0, 0.25, 0.75, 0.7, 0.75)]
    if short.endswith("_button"):
        return [(0.3, 0, 0.3, 0.7, 0.15, 0.7)]
    if short.endswith("_banner") and "wall" not in short:
        return [(0.42, 0, 0.42, 0.58, 1, 0.58), (0.1, 0.4, 0.45, 0.9, 1, 0.55)]
    if short.endswith("_wall_banner") or short.endswith("_wall_sign") or short.endswith("_wall_hanging_sign"):
        f = props.get("facing", "north")
        return [{"north": (0.05, 0.1, 0.85, 0.95, 0.95, 1), "south": (0.05, 0.1, 0, 0.95, 0.95, 0.15),
                 "west": (0.85, 0.1, 0.05, 1, 0.95, 0.95), "east": (0, 0.1, 0.05, 0.15, 0.95, 0.95)}[f]]
    if short.endswith("_sign") or short.endswith("_hanging_sign"):
        return [(0.42, 0, 0.42, 0.58, 0.6, 0.58), (0.05, 0.5, 0.42, 0.95, 1, 0.58)]
    return [(0, 0, 0, 1, 1, 1)]


def _is_full_opaque(block: str) -> bool:
    if block == AIR or is_transparent(block):
        return False
    boxes = _shape_boxes(block)
    return len(boxes) == 1 and boxes[0] == (0, 0, 0, 1, 1, 1)


@lru_cache(maxsize=16384)
def _sprite(block: str, tw: int, shadow: bool = False) -> Image.Image:
    th = tw // 2
    bh = tw // 2
    color = block_color(block)
    if shadow and not is_emissive(block):
        color = tuple(int(c * 0.74) for c in color)
    emis = is_emissive(block)
    trans = is_transparent(block)
    alpha = 120 if trans else 255
    img = Image.new("RGBA", (tw, th + bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    def P(px, py, pz):
        return (tw / 2 + (px - pz) * tw / 2, (px + pz) * th / 2 + (1 - py) * bh)

    def shade(k):
        if emis:
            k = 0.9 + 0.1 * k
        return tuple(min(255, int(c * k)) for c in color) + (alpha,)

    def edge(k):
        return tuple(max(0, int(c * k * 0.72)) for c in color) + (alpha,)

    for (x0, y0, z0, x1, y1, z1) in _shape_boxes(block):
        top = [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)]
        right = [P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1), P(x1, y0, z0)]
        left = [P(x0, y1, z1), P(x1, y1, z1), P(x1, y0, z1), P(x0, y0, z1)]
        d.polygon(right, fill=shade(LIGHT_RIGHT), outline=edge(LIGHT_RIGHT) if tw >= 12 else None)
        d.polygon(left, fill=shade(LIGHT_LEFT), outline=edge(LIGHT_LEFT) if tw >= 12 else None)
        d.polygon(top, fill=shade(LIGHT_TOP), outline=edge(LIGHT_TOP) if tw >= 12 else None)
    return img


def render_iso(s: Schematic, rot: int = 0, tw: int = 16, bg: bool = True, crop: bool = True) -> Image.Image:
    """Render one isometric view. rot in 0..3 rotates the build clockwise by rot*90 degrees first."""
    if rot % 4:
        s = s.rotated(rot)
    W, H, L = s.w, s.h, s.l
    th = tw // 2
    bh = tw // 2
    img_w = (W + L) * (tw // 2) + tw
    img_h = (W + L) * (th // 2) + (H + 2) * bh + th
    ox = L * (tw // 2)
    oy = (H + 1) * bh
    if bg:
        img = _gradient(img_w, img_h)
    else:
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    # opaque mask with padding for hidden-block test
    ids = s.data
    opaque_lut = np.array([_is_full_opaque(b) for b in s.blocks_by_id], dtype=bool)
    op = opaque_lut[ids]
    pad = np.zeros((W + 1, H + 1, L + 1), dtype=bool)
    pad[:W, :H, :L] = op
    hidden = pad[1:, :H, :L] & pad[:W, 1:, :L] & pad[:W, :H, 1:]
    xs, ys, zs = np.nonzero((ids != 0) & ~hidden)
    order = np.argsort(xs + ys + zs, kind="stable")
    # drop shadow: a block with something within 8 blocks straight above it is drawn darker
    nz = ids != 0
    above = np.zeros_like(nz)
    for dy in range(1, min(9, H)):
        above[:, :H - dy, :] |= nz[:, dy:, :]
    sprites = {}
    names = s.blocks_by_id
    for i in order:
        x, y, z = int(xs[i]), int(ys[i]), int(zs[i])
        pid = int(ids[x, y, z])
        sh_ = bool(above[x, y, z])
        spr = sprites.get((pid, sh_))
        if spr is None:
            spr = sprites[(pid, sh_)] = _sprite(names[pid], tw, sh_)
        left = ox + (x - z) * (tw // 2) - tw // 2
        top = oy + (x + z) * (th // 2) - (y + 1) * bh
        img.alpha_composite(spr, (left, top))
    if crop:
        bbox = _content_bbox(img, img_w, img_h)
        if bbox:
            img = img.crop(bbox)
    return img


def _content_bbox(img, w, h, margin=12):
    # Bounding box of drawn content: approximate from alpha of a no-bg render is expensive; use full image.
    return None


def _gradient(w: int, h: int) -> Image.Image:
    top = np.array(BG_TOP, dtype=float)
    bot = np.array(BG_BOTTOM, dtype=float)
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (top[None, None, :] * (1 - t) + bot[None, None, :] * t).astype(np.uint8)
    arr = np.repeat(arr, w, axis=1)
    rgba = np.concatenate([arr, np.full((h, w, 1), 255, dtype=np.uint8)], axis=2)
    return Image.fromarray(rgba, "RGBA")


def render_plan(s: Schematic, scale: int = 6) -> Image.Image:
    """Top-down view: colour of the highest block in each column, shaded by height."""
    W, H, L = s.w, s.h, s.l
    arr = np.zeros((L, W, 3), dtype=np.uint8)
    arr[:] = (200, 190, 205)
    ids = s.data
    nonzero = ids != 0
    heights = np.where(nonzero.any(axis=1), (nonzero * np.arange(H)[None, :, None]).max(axis=1), -1)
    lut = np.array([block_color(b) for b in s.blocks_by_id], dtype=float)
    for x in range(W):
        for z in range(L):
            hgt = heights[x, z]
            if hgt < 0:
                continue
            c = lut[ids[x, hgt, z]]
            k = 0.55 + 0.45 * (hgt + 1) / max(H, 1)
            arr[z, x] = np.clip(c * k, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").resize((W * scale, L * scale), Image.NEAREST)
    return img


def _label(img: Image.Image, text: str) -> Image.Image:
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    d.rectangle([4, 4, 12 + len(text) * 9, 26], fill=(20, 20, 30, 200))
    d.text((8, 6), text, fill=(255, 255, 255), font=font)
    return img


def render_views(s: Schematic, out_prefix: str, tw: int = 16, max_px: int = 2600) -> List[str]:
    """Write <prefix>_iso.png (2x2 grid of the 4 rotations) and <prefix>_plan.png. Returns the paths."""
    os.makedirs(os.path.dirname(os.path.abspath(out_prefix)) or ".", exist_ok=True)
    # pick a tile size so each view is roughly 900-1300 px wide (detail for small builds, sanity for big ones)
    tw = max(8, min(32, int(2200 / (s.w + s.l)) // 2 * 2))
    est = (s.w + s.l) * (tw // 2) + tw
    while est > max_px and tw > 6:
        tw -= 2
        est = (s.w + s.l) * (tw // 2) + tw
    views = []
    for r in range(4):
        im = render_iso(s, rot=r, tw=tw)
        corner = ["SE: east face right, south face left", "NE: north face right, east face left",
                  "NW: west face right, north face left", "SW: south face right, west face left"][r]
        views.append(_label(im, f"rot {r} - camera {corner}"))
    w = max(v.width for v in views)
    h = max(v.height for v in views)
    grid = Image.new("RGBA", (w * 2, h * 2), BG_BOTTOM + (255,))
    for i, v in enumerate(views):
        grid.paste(v, ((i % 2) * w, (i // 2) * h))
    iso_path = out_prefix + "_iso.png"
    grid.convert("RGB").save(iso_path, optimize=True)
    plan = render_plan(s, scale=max(2, min(8, 1200 // max(s.w, s.l))))
    plan_path = out_prefix + "_plan.png"
    _label(plan.convert("RGBA"), "plan view (north = up, east = right)").convert("RGB").save(plan_path, optimize=True)
    return [iso_path, plan_path]


def render_single(s: Schematic, out_path: str, rot: int = 0, tw: int = 24) -> str:
    """One large detailed view (for close inspection)."""
    im = render_iso(s, rot=rot, tw=tw)
    im.convert("RGB").save(out_path, optimize=True)
    return out_path

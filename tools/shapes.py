"""
Geometry primitives and detailing helpers. All functions take a Schematic `s` first.
Coordinates are ints; ranges are inclusive on both ends.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .schem import Schematic, AIR
from . import states as st

Vec = Tuple[int, int, int]


# ------------------------------------------------------------------------- basic solids
def box(s: Schematic, x1, y1, z1, x2, y2, z2, block: str) -> None:
    """Filled axis-aligned box (inclusive)."""
    x1, x2 = sorted((int(x1), int(x2)))
    y1, y2 = sorted((int(y1), int(y2)))
    z1, z2 = sorted((int(z1), int(z2)))
    x1, y1, z1 = max(0, x1), max(0, y1), max(0, z1)
    x2, y2, z2 = min(s.w - 1, x2), min(s.h - 1, y2), min(s.l - 1, z2)
    if x1 > x2 or y1 > y2 or z1 > z2:
        return
    s.data[x1:x2 + 1, y1:y2 + 1, z1:z2 + 1] = s.pid(block)


def box_if_air(s: Schematic, x1, y1, z1, x2, y2, z2, block: str) -> None:
    x1, x2 = sorted((int(x1), int(x2)))
    y1, y2 = sorted((int(y1), int(y2)))
    z1, z2 = sorted((int(z1), int(z2)))
    x1, y1, z1 = max(0, x1), max(0, y1), max(0, z1)
    x2, y2, z2 = min(s.w - 1, x2), min(s.h - 1, y2), min(s.l - 1, z2)
    if x1 > x2 or y1 > y2 or z1 > z2:
        return
    sub = s.data[x1:x2 + 1, y1:y2 + 1, z1:z2 + 1]
    sub[sub == 0] = s.pid(block)


def hollow_box(s: Schematic, x1, y1, z1, x2, y2, z2, block: str, thickness: int = 1, floor=True, ceiling=True) -> None:
    """Shell of a box (walls, optional floor/ceiling); interior left untouched."""
    t = thickness
    x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
    box(s, x1, y1, z1, x1 + t - 1, y2, z2, block)
    box(s, x2 - t + 1, y1, z1, x2, y2, z2, block)
    box(s, x1, y1, z1, x2, y2, z1 + t - 1, block)
    box(s, x1, y1, z2 - t + 1, x2, y2, z2, block)
    if floor:
        box(s, x1, y1, z1, x2, y1 + t - 1, z2, block)
    if ceiling:
        box(s, x1, y2 - t + 1, z1, x2, y2, z2, block)


def room(s: Schematic, x1, y1, z1, x2, y2, z2, wall: str, floor: str, ceiling: str, interior: str = AIR) -> None:
    """Box with distinct wall / floor / ceiling blocks and a cleared interior."""
    box(s, x1, y1, z1, x2, y2, z2, wall)
    box(s, x1, y1, z1, x2, y1, z2, floor)
    box(s, x1, y2, z1, x2, y2, z2, ceiling)
    box(s, x1 + 1, y1 + 1, z1 + 1, x2 - 1, y2 - 1, z2 - 1, interior)


def _mask_ellipsoid(s: Schematic, cx, cy, cz, rx, ry, rz) -> np.ndarray:
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    rx, ry, rz = max(rx, 0.01), max(ry, 0.01), max(rz, 0.01)
    return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 + ((zs - cz) / rz) ** 2 <= 1.0


def ellipsoid(s: Schematic, cx, cy, cz, rx, ry, rz, block: str, hollow: bool = False, thickness: float = 1.0,
              only_air: bool = False) -> None:
    m = _mask_ellipsoid(s, cx, cy, cz, rx + 0.5, ry + 0.5, rz + 0.5)
    if hollow:
        inner = _mask_ellipsoid(s, cx, cy, cz, rx + 0.5 - thickness, ry + 0.5 - thickness, rz + 0.5 - thickness)
        m &= ~inner
    if only_air:
        m &= (s.data == 0)
    s.data[m] = s.pid(block)


def sphere(s: Schematic, cx, cy, cz, r, block: str, hollow: bool = False, thickness: float = 1.0, only_air=False) -> None:
    ellipsoid(s, cx, cy, cz, r, r, r, block, hollow, thickness, only_air)


def dome(s: Schematic, cx, cy, cz, r, block: str, hollow: bool = True, thickness: float = 1.0, ry: Optional[float] = None) -> None:
    """Upper half of an ellipsoid (base at y=cy)."""
    ry = r if ry is None else ry
    m = _mask_ellipsoid(s, cx, cy, cz, r + 0.5, ry + 0.5, r + 0.5)
    if hollow:
        m &= ~_mask_ellipsoid(s, cx, cy, cz, r + 0.5 - thickness, ry + 0.5 - thickness, r + 0.5 - thickness)
    ys = np.arange(s.h)[None, :, None]
    m &= (ys >= cy)
    s.data[m] = s.pid(block)


def cylinder(s: Schematic, cx, cy, cz, r, length, block: str, axis: str = "y", hollow: bool = False,
             thickness: float = 1.0, r2: Optional[float] = None, only_air=False) -> None:
    """Cylinder / cone-frustum along `axis` starting at (cx,cy,cz) and extending `length` blocks in the +axis
    direction (length may be negative). r2 = radius at the far end (None = same as r)."""
    r2 = r if r2 is None else r2
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    if axis == "y":
        a, u, v, a0 = ys, xs - cx, zs - cz, cy
    elif axis == "x":
        a, u, v, a0 = xs, ys - cy, zs - cz, cx
    else:
        a, u, v, a0 = zs, xs - cx, ys - cy, cz
    if length >= 0:
        t = (a - a0) / max(length, 1)
        along = (a >= a0) & (a <= a0 + length)
    else:
        t = (a0 - a) / max(-length, 1)
        along = (a <= a0) & (a >= a0 + length)
    rr = r + (r2 - r) * np.clip(t, 0, 1) + 0.5
    d2 = u ** 2 + v ** 2
    m = along & (d2 <= rr ** 2)
    if hollow:
        ri = np.maximum(rr - thickness, 0)
        m &= ~(d2 <= ri ** 2)
    if only_air:
        m &= (s.data == 0)
    s.data[m] = s.pid(block)


def elliptic_cylinder(s: Schematic, cx, cy, cz, rx, rz, length, block: str, axis: str = "y", hollow=False,
                      thickness=1.0, only_air=False) -> None:
    """Elliptic cylinder along axis; (rx, rz) are the two radii perpendicular to the axis (for axis='x' they are
    interpreted as (ry, rz); for axis='z' as (rx, ry))."""
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    if axis == "y":
        a, u, v, a0 = ys, (xs - cx) / (rx + 0.5), (zs - cz) / (rz + 0.5), cy
        ui, vi = (xs - cx) / max(rx + 0.5 - thickness, 0.01), (zs - cz) / max(rz + 0.5 - thickness, 0.01)
    elif axis == "x":
        a, u, v, a0 = xs, (ys - cy) / (rx + 0.5), (zs - cz) / (rz + 0.5), cx
        ui, vi = (ys - cy) / max(rx + 0.5 - thickness, 0.01), (zs - cz) / max(rz + 0.5 - thickness, 0.01)
    else:
        a, u, v, a0 = zs, (xs - cx) / (rx + 0.5), (ys - cy) / (rz + 0.5), cz
        ui, vi = (xs - cx) / max(rx + 0.5 - thickness, 0.01), (ys - cy) / max(rz + 0.5 - thickness, 0.01)
    lo, hi = (a0, a0 + length) if length >= 0 else (a0 + length, a0)
    m = (a >= lo) & (a <= hi) & (u ** 2 + v ** 2 <= 1)
    if hollow:
        m &= ~(ui ** 2 + vi ** 2 <= 1)
    if only_air:
        m &= (s.data == 0)
    s.data[m] = s.pid(block)


def loft(s: Schematic, sections: Sequence[Tuple[float, float, float, float, float]], block: str, axis: str = "x",
         hollow: bool = False, thickness: float = 1.0, only_air: bool = False, fill_mask: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    """Lofted hull: linear interpolation of elliptical cross sections along an axis.

    sections: list of (a, c1, c2, r1, r2): position along axis, centre in the two other axes, and the two radii.
      axis='x': (x, cy, cz, ry, rz)   axis='z': (z, cx, cy, rx, ry)   axis='y': (y, cx, cz, rx, rz)
    Sections must be sorted by `a`. Returns the boolean mask of the filled solid (useful to carve interiors).
    Great for ship hulls, pods, tanks: a few sections give a smooth organic shape.
    """
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    if axis == "x":
        a, u, v = xs, ys, zs
    elif axis == "z":
        a, u, v = zs, xs, ys
    else:
        a, u, v = ys, xs, zs
    sec = np.array(sections, dtype=float)
    A = sec[:, 0]
    a_f = a.astype(float)
    c1 = np.interp(a_f, A, sec[:, 1])
    c2 = np.interp(a_f, A, sec[:, 2])
    r1 = np.interp(a_f, A, sec[:, 3]) + 0.5
    r2 = np.interp(a_f, A, sec[:, 4]) + 0.5
    inside_range = (a_f >= A[0]) & (a_f <= A[-1])
    m = inside_range & (((u - c1) / np.maximum(r1, 0.01)) ** 2 + ((v - c2) / np.maximum(r2, 0.01)) ** 2 <= 1)
    if hollow:
        r1i, r2i = np.maximum(r1 - thickness, 0.01), np.maximum(r2 - thickness, 0.01)
        inner = inside_range & (((u - c1) / r1i) ** 2 + ((v - c2) / r2i) ** 2 <= 1) & (r1 - thickness > 0) & (r2 - thickness > 0)
        m &= ~inner
    if fill_mask is not None:
        m &= fill_mask
    if only_air:
        m &= (s.data == 0)
    s.data[m] = s.pid(block)
    return m


def loft_mask(s: Schematic, sections, axis: str = "x", shrink: float = 0.0) -> np.ndarray:
    """Solid mask of a loft without drawing (shrink reduces all radii)."""
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    a, u, v = (xs, ys, zs) if axis == "x" else ((zs, xs, ys) if axis == "z" else (ys, xs, zs))
    sec = np.array(sections, dtype=float)
    A = sec[:, 0]
    a_f = a.astype(float)
    c1 = np.interp(a_f, A, sec[:, 1]); c2 = np.interp(a_f, A, sec[:, 2])
    r1 = np.maximum(np.interp(a_f, A, sec[:, 3]) + 0.5 - shrink, 0.01)
    r2 = np.maximum(np.interp(a_f, A, sec[:, 4]) + 0.5 - shrink, 0.01)
    return (a_f >= A[0]) & (a_f <= A[-1]) & (((u - c1) / r1) ** 2 + ((v - c2) / r2) ** 2 <= 1)


def fill_mask(s: Schematic, mask: np.ndarray, block: str, only_air: bool = False) -> None:
    if only_air:
        mask = mask & (s.data == 0)
    s.data[mask] = s.pid(block)


def torus(s: Schematic, cx, cy, cz, R, r, block: str, axis: str = "y") -> None:
    xs = np.arange(s.w)[:, None, None]; ys = np.arange(s.h)[None, :, None]; zs = np.arange(s.l)[None, None, :]
    if axis == "y":
        q = np.sqrt((xs - cx) ** 2 + (zs - cz) ** 2) - R
        m = q ** 2 + (ys - cy) ** 2 <= (r + 0.5) ** 2
    elif axis == "x":
        q = np.sqrt((ys - cy) ** 2 + (zs - cz) ** 2) - R
        m = q ** 2 + (xs - cx) ** 2 <= (r + 0.5) ** 2
    else:
        q = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) - R
        m = q ** 2 + (zs - cz) ** 2 <= (r + 0.5) ** 2
    s.data[m] = s.pid(block)


def line(s: Schematic, p1: Vec, p2: Vec, block: str, radius: float = 0.0) -> None:
    """3D line (Bresenham-like, via sampling) with optional thickness."""
    x1, y1, z1 = p1; x2, y2, z2 = p2
    n = max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1), 1)
    for i in range(n + 1):
        t = i / n
        x, y, z = round(x1 + (x2 - x1) * t), round(y1 + (y2 - y1) * t), round(z1 + (z2 - z1) * t)
        if radius <= 0:
            s.set(x, y, z, block)
        else:
            sphere(s, x, y, z, radius, block)


def polygon_prism(s: Schematic, pts: Sequence[Tuple[float, float]], y1: int, y2: int, block: str, hollow=False) -> None:
    """Extrude a polygon (list of (x,z)) between y1..y2. Uses even-odd fill."""
    xs = np.arange(s.w)[:, None] + 0.5
    zs = np.arange(s.l)[None, :] + 0.5
    inside = np.zeros((s.w, s.l), dtype=bool)
    n = len(pts)
    for i in range(n):
        (xa, za), (xb, zb) = pts[i], pts[(i + 1) % n]
        cond = ((za > zs) != (zb > zs)) & (xs < (xb - xa) * (zs - za) / ((zb - za) if zb != za else 1e-9) + xa)
        inside ^= cond
    if hollow:
        er = inside.copy()
        er[1:-1, 1:-1] = inside[1:-1, 1:-1] & inside[:-2, 1:-1] & inside[2:, 1:-1] & inside[1:-1, :-2] & inside[1:-1, 2:]
        inside &= ~er
    pid = s.pid(block)
    for y in range(max(0, y1), min(s.h - 1, y2) + 1):
        s.data[:, y, :][inside] = pid


# ------------------------------------------------------------------------- detailing
def ring(s: Schematic, cx, cy, cz, r, block: str, axis: str = "y", thickness: float = 1.0) -> None:
    """One-block-tall hollow circle (frame / hoop)."""
    cylinder(s, cx, cy, cz, r, 0, block, axis=axis, hollow=True, thickness=thickness)


def outline_top(s: Schematic, x1, y, z1, x2, z2, block: str) -> None:
    """Rectangle outline at height y."""
    box(s, x1, y, z1, x2, y, z1, block); box(s, x1, y, z2, x2, y, z2, block)
    box(s, x1, y, z1, x1, y, z2, block); box(s, x2, y, z1, x2, y, z2, block)


def pillars(s: Schematic, positions: Iterable[Tuple[int, int]], y1: int, y2: int, block: str) -> None:
    for (x, z) in positions:
        box(s, x, y1, z, x, y2, z, block)


def stair_ramp(s: Schematic, x, y, z, length: int, dir: str, material: str, width: int = 1) -> None:
    """Straight staircase going up in direction `dir` ('north','south','east','west') starting at (x,y,z)."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[dir]
    for i in range(length):
        for w_ in range(width):
            ox, oz = (w_, 0) if dz else (0, w_)
            s.set(x + dx * i + ox, y + i, z + dz * i + oz, st.stairs(material, dir))


def roof_gable(s: Schematic, x1, y, z1, x2, z2, material: str, along: str = "x", overhang: int = 1, cap: Optional[str] = None) -> None:
    """Simple gable roof of stairs over rect (x1..x2, z1..z2). `along` = ridge direction."""
    x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
    if along == "x":
        z1o, z2o = z1 - overhang, z2 + overhang
        depth = (z2o - z1o + 1) // 2
        for i in range(depth):
            zl, zr = z1o + i, z2o - i
            if zl > zr:
                break
            if zl == zr:
                box(s, x1 - overhang, y + i, zl, x2 + overhang, y + i, zl, cap or st.slab(material))
            else:
                box(s, x1 - overhang, y + i, zl, x2 + overhang, y + i, zl, st.stairs(material, "south"))
                box(s, x1 - overhang, y + i, zr, x2 + overhang, y + i, zr, st.stairs(material, "north"))
                if zl + 1 < zr and i > 0:
                    box(s, x1 - overhang, y + i - 1, zl + 1, x2 + overhang, y + i - 1, zr - 1, (material + "_planks") if not material.endswith("planks") and "_" not in material else material)
    else:
        x1o, x2o = x1 - overhang, x2 + overhang
        depth = (x2o - x1o + 1) // 2
        for i in range(depth):
            xl, xr = x1o + i, x2o - i
            if xl > xr:
                break
            if xl == xr:
                box(s, xl, y + i, z1 - overhang, xl, y + i, z2 + overhang, cap or st.slab(material))
            else:
                box(s, xl, y + i, z1 - overhang, xl, y + i, z2 + overhang, st.stairs(material, "east"))
                box(s, xr, y + i, z1 - overhang, xr, y + i, z2 + overhang, st.stairs(material, "west"))


# ------------------------------------------------------------------------- environment / weathering
def value_noise2(x: float, z: float, seed: int = 0, scale: float = 8.0) -> float:
    """Cheap deterministic 2D value noise in [0,1)."""
    def h(i, j):
        n = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0
    fx, fz = x / scale, z / scale
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a = h(ix, iz) * (1 - tx) + h(ix + 1, iz) * tx
    b = h(ix, iz + 1) * (1 - tx) + h(ix + 1, iz + 1) * tx
    return a * (1 - tz) + b * tz


def snow_cover(s: Schematic, x1=0, z1=0, x2=None, z2=None, y_min: int = 0, prob: float = 1.0, seed: int = 1,
               layers: Tuple[int, int] = (1, 3), skip: Iterable[str] = ()) -> None:
    """Add snow layers on exposed top faces of full blocks (weathering). Snow sits only on top of
    non-air blocks whose block above is air. Blocks in `skip` (substring match) are not covered."""
    rng = random.Random(seed)
    x2 = s.w - 1 if x2 is None else x2
    z2 = s.l - 1 if z2 is None else z2
    skip = tuple(skip)
    non_solid = ("slab", "stairs", "glass_pane", "fence", "wall", "trapdoor", "door", "lantern", "torch", "rod",
                 "chain", "bars", "snow", "campfire", "carpet", "button", "lever", "rail", "sign", "banner", "candle",
                 "pointed", "cluster", "bud", "scaffolding", "ladder", "flower", "grass", "fern", "bush", "sapling",
                 "petals", "lichen", "vine", "pickle", "dripleaf", "amethyst_cluster", "web", "pressure_plate",
                 "sculk_vein", "water", "lava", "fire", "powder_snow", "cake", "head", "skull", "pot", "bell", "hopper",
                 "cauldron", "anvil", "lightning", "end_rod", "iron_bars", "chest", "barrel", "lectern", "stand",
                 "composter", "brewing", "grindstone", "stonecutter", "daylight", "conduit", "beacon", "cobweb")
    for x in range(max(0, x1), min(s.w, x2 + 1)):
        for z in range(max(0, z1), min(s.l, z2 + 1)):
            ty = s.top_y(x, z)
            if ty < y_min or ty + 1 >= s.h:
                continue
            b = s.get(x, ty, z)
            if any(k in b for k in non_solid) or any(k in b for k in skip):
                continue
            if b.endswith("_slab]") or "type=top" in b:
                continue
            if rng.random() < prob * (0.5 + value_noise2(x, z, seed, 6.0)):
                n = layers[0] + int((layers[1] - layers[0] + 0.999) * value_noise2(x + 100, z + 100, seed + 7, 5.0))
                s.set(x, ty + 1, z, st.snow_layer(max(1, min(8, n))))


def erode(s: Schematic, x1, y1, z1, x2, y2, z2, prob: float = 0.3, seed: int = 2, replace: str = AIR,
          only: Optional[Iterable[str]] = None, noise_scale: float = 4.0) -> None:
    """Randomly remove (or replace) blocks in a region: damage, decay, rubble. Uses noise so damage clusters."""
    rng = random.Random(seed)
    only = tuple(only) if only else None
    for x in range(max(0, x1), min(s.w, x2 + 1)):
        for y in range(max(0, y1), min(s.h, y2 + 1)):
            for z in range(max(0, z1), min(s.l, z2 + 1)):
                if s.data[x, y, z] == 0:
                    continue
                if only and not any(k in s.get(x, y, z) for k in only):
                    continue
                n = value_noise2(x * 0.7 + y * 0.3, z * 0.7 + y * 0.5, seed, noise_scale)
                if rng.random() < prob * n * 1.6:
                    s.set(x, y, z, replace)


def scatter(s: Schematic, x1, z1, x2, z2, blocks: Sequence[str], count: int, seed: int = 3, y_offset: int = 1,
            on: Optional[Iterable[str]] = None) -> None:
    """Scatter `count` blocks on top of the terrain/structure in a region (debris, rocks, crates)."""
    rng = random.Random(seed)
    on = tuple(on) if on else None
    tries = 0
    placed = 0
    while placed < count and tries < count * 30:
        tries += 1
        x, z = rng.randint(x1, x2), rng.randint(z1, z2)
        ty = s.top_y(x, z)
        if ty < 0:
            continue
        base = s.get(x, ty, z)
        if on and not any(k in base for k in on):
            continue
        if "snow[" in base:  # sit on the block under a snow layer
            s.set(x, ty, z, AIR)
            ty -= 1
        s.set(x, ty + y_offset, z, rng.choice(blocks))
        placed += 1


def ground_disc(s: Schematic, cx, cz, r, y: int, block: str, rim_block: Optional[str] = None, seed: int = 4,
                noise: float = 0.35, depth: int = 1) -> None:
    """Noisy disc of ground material (crater floor, scorched earth, trampled snow) from y-depth+1 .. y."""
    for x in range(s.w):
        for z in range(s.l):
            d = math.hypot(x - cx, z - cz)
            rr = r * (1 - noise + 2 * noise * value_noise2(x, z, seed, 5.0))
            if d <= rr:
                box(s, x, y - depth + 1, z, x, y, z, block)
            elif rim_block and d <= rr + 1.5:
                box(s, x, y - depth + 1, z, x, y, z, rim_block)


def crater(s: Schematic, cx, cz, r, ground_y: int, floor: str, rim: str, ejecta: str, depth: int = 2,
           rim_height: int = 2, seed: int = 5) -> None:
    """Impact crater: bowl carved to `depth` under ground_y, raised rim, ejecta ring. ground_y = surface block y.
    The schematic must contain a ground slab up to ground_y (use ground_slab first)."""
    for x in range(s.w):
        for z in range(s.l):
            n = value_noise2(x, z, seed, 6.0)
            d = math.hypot(x - cx, z - cz) / (r * (0.85 + 0.3 * n))
            if d <= 1.0:
                dep = int(round(depth * (1 - d * d)))
                for y in range(ground_y - dep + 1, ground_y + 1):
                    s.set(x, y, z, AIR)
                s.set(x, ground_y - dep, z, floor)
            elif d <= 1.35:
                h = int(round(rim_height * (1.35 - d) / 0.35 * (0.6 + 0.6 * n)))
                for y in range(ground_y + 1, ground_y + 1 + h):
                    s.set(x, y, z, rim)
            elif d <= 1.9 and n > 0.72:
                s.set(x, ground_y + 1, z, ejecta)


def ground_slab(s: Schematic, y_top: int, block: str = "minecraft:snow_block", depth: int = 3,
                x1=0, z1=0, x2=None, z2=None) -> None:
    """Fill a flat ground slab from y_top-depth+1 to y_top. Use it for crash sites so the crater
    (dark scorched floor) gets pasted into the terrain."""
    x2 = s.w - 1 if x2 is None else x2
    z2 = s.l - 1 if z2 is None else z2
    box(s, x1, max(0, y_top - depth + 1), z1, x2, y_top, z2, block)


def clear_above(s: Schematic, y: int) -> None:
    s.data[:, y:, :] = 0


# ------------------------------------------------------------------------- connections
_D4 = (("north", 0, -1), ("south", 0, 1), ("west", -1, 0), ("east", 1, 0))


def _connects_to(target: str, self_kind: str) -> bool:
    """Whether a fence/pane/wall/bars of kind `self_kind` visually connects to block `target`."""
    if target == AIR:
        return False
    name = target.split("[")[0]
    short = name.split(":")[1]
    thin = any(k in short for k in ("_fence", "glass_pane", "iron_bars", "_wall")) and not short.endswith("_fence_gate") and "wall_sign" not in short and "wall_banner" not in short and "wall_torch" not in short and "wall_hanging" not in short
    if short.endswith("_fence_gate"):
        return self_kind in ("fence", "wall")
    if thin:
        if self_kind == "fence":
            return "_fence" in short and "nether_brick" not in short  # wooden fences don't connect to nether brick
        if self_kind == "pane":
            return "glass_pane" in short or "iron_bars" in short or short.endswith("_wall")
        if self_kind == "wall":
            return short.endswith("_wall") or "glass_pane" in short or "iron_bars" in short
    non_full = ("slab", "stairs", "door", "lantern", "torch", "rod", "chain", "snow", "campfire", "carpet", "button",
                "lever", "rail", "sign", "banner", "candle", "pointed", "cluster", "bud", "scaffolding", "ladder",
                "flower", "grass", "fern", "bush", "sapling", "petals", "lichen", "vine", "leaves", "glass", "ice",
                "cake", "head", "skull", "pot", "bell", "hopper", "cauldron", "anvil", "lightning", "chest", "barrel",
                "lectern", "stand", "composter", "grindstone", "stonecutter", "daylight", "conduit", "beacon", "web",
                "trapdoor", "shulker", "bed", "dripleaf", "sea_pickle", "end_rod", "bars", "water", "lava", "fire",
                "powder_snow", "bamboo", "cactus", "structure_void", "barrier", "sculk_vein", "sculk_sensor", "pickle")
    if "stained_glass" in short and not short.endswith("_pane"):
        return self_kind == "pane"  # glass blocks connect to panes
    if short == "glass" or short == "tinted_glass":
        return self_kind == "pane"
    if any(k in short for k in non_full):
        return False
    return True  # full solid block


def autoconnect(s: Schematic) -> None:
    """Set connection properties of fences, glass panes, iron bars and walls based on neighbours.
    Call once at the end of a build (before save). Pre-existing explicit connection props are overwritten."""
    for i, b in list(enumerate(s.blocks_by_id)):
        if i == 0:
            continue
        name = b.split("[")[0]
        short = name.split(":")[1]
        if short.endswith("_fence_gate") or "wall_sign" in short or "wall_banner" in short or "wall_torch" in short or "wall_hanging" in short:
            continue
        if short.endswith("_fence"):
            kind = "fence"
        elif "glass_pane" in short or short == "iron_bars":
            kind = "pane"
        elif short.endswith("_wall"):
            kind = "wall"
        else:
            continue
        xs, ys, zs = np.nonzero(s.data == i)
        for x, y, z in zip(xs, ys, zs):
            x, y, z = int(x), int(y), int(z)
            props = {}
            conn = []
            for d, dx, dz in _D4:
                c = _connects_to(s.get(x + dx, y, z + dz), kind)
                conn.append(c)
                if kind == "wall":
                    props[d] = "low" if c else "none"
                else:
                    props[d] = "true" if c else "false"
            if kind == "wall":
                above = s.get(x, y + 1, z)
                n, sth, w_, e = conn
                straight = (n and sth and not w_ and not e) or (w_ and e and not n and not sth)
                post = not straight or above != AIR
                if above != AIR and above.split("[")[0].split(":")[1].endswith("_wall"):
                    for d, dx, dz in _D4:
                        if props[d] == "low":
                            props[d] = "tall"
                props["up"] = "true" if post else "false"
            props["waterlogged"] = "false"
            s.data[x, y, z] = s.pid(st.unparse(name, props))


def stairs_shape_fix(s: Schematic) -> None:
    """Compute inner/outer corner shapes for stairs based on neighbouring stairs (vanilla logic)."""
    dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    left_of = {"north": "west", "west": "south", "south": "east", "east": "north"}
    right_of = {v: k for k, v in left_of.items()}
    stair_ids = [i for i, b in enumerate(s.blocks_by_id) if b.split("[")[0].endswith("_stairs")]
    if not stair_ids:
        return
    mask = np.isin(s.data, stair_ids)
    xs, ys, zs = np.nonzero(mask)
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        b = s.get(x, y, z)
        name, p = st.parse(b)
        f, half = p.get("facing", "north"), p.get("half", "bottom")
        shape = "straight"
        dx, dz = dirs[f]
        front = s.get(x + dx, y, z + dz)
        if front.split("[")[0].endswith("_stairs"):
            _, fp = st.parse(front)
            if fp.get("half", "bottom") == half and fp.get("facing") in (left_of[f], right_of[f]):
                shape = "outer_left" if fp["facing"] == left_of[f] else "outer_right"
        if shape == "straight":
            bx, bz = -dx, -dz
            back = s.get(x + bx, y, z + bz)
            if back.split("[")[0].endswith("_stairs"):
                _, bp = st.parse(back)
                if bp.get("half", "bottom") == half and bp.get("facing") in (left_of[f], right_of[f]):
                    shape = "inner_left" if bp["facing"] == left_of[f] else "inner_right"
        if shape != p.get("shape", "straight"):
            p["shape"] = shape
            s.data[x, y, z] = s.pid(st.unparse(name, p))


def finalize(s: Schematic) -> Schematic:
    """Standard post-processing: autoconnect thin blocks and fix stair corners."""
    autoconnect(s)
    stairs_shape_fix(s)
    return s


# ------------------------------------------------------------------------- texturing
def texturize(s: Schematic, target: str, choices: Sequence[Tuple[str, float]], seed: int = 11,
              region: Optional[Tuple[int, int, int, int, int, int]] = None) -> None:
    """Replace every `target` block with a weighted random pick from `choices` [(block, weight), ...].
    Gives large surfaces a subtle gradient/noise texture. Keep the variants close in colour!"""
    from .schem import norm_block
    t = norm_block(target)
    if t not in s.palette:
        return
    tid = s.palette[t]
    rng = np.random.default_rng(seed)
    blocks = [c[0] for c in choices]
    w = np.array([c[1] for c in choices], dtype=float)
    w /= w.sum()
    ids = np.array([s.pid(b) for b in blocks])
    mask = s.data == tid
    if region:
        x1, y1, z1, x2, y2, z2 = region
        rm = np.zeros_like(mask)
        rm[max(0, x1):x2 + 1, max(0, y1):y2 + 1, max(0, z1):z2 + 1] = True
        mask &= rm
    n = int(mask.sum())
    if n:
        s.data[mask] = ids[rng.choice(len(ids), size=n, p=w)]


def replace_in_region(s: Schematic, x1, y1, z1, x2, y2, z2, target: str, block: str) -> None:
    from .schem import norm_block
    t = norm_block(target)
    if t not in s.palette:
        return
    sub = s.data[max(0, x1):x2 + 1, max(0, y1):y2 + 1, max(0, z1):z2 + 1]
    sub[sub == s.palette[t]] = s.pid(block)


def surface_mask(s: Schematic, mask: np.ndarray) -> np.ndarray:
    """Cells of `mask` that touch a cell outside `mask` (6-neighbourhood) - i.e. the shell of a solid."""
    pad = np.zeros((s.w + 2, s.h + 2, s.l + 2), dtype=bool)
    pad[1:-1, 1:-1, 1:-1] = mask
    inner = (pad[:-2, 1:-1, 1:-1] & pad[2:, 1:-1, 1:-1] & pad[1:-1, :-2, 1:-1] & pad[1:-1, 2:, 1:-1]
             & pad[1:-1, 1:-1, :-2] & pad[1:-1, 1:-1, 2:])
    return mask & ~inner


def blocks_mask(s: Schematic, *blocks: str) -> np.ndarray:
    from .schem import norm_block
    ids = [s.palette[norm_block(b)] for b in blocks if norm_block(b) in s.palette]
    return np.isin(s.data, ids) if ids else np.zeros_like(s.data, dtype=bool)


def light_strip(s: Schematic, p1: Vec, p2: Vec, block: str = "minecraft:sea_lantern", every: int = 3) -> None:
    """Regularly spaced lights along a straight line (floor edge lighting, runway lights)."""
    x1, y1, z1 = p1; x2, y2, z2 = p2
    n = max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1), 1)
    for i in range(0, n + 1, every):
        t = i / n
        s.set(round(x1 + (x2 - x1) * t), round(y1 + (y2 - y1) * t), round(z1 + (z2 - z1) * t), block)


# ------------------------------------------------------------------------- rounded edges
def _facing_to_center(dx: float, dz: float) -> str:
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def ring_stairs(s: Schematic, cx: float, y: int, cz: float, r: float, material: str, half: str = "bottom",
                outward: bool = False, only_air: bool = True) -> None:
    """A ring of stairs (radius r, at height y) whose tall side faces the centre (bevel for cylinder tops /
    heat-shield rims / dome bases). outward=True flips them (tall side away from the centre)."""
    for x in range(s.w):
        for z in range(s.l):
            d = math.hypot(x + 0.5 - (cx + 0.5), z + 0.5 - (cz + 0.5))
            if r - 0.5 <= d <= r + 0.5:
                f = _facing_to_center(x - cx, z - cz)
                if outward:
                    f = {"north": "south", "south": "north", "east": "west", "west": "east"}[f]
                if only_air and not s.is_air(x, y, z):
                    continue
                s.set(x, y, z, st.stairs(material, f, half))


def ring_slabs(s: Schematic, cx: float, y: int, cz: float, r: float, material: str, type: str = "bottom", only_air=True) -> None:
    for x in range(s.w):
        for z in range(s.l):
            d = math.hypot(x + 0.5 - (cx + 0.5), z + 0.5 - (cz + 0.5))
            if r - 0.5 <= d <= r + 0.5:
                if only_air and not s.is_air(x, y, z):
                    continue
                s.set(x, y, z, st.slab(material, type))


def box_edge_stairs(s: Schematic, x1, y, z1, x2, z2, material: str, half: str = "top") -> None:
    """Stairs all around the outside of a rectangle at height y, tall side toward the box (bevels a roof edge
    with half='bottom' at the top, or an overhang underside with half='top')."""
    for x in range(x1, x2 + 1):
        s.set(x, y, z1 - 1, st.stairs(material, "south", half))
        s.set(x, y, z2 + 1, st.stairs(material, "north", half))
    for z in range(z1, z2 + 1):
        s.set(x1 - 1, y, z, st.stairs(material, "east", half))
        s.set(x2 + 1, y, z, st.stairs(material, "west", half))

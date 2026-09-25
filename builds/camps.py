"""Exploration camps: a 2-tent bivouac (camp_small) and the main expedition base (camp_base).
White fabric tents (white wool textured with close shades, quartz-stair slopes, a thin cherry hem, cyan seam ribs
flush with the slope), short stripped-spruce ridge logs, fence poles, warm lanterns + campfires against the cold.
ground=1 (surface at y=1). Nothing goes below the surface: the surface layer is one contiguous snow pad under the camp
(plus trodden-snow paths, tent floors and fire-pit stones) so nothing floats and `//paste -a` simply re-snows the
surface where the camp stands, inheriting the world's own hills all around."""
import math
import random
from collections import deque

import numpy as np

from tools.schem import Schematic, AIR
from tools import shapes as sh, states as st
from tools.palette import CAMP, GROUND

WOOL = CAMP["tent"]                # white_wool
WOOL_LG = CAMP["tent_alt"]         # light_gray_wool
CYAN = CAMP["tent_accent"]
ORANGE = CAMP["tent_orange"]
FENCE = CAMP["pole"]               # spruce_fence
LOG = "minecraft:stripped_spruce_log"
PLANK = CAMP["plank"]
CHERRY = CAMP["plank_light"]       # cherry_planks (world signature pink wood)
TRODDEN = CAMP["trodden_snow"]     # white_concrete_powder
TRODDEN_LG = "minecraft:light_gray_concrete_powder"
SNOW = GROUND["snow"]
BARREL = "minecraft:barrel[facing=up,open=false]"
DARK = "minecraft:polished_deepslate"          # the dark "structure" layer that outlines props on white snow
DARK_SLAB = "minecraft:polished_deepslate_slab[type=bottom]"
DARK_FENCE = "minecraft:dark_oak_fence"
DARK_LOG = "minecraft:dark_oak_log"
PATH_MIX = [(TRODDEN, 8), (TRODDEN_LG, 2)]     # two close shades only: a groove, not speckle
WOOL_MIX = [(WOOL, 7), ("minecraft:white_concrete", 2), ("minecraft:quartz_block", 1)]
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DXZ = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}


# ----------------------------------------------------------------------------------------------- helpers
def dir_along(along, sign):
    """Direction of +sign along the ridge axis."""
    if along == "x":
        return "east" if sign > 0 else "west"
    return "south" if sign > 0 else "north"


def dir_cross(along, sign):
    """Direction of +sign across the ridge (the v axis)."""
    if along == "x":
        return "south" if sign > 0 else "north"
    return "east" if sign > 0 else "west"


def ground_under(s, x, g, z):
    """Make sure a surface block exists under a prop (deliberate snow block at the surface level)."""
    if s.inside(x, g, z) and s.is_air(x, g, z):
        s.set(x, g, z, SNOW)


def snow_layer_if_air(s, x, y, z, n):
    """Snow layers on the ground (y == g+1). The surface block under it is filled later by ground_pad()."""
    if s.inside(x, y, z) and s.is_air(x, y, z):
        b = s.get(x, y - 1, z)
        if b == AIR or "snow_block" in b or "concrete_powder" in b:
            s.set(x, y, z, st.snow_layer(max(1, min(7, n))))


def snow_on_top(s, x, y, z, n):
    """Snow layer on top of a full block at y (only if the space above is free)."""
    if s.inside(x, y + 1, z) and s.is_air(x, y + 1, z) and not s.is_air(x, y, z):
        s.set(x, y + 1, z, st.snow_layer(n))


def ground_pad(s, g, seed=7):
    """One contiguous snow surface (y == g, the world's own surface level) under everything and 1-3 blocks
    around it with a noisy edge, so no prop floats and no lone snow cube lies on the ground. Nothing goes below
    g: with `//paste -a` this simply re-snows the surface where the camp stands."""
    occ = np.zeros((s.w, s.l), dtype=bool)
    for x in range(s.w):
        for z in range(s.l):
            occ[x, z] = bool((s.data[x, g:, z] != 0).any())
    dist = np.full((s.w, s.l), 99, dtype=int)
    q = deque()
    for x, z in zip(*np.nonzero(occ)):
        dist[x, z] = 0
        q.append((x, z))
    while q:
        x, z = q.popleft()
        if dist[x, z] >= 3:
            continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if 0 <= nx < s.w and 0 <= nz < s.l and dist[nx, nz] > dist[x, z] + 1:
                dist[nx, nz] = dist[x, z] + 1
                q.append((nx, nz))
    for x in range(s.w):
        for z in range(s.l):
            d = dist[x, z]
            n = sh.value_noise2(x, z, seed, 4.0)
            if d <= 1 or (d == 2 and n > 0.3) or (d == 3 and n > 0.6):
                if s.is_air(x, g, z):
                    s.set(x, g, z, SNOW)
    for _ in range(2):                                      # close 1-cell holes / notches in the pad
        for x in range(s.w):
            for z in range(s.l):
                if s.is_air(x, g, z):
                    n = sum(1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
                            if s.inside(x + dx, g, z + dz) and not s.is_air(x + dx, g, z + dz))
                    if n >= 3:
                        s.set(x, g, z, SNOW)


def path_edges(s, g, seed=8, prob=0.7):
    """Low snow layers (1-2) along both sides of every trodden strip so it reads as a groove in the snow."""
    rng = random.Random(seed)
    trod = {(x, z) for x in range(s.w) for z in range(s.l) if s.get(x, g, z) == TRODDEN}
    for x, z in trod:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if (nx, nz) in trod or not s.inside(nx, g + 1, nz):
                continue
            if s.get(nx, g, nz) in (AIR, SNOW) and s.is_air(nx, g + 1, nz) and rng.random() < prob:
                s.set(nx, g + 1, nz, st.snow_layer(rng.randint(1, 2)))


def hanging_sign(s, x, y, z, rotation, lines):
    """1.20 hanging sign under a beam (the toolkit's add_sign hardcodes the 'minecraft:sign' entity id)."""
    s.add_sign(x, y, z, "minecraft:spruce_hanging_sign[rotation=%d,attached=false]" % rotation, lines)
    s.block_entities[-1]["Id"] = "minecraft:hanging_sign"


def tent(s, u1, u2, c, g, hw, along="x", front="+", wall=0, body=WOOL, end=WOOL_LG, stair="quartz", hem="cherry",
         accent=CYAN, accent_stair="prismarine_brick", flap="cherry", floor=PLANK, bands=None, seed=1, lee=1,
         patch=True, window=True, glass_strip=False, awning_lanterns=1, banner=None):
    """A-frame (wall=0) or wall tent (wall=1). Ridge runs along `along` from u1..u2 at cross-centre c, half-width hw.
    front '+' = door at the u2 end. lee = +1/-1: side (sign of v) where the snow drifts pile up.
    Slope: quartz stairs on a wool mass, thin cherry slab hem at the skirt, cyan ribs = cyan wool body + prismarine
    brick stairs (flush with the slope), short stripped-log ridge with a 1-log + fence awning over the door.
    Returns a mapper P(u, v) -> (x, z), the door/back u coordinates, the door direction and the ridge y."""
    rng = random.Random(seed)

    def P(u, v):
        return (u, c + v) if along == "x" else (c + v, u)

    def facing_in(v):                       # stairs high side toward the ridge
        return dir_cross(along, -1 if v > 0 else 1)

    def h(v):                               # top block (stair / ridge) height above g
        return wall + hw + 1 - abs(v)

    ridge_y = g + h(0)
    d = 1 if front == "+" else -1
    u_f = u2 if front == "+" else u1
    u_b = u1 if front == "+" else u2
    band_us = set(bands) if bands is not None else {u1 + 2, u2 - 2}
    # ---- shell
    for u in range(u1, u2 + 1):
        rib = u in band_us
        for v in range(-hw, hw + 1):
            x, z = P(u, v)
            top = h(v)
            blk = end if u in (u1, u2) else (accent if rib else body)
            for dy in range(1, top):
                s.set(x, g + dy, z, blk)
            if v == 0:
                s.set(x, g + top, z, st.log(LOG, along))
            elif abs(v) == hw:
                s.set(x, g + top, z, st.slab(hem, "bottom"))                      # thin sewn hem
            elif u in (u1, u2):                                                    # bevelled gable (pink trim)
                s.set(x, g + top, z, st.stairs(hem, dir_along(along, 1 if u == u1 else -1)))
            else:
                s.set(x, g + top, z, st.stairs(accent_stair if rib else stair, facing_in(v)))
    # ---- interior + floor
    for u in range(u1 + 1, u2):
        for v in range(-hw, hw + 1):
            x, z = P(u, v)
            for dy in range(1, h(v) - 1):
                s.set(x, g + dy, z, AIR)
            if h(v) >= 3:
                s.set(x, g, z, floor)
    # ---- door opening (follows the interior triangle, |v| <= 1) + threshold + flaps
    for v in (-1, 0, 1):
        x, z = P(u_f, v)
        for dy in range(1, h(v) - 1):
            s.set(x, g + dy, z, AIR)
        s.set(x, g, z, floor if v == 0 else TRODDEN)
    for v in (-1, 1):                                                              # 2-high open door flaps
        x, z = P(u_f + d, v)
        for dy in (1, 2):
            s.set(x, g + dy, z, st.trapdoor(flap, facing_in(-v), "bottom", open=True))
    x, z = P(u_f - d, -1)                                                          # lantern just inside the door
    if s.is_air(x, g + 1, z):
        s.set(x, g + 1, z, st.lantern(hanging=False))
    # ---- awning: one more row of stairs, ridge log +1 then a fence tip on a fence pole
    for v in range(-(hw - 1), hw):
        if v == 0:
            continue
        x, z = P(u_f + d, v)
        s.set(x, g + h(v), z, st.stairs(stair, facing_in(v)))
    x, z = P(u_f + d, 0)
    s.set(x, ridge_y, z, st.log(LOG, along))
    if awning_lanterns == 1:
        s.set(x, ridge_y - 1, z, st.lantern(hanging=True))
    else:
        for v in (-2, 2):
            xl, zl = P(u_f + d, v)
            s.set(xl, g + h(v) - 1, zl, st.lantern(hanging=True))
    x, z = P(u_f + 2 * d, 0)
    for y in range(g + 1, ridge_y + 1):
        s.set(x, y, z, FENCE)
    s.set(x, g, z, TRODDEN)
    # icicles hanging under the awning stairs (2 per tent, never in the door line v=0)
    placed = 0
    for v in (-(hw - 1), hw - 2, -(hw - 2), hw - 1):
        x, z = P(u_f + d, v)
        y = g + h(v) - 1
        if v != 0 and y >= g + 2 and s.is_air(x, y, z) and placed < 2:
            s.set(x, y, z, st.pointed_dripstone("down", "tip"))
            placed += 1
    if banner:
        x, z = P(u_f + d, 0)
        s.set(x, ridge_y - 1, z, st.wall_banner(banner, dir_along(along, d)))
    # ---- gables: mesh window at the back, glass strip (big tents), a dark repair patch, snow on the sill
    if window:
        x, z = P(u_b, 0)
        s.set(x, g + 2, z, "minecraft:light_gray_stained_glass_pane")
    if glass_strip:
        for v in (-1, 0, 1):
            x, z = P(u_b, v)
            s.set(x, g + 3, z, "minecraft:light_gray_stained_glass_pane")
        x, z = P(u_b, 0)
        s.set(x, g + 4, z, "minecraft:light_gray_stained_glass_pane")
    if patch:
        v = rng.choice((-1, 1)) * (hw - 2 if hw > 2 else 1)
        x, z = P(u_b - d, v)
        s.set(x, g + 1 + rng.randint(0, 1), z, st.trapdoor("spruce", dir_along(along, -d), "bottom", open=True))
        # a second patch lying on the roof slope
        u = rng.choice([uu for uu in range(u1 + 1, u2) if uu not in band_us])
        v = rng.choice((-1, 1)) * max(1, hw - 2)
        x, z = P(u, v)
        s.set(x, g + h(v) + 1, z, st.trapdoor("spruce", facing_in(v), "bottom", open=False))
    # ---- guy pegs at the four corners (fence stub)
    for uu in (u1 - 1, u2 + 1):
        for vv in (-(hw + 1), hw + 1):
            x, z = P(uu, vv)
            if s.inside(x, g + 1, z) and s.is_air(x, g + 1, z):
                s.set(x, g + 1, z, FENCE)
    # ---- weathering: snow on the ridge (leeward bias), drifts piling against the skirt and the back
    for u in range(u1, u2 + 1):
        x, z = P(u, 0)
        if rng.random() < 0.45:
            s.set(x, ridge_y + 1, z, st.snow_layer(rng.randint(1, 2)))
    # drifts = snow layers only, tallest against the skirt and falling off with distance (leeward bias)
    for u in range(u1 - 1, u2 + 2):
        for sgn in (1, -1):
            if sgn == lee:
                specs = ((hw + 1, (4, 6), 0.95), (hw + 2, (2, 3), 0.8), (hw + 3, (1, 1), 0.45))
            else:
                specs = ((hw + 1, (1, 2), 0.7), (hw + 2, (1, 1), 0.2))
            for vv, n, p in specs:
                x, z = P(u, sgn * vv)
                if rng.random() < p:
                    snow_layer_if_air(s, x, g + 1, z, rng.randint(*n))
    for vv in range(-hw - 1, hw + 2):
        x, z = P(u_b - d, vv)
        if rng.random() < 0.9:
            snow_layer_if_air(s, x, g + 1, z, rng.randint(3, 5))
        x, z = P(u_b - 2 * d, vv)
        if rng.random() < 0.6:
            snow_layer_if_air(s, x, g + 1, z, rng.randint(1, 2))
    return P, u_f, u_b, d, ridge_y


def campfire_ring(s, cx, cz, g, seats=("n", "s", "e", "w")):
    """Campfire with stripped-log seats (axis perpendicular to the fire), trodden snow disc, fire-pit stones."""
    sh.ground_disc(s, cx, cz, 3.2, g, TRODDEN, seed=cx + cz, noise=0.3, depth=1)
    s.set(cx, g + 1, cz, st.campfire())
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set(cx + dx, g, cz + dz, "minecraft:polished_deepslate")     # fire pit stones set into the snow
    if "n" in seats:
        sh.box(s, cx - 1, g + 1, cz - 2, cx + 1, g + 1, cz - 2, st.log(LOG, "x"))
    if "s" in seats:
        sh.box(s, cx - 1, g + 1, cz + 2, cx + 1, g + 1, cz + 2, st.log(LOG, "x"))
    if "e" in seats:
        sh.box(s, cx + 2, g + 1, cz - 1, cx + 2, g + 1, cz + 1, st.log(LOG, "z"))
    if "w" in seats:
        sh.box(s, cx - 2, g + 1, cz - 1, cx - 2, g + 1, cz + 1, st.log(LOG, "z"))


def lantern_pole(s, x, z, g, height=3, soul=False):
    for y in range(g + 1, g + 1 + height):
        s.set(x, y, z, FENCE)
    s.set(x, g + 1 + height, z, st.lantern(soul=soul, hanging=False))


def lookout_post(s, x, z, g):
    """Bivouac lookout: a tall fence post with a lantern on top and a spyglass (end rod) on a bracket."""
    for y in range(g + 1, g + 5):
        s.set(x, y, z, FENCE)
    s.set(x, g + 5, z, st.lantern(hanging=False))
    s.set(x + 1, g + 4, z, st.end_rod("east"))
    s.set(x, g + 1, z + 1, st.snow_layer(3))                            # trampled step at the foot


def lookout_deck(s, lx, lz, g):
    """2x2 raised deck: 3 fence legs + 1 log leg with a ladder, cherry-plank deck, fence railing on 3 sides,
    end-rod spyglass, lantern, snow on the deck."""
    for y in range(g + 1, g + 4):
        s.set(lx, y, lz, st.log(LOG, "y"))
        s.set(lx + 1, y, lz, FENCE)
        s.set(lx, y, lz + 1, FENCE)
        s.set(lx + 1, y, lz + 1, FENCE)
    for y in range(g + 1, g + 5):
        s.set(lx - 1, y, lz, "minecraft:ladder[facing=west]")
    for dx in (0, 1):
        for dz in (0, 1):
            s.set(lx + dx, g + 4, lz + dz, CHERRY)
    for (dx, dz) in ((0, 1), (1, 0), (1, 1)):
        s.set(lx + dx, g + 5, lz + dz, FENCE)
    s.set(lx + 1, g + 6, lz + 1, st.end_rod("east"))
    s.set(lx, g + 5, lz, st.snow_layer(2))
    s.set(lx, g + 3, lz + 1, st.lantern(hanging=True))                  # lantern hung under the deck
    s.set(lx + 2, g + 1, lz + 1, BARREL)


def flag_pole(s, x, z, g, height, rotation=0, base=True):
    """Iron-bars mast with a cyan banner on top and a small stone foot."""
    for y in range(g + 1, g + 1 + height):
        s.set(x, y, z, CAMP["flag_pole"])
    s.set(x, g + 1 + height, z, st.banner("cyan", rotation))
    s.set(x, g + 1, z, "minecraft:polished_deepslate")   # foot
    s.set(x, g + 2, z, "minecraft:deepslate_tile_wall")
    if base:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s.set(x + dx, g + 1, z + dz, "minecraft:polished_deepslate_slab[type=bottom]")


def guy_line(s, x0, y0, z0, dx, dz, g, arm=2):
    """Guy line from the crossbar block at (x0,y0,z0): an end-rod arm `arm` long, one horizontal chain at its
    tip, then a single straight vertical chain column down to a fence peg at g+1 (everything face-connected)."""
    ax = "x" if dx else "z"
    f = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(dx, dz)]
    for i in range(1, arm + 1):
        s.set(x0 + dx * i, y0, z0 + dz * i, st.end_rod(f))
    x, z = x0 + dx * (arm + 1), z0 + dz * (arm + 1)
    s.set(x, y0, z, st.chain(ax))
    for y in range(g + 2, y0):
        s.set(x, y, z, st.chain("y"))
    s.set(x, g + 1, z, FENCE)


def path(s, pts, g, width=2, seed=5):
    """Continuous trodden-snow strip (width 1 or 2, no random speckle) through a polyline, at the surface."""
    cells = set()
    offs = ((0, 0), (1, 0), (0, 1), (1, 1)) if width >= 2 else ((0, 0),)
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1), 1)
        for i in range(n + 1):
            t = i / n
            px, pz = round(x1 + (x2 - x1) * t), round(z1 + (z2 - z1) * t)
            for dx, dz in offs:
                cells.add((px + dx, pz + dz))
    for x, z in cells:
        if s.inside(x, g, z) and s.get(x, g, z) in (AIR, SNOW):
            s.set(x, g, z, TRODDEN)
    return cells


def footprints(s, pts, g, seed=6):
    """A 1-wide trail that wanders one block left/right (random walk, no gaps)."""
    rng = random.Random(seed)
    off = 0
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1), 1)
        along_z = abs(x2 - x1) < abs(z2 - z1)
        for i in range(n + 1):
            t = i / n
            x, z = round(x1 + (x2 - x1) * t), round(z1 + (z2 - z1) * t)
            if rng.random() < 0.3:
                off = max(-1, min(1, off + rng.choice((-1, 1))))
            x, z = (x + off, z) if along_z else (x, z + off)
            if s.inside(x, g, z) and s.get(x, g, z) in (AIR, SNOW):
                s.set(x, g, z, TRODDEN)


def crate_stack(s, x, z, g, w, l, hgt=2, seed=2, snow=True):
    """Barrels mixed with stripped-log rounds, snow on top of the exposed stacks."""
    rng = random.Random(seed)
    for dx in range(w):
        for dz in range(l):
            top = hgt if rng.random() < 0.7 else hgt - 1
            for k in range(top):
                s.set(x + dx, g + 1 + k, z + dz, BARREL if rng.random() < 0.7 else st.log(LOG, "y"))
            if snow and rng.random() < 0.7:
                snow_on_top(s, x + dx, g + top, z + dz, rng.randint(1, 3))


def skis(s, x, z, g, along="x"):
    """A pair of skis planted upright + two poles."""
    if along == "x":
        s.set(x, g + 1, z, st.trapdoor("cherry", "north", "bottom", open=True))
        s.set(x + 1, g + 1, z, st.trapdoor("cherry", "north", "bottom", open=True))
        s.set(x + 2, g + 1, z, FENCE)
        s.set(x + 3, g + 1, z, FENCE)
    else:
        s.set(x, g + 1, z, st.trapdoor("cherry", "west", "bottom", open=True))
        s.set(x, g + 1, z + 1, st.trapdoor("cherry", "west", "bottom", open=True))
        s.set(x, g + 1, z + 2, FENCE)
        s.set(x, g + 1, z + 3, FENCE)


def sled(s, x, z, g, facing="west", cargo=True):
    """Dog/pull sled 4x2 along x: raised deck (top slabs), curled nose stair, handlebar, cargo."""
    xs = list(range(x, x + 4))
    if facing == "west":
        nose, tail, nose_face = xs[0], xs[-1], "east"
    else:
        nose, tail, nose_face = xs[-1], xs[0], "west"
    for xx in xs:
        for zz in (z, z + 1):
            s.set(xx, g + 1, zz, st.slab("dark_oak", "top"))            # dark runners: the sled reads on snow
    for zz in (z, z + 1):
        s.set(nose, g + 1, zz, st.stairs("dark_oak", nose_face, "top"))
        s.set(tail, g + 2, zz, DARK_FENCE)
    if cargo:
        mid = xs[1] if facing == "west" else xs[2]
        s.set(mid, g + 2, z, BARREL)
        s.set(mid, g + 2, z + 1, WOOL_LG)
        s.set(mid + (1 if facing == "west" else -1), g + 2, z + 1, st.slab("spruce", "bottom"))


def snowmobile(s, x, z, g, facing="west"):
    """6x2 snowmobile along x: iron-trapdoor skis, quartz-stair nose, white hood with an iron-trapdoor windshield,
    black padded seat (carpet), rear rack (iron trapdoor) with cargo, handlebar button."""
    step = 1 if facing == "west" else -1
    x0 = x if facing == "west" else x + 5          # skis end
    ski, nose, hood, seat_a, seat_b, rack = [x0 + step * k for k in range(6)]
    for zz in (z, z + 1):
        s.set(ski, g + 1, zz, st.trapdoor("iron", "north" if zz == z else "south", "bottom", open=False))
        s.set(nose, g + 1, zz, st.stairs("quartz", OPP[facing]))
        s.set(hood, g + 1, zz, "minecraft:white_concrete")
        s.set(hood, g + 2, zz, st.trapdoor("iron", facing, "bottom", open=True))       # windshield
        for sx in (seat_a, seat_b):
            s.set(sx, g + 1, zz, DARK)                                          # dark track unit under the seat
            s.set(sx, g + 2, zz, "minecraft:black_carpet")
        s.set(rack, g + 1, zz, st.trapdoor("iron", facing, "top", open=False))
    s.set(hood, g + 2, z, "minecraft:polished_blackstone_button[face=floor,facing=" + facing + "]")
    s.set(rack, g + 2, z + 1, BARREL)
    s.set(rack, g + 2, z, st.slab("spruce", "bottom"))                                      # strapped crate lid


def string_lights(s, poles, g, top=5, seed=3):
    """Poles (fence, `top`-1 high) linked by low sagging chains: the 2 blocks by each pole at `top`, the middle
    span one lower, lanterns hung straight under the chain every 4th block (still 2 clear blocks to walk)."""
    for (x, z) in poles:
        for y in range(g + 1, g + top):
            s.set(x, y, z, FENCE)
    for (x1, z1), (x2, z2) in zip(poles, poles[1:]):
        ax = "x" if z1 == z2 else "z"
        n = max(abs(x2 - x1), abs(z2 - z1))
        for i in range(1, n):
            x = x1 + (x2 - x1) * i // n
            z = z1 + (z2 - z1) * i // n
            outer = i <= 2 or i >= n - 2
            if i in (2, n - 2):                                  # sag transition: vertical link + lower chain
                s.set(x, g + top, z, st.chain("y"))
                s.set(x, g + top - 1, z, st.chain(ax))
            else:
                s.set(x, g + top if outer else g + top - 1, z, st.chain(ax))
            if not outer and (i - 2) % 4 == 2:
                s.set(x, g + top - 2, z, st.lantern(hanging=True))


def shed_cherry(s, x, y, z, w, l, hgt):
    """Small cherry-plank shed (walls + flat plank roof with slab eaves + snow)."""
    sh.box(s, x, y, z, x + w - 1, y + hgt - 1, z + l - 1, CHERRY)
    sh.box(s, x + 1, y, z + 1, x + w - 2, y + hgt - 1, z + l - 2, AIR)
    for cx, cz in ((x, z), (x + w - 1, z), (x, z + l - 1), (x + w - 1, z + l - 1)):   # dark corner trim
        sh.box(s, cx, y, cz, cx, y + hgt - 1, cz, st.log(DARK_LOG, "y"))
    for dx in range(-1, w + 1):
        for dz in range(-1, l + 1):
            edge = dx in (-1, w) or dz in (-1, l)
            s.set(x + dx, y + hgt, z + dz, st.slab("cherry", "bottom") if edge else CHERRY)


# ----------------------------------------------------------------------------------------------- camp_small
def build_small():
    W, H, L, G = 22, 10, 22, 1
    s = Schematic(W, H, L, ground=G)

    fire = (12, 10)
    # tent A: ridge along x, door to the east (toward the fire); tent B: ridge along z, door north
    PA, ufA, ubA, dA, _ = tent(s, 2, 9, 5, G, 3, along="x", front="+", seed=11, lee=-1)
    PB, ufB, ubB, dB, _ = tent(s, 12, 19, 16, G, 3, along="z", front="-", seed=12, lee=1)
    # interiors: bed at the back, chest / crate beside, hanging lantern, lavender carpet
    for P, ub, d, ax, bed_face in ((PA, ubA, dA, "x", "west"), (PB, ubB, dB, "z", "north")):
        xh, zh = P(ub + d, 0)
        xf, zf = P(ub + 2 * d, 0)
        s.set(xh, G + 1, zh, st.bed("cyan", bed_face, "head"))
        s.set(xf, G + 1, zf, st.bed("cyan", bed_face, "foot"))
        s.set(xf, G + 2, zf, st.lantern(hanging=True))
        x1, z1 = P(ub + d, 1)
        s.set(x1, G + 1, z1, BARREL)
        x2, z2 = P(ub + 3 * d, -1)
        s.set(x2, G + 1, z2, "minecraft:purple_carpet")
        x2, z2 = P(ub + 3 * d, 0)
        s.set(x2, G + 1, z2, "minecraft:magenta_carpet")
    xc, zc = PA(ubA + dA, -1)
    s.add_chest(xc, G + 1, zc, "east", "minecraft:chests/igloo_chest")
    xc, zc = PB(ubB + dB, -1)
    s.set(xc, G + 1, zc, "minecraft:lantern[hanging=false]")
    # campfire ring between the two doors
    campfire_ring(s, fire[0], fire[1], G, seats=("n", "e", "w"))
    s.set(fire[0], G + 1, fire[1] + 2, "minecraft:water_cauldron[level=2]")        # melt-water pot by the fire
    # crates (2 barrels + a log round) with a light-gray tarp thrown over, lantern pole, skis, snowshoes, sled
    s.set(3, G + 1, 11, BARREL); s.set(4, G + 1, 11, BARREL); s.set(3, G + 1, 12, st.log(LOG, "y"))
    s.set(3, G + 2, 11, "minecraft:light_gray_carpet"); s.set(4, G + 2, 11, "minecraft:light_gray_carpet")
    s.set(3, G + 2, 12, st.snow_layer(2))
    lantern_pole(s, 8, 12, G, height=3)
    skis(s, 6, 10, G, along="x")
    s.set(10, G + 1, 12, st.trapdoor("spruce", "east", "bottom", open=True))     # snowshoes leaning on the pole
    s.set(9, G + 1, 13, st.trapdoor("spruce", "north", "bottom", open=True))
    sled(s, 4, 15, G, facing="west")
    # lookout post (NE corner), flag pole west of the fire
    lx, lz = 17, 3
    lookout_post(s, lx, lz, G)
    flag_pole(s, 12, 5, G, 7, rotation=4, base=False)   # 7 high: keeps the schematic >= 9 tall (renderer limit)
    # wind break north of the fire: a light-gray tarp stretched between two fence posts, snow caught on top
    wz = fire[1] - 4
    for dx in (-3, 3):
        for y in range(G + 1, G + 4):
            s.set(fire[0] + dx, y, wz, FENCE)
    for dx in range(-2, 3):
        s.set(fire[0] + dx, G + 1, wz, WOOL_LG)
        s.set(fire[0] + dx, G + 2, wz, WOOL_LG)
        s.set(fire[0] + dx, G + 3, wz, st.snow_layer(1 + (dx + 2) % 3))
    for dx in range(-2, 3):                                                       # drift on the windward face
        snow_layer_if_air(s, fire[0] + dx, G + 1, wz - 1, 2 + (dx * 7) % 3)
    # a few dropped things around the camp
    s.set(15, G + 1, 12, st.log(LOG, "x"))                                        # firewood
    s.set(15, G + 1, 13, st.log(LOG, "x"))
    s.set(15, G + 2, 12, st.snow_layer(1))
    s.set(7, G + 1, 17, "minecraft:hay_block[axis=x]")
    # signs
    xs, zs = PA(ufA + dA, 2)
    s.add_sign(xs, G + 1, zs, "minecraft:spruce_sign[rotation=12]", ["BIVOUAC 3", "2 pers.", "retour J+2", "- Lena"])
    xs, zs = PB(ufB + dB, 2)
    s.add_sign(xs, G + 1, zs, "minecraft:spruce_sign[rotation=8]", ["JOURNAL 12", "cristaux bleus", "a 400m ouest", "chantent la nuit"])
    # trodden snow: doors -> fire, fire -> lookout, fire -> crates
    xa, za = PA(ufA + 2 * dA, 0)
    xb, zb = PB(ufB + 2 * dB, 0)
    path(s, [(xa, za - 1), (fire[0] - 1, fire[1] - 1), (xb - 1, zb)], G, width=2, seed=31)
    footprints(s, [fire, (lx, lz + 2)], G, seed=32)
    footprints(s, [fire, (6, 13)], G, seed=33)
    footprints(s, [(xa + 1, za), (xa + 1, za + 6)], G, seed=34)
    path_edges(s, G, seed=38)
    sh.texturize(s, TRODDEN, PATH_MIX, seed=35)
    sh.texturize(s, WOOL, WOOL_MIX, seed=37)
    ground_pad(s, G, seed=39)
    sh.snow_cover(s, y_min=G + 1, prob=0.35, seed=36,
                  skip=["wool", "concrete", "bed", "carpet", "cake", "planks", "stripped", "hay", "snow_block",
                        "deepslate"])
    return s.cropped(pad=1)


# ----------------------------------------------------------------------------------------------- camp_base
def build_base():
    W, H, L, G = 44, 16, 44, 1
    s = Schematic(W, H, L, ground=G)
    fire = (23, 25)

    # ---- mess tent (wall tent, 12x9) ridge along z, door south toward the plaza
    PM, ufM, ubM, dM, ridgeM = tent(s, 2, 13, 18, G, 4, along="z", front="+", wall=1, bands=(4, 7, 11), seed=41,
                                     lee=-1, window=False, glass_strip=True, awning_lanterns=2, banner="cyan")
    # long table (fence + trapdoor top) with stair chairs, kitchen at the back, hanging lanterns
    for u in range(5, 11):
        x, z = PM(u, 0)
        s.set(x, G + 1, z, FENCE)
        s.set(x, G + 2, z, st.trapdoor("spruce", "north", "bottom", open=False))
        for v, face in ((-1, "west"), (1, "east")):
            x, z = PM(u, v)
            s.set(x, G + 1, z, st.stairs("spruce", face))
    for u in (4, 7, 10):
        x, z = PM(u, 0)
        s.set(x, G + 4, z, st.lantern(hanging=True))
    x, z = PM(8, 0); s.set(x, G + 3, z, "minecraft:cake[bites=2]")
    x, z = PM(6, 0); s.set(x, G + 3, z, st.candle("cyan", 3))
    x, z = PM(3, -1); s.set(x, G + 1, z, "minecraft:smoker[facing=south,lit=true]")
    x, z = PM(3, 0); s.set(x, G + 1, z, "minecraft:crafting_table")
    x, z = PM(3, 1); s.set(x, G + 1, z, "minecraft:water_cauldron[level=3]")
    x, z = PM(3, -2); s.set(x, G + 1, z, BARREL)
    x, z = PM(3, -3); s.set(x, G + 1, z, BARREL)
    x, z = PM(4, -3); s.set(x, G + 1, z, BARREL)
    x, z = PM(3, 2); s.add_chest(x, G + 1, z, "south", "minecraft:chests/igloo_chest")
    x, z = PM(3, 3); s.set(x, G + 1, z, "minecraft:hay_block[axis=y]")
    x, z = PM(11, -3); s.set(x, G + 1, z, BARREL)
    x, z = PM(12, 3); s.set(x, G + 1, z, "minecraft:lantern[hanging=false]")
    for u in (5, 8, 11):                                                  # lavender runner along the east side
        x, z = PM(u, 2); s.set(x, G + 1, z, "minecraft:purple_carpet")
        x, z = PM(u + 1, 2); s.set(x, G + 1, z, "minecraft:magenta_carpet")
    x, z = PM(ufM + dM, 2)
    s.add_sign(x, G + 1, z, "minecraft:spruce_sign[rotation=8]", ["REFECTOIRE", "repas 7h 12h 19h", "PROCHAIN", "RAVITAILLEMENT"])
    x, z = PM(ufM + dM, 3)
    s.add_sign(x, G + 1, z, "minecraft:spruce_sign[rotation=8]", ["J+12", "rationnement", "1 cafe / jour", "- le chef"])

    # ---- science tent, ridge along x, door east toward the plaza
    PS, ufS, ubS, dS, _ = tent(s, 2, 10, 22, G, 4, along="x", front="+", seed=42, lee=1)
    x, z = PS(3, 0); s.set(x, G + 1, z, "minecraft:lectern[facing=east,has_book=true,powered=false]")
    x, z = PS(3, -1); s.set(x, G + 1, z, "minecraft:chiseled_bookshelf[facing=east]")
    x, z = PS(3, 1); s.set(x, G + 1, z, "minecraft:brewing_stand")
    x, z = PS(3, 2); s.set(x, G + 1, z, "minecraft:water_cauldron[level=1]")
    x, z = PS(3, -2); s.add_chest(x, G + 1, z, "east", "minecraft:chests/simple_dungeon")
    for u, blk in ((5, "minecraft:cartography_table"), (6, "minecraft:daylight_detector[inverted=false,power=0]"),
                   (7, "minecraft:observer[facing=up,powered=false]"), (8, st.redstone_lamp(True))):
        x, z = PS(u, -2); s.set(x, G + 1, z, blk)
    for u, blk in ((5, "minecraft:packed_ice"), (6, "minecraft:blue_ice"), (7, "minecraft:amethyst_block"),
                   (8, st.facing_block("minecraft:amethyst_cluster", "up"))):
        x, z = PS(u, 2); s.set(x, G + 1, z, blk)
    x, z = PS(7, 2); s.set(x, G + 2, z, st.facing_block("minecraft:medium_amethyst_bud", "up"))
    x, z = PS(4, 1); s.set(x, G + 1, z, "minecraft:smooth_quartz_slab[type=bottom]")   # lab bench
    x, z = PS(5, 1); s.set(x, G + 1, z, "minecraft:smooth_quartz_slab[type=bottom]")
    x, z = PS(6, 1); s.set(x, G + 1, z, "minecraft:purpur_slab[type=bottom]")          # alien-tech specimen tray
    x, z = PS(5, 1); s.set(x, G + 2, z, "minecraft:light_blue_stained_glass_pane")     # specimen jar
    x, z = PS(7, 0); s.set(x, G + 1, z, "minecraft:purple_carpet")
    x, z = PS(6, 0); s.set(x, G + 1, z, "minecraft:magenta_carpet")
    for u in (4, 8):
        x, z = PS(u, 0); s.set(x, G + 3, z, st.lantern(hanging=True))
    x, z = PS(ufS + dS, 2)
    s.add_sign(x, G + 1, z, "minecraft:spruce_sign[rotation=12]", ["LABO TERRAIN", "echantillons", "cristal bleu", "NE PAS TOUCHER"])
    # ice-core rack outside the lab (north side)
    for k in range(3):
        s.set(4 + k, G + 1, 16, "minecraft:packed_ice")
    s.set(3, G + 1, 16, FENCE); s.set(7, G + 1, 16, FENCE)

    # ---- sleeping tents (3)
    tents_small = [(34, 41, 10, "x", "-", -1), (34, 41, 20, "x", "-", 1), (34, 41, 14, "z", "-", -1)]
    for i, (u1, u2, c, ax, fr, lee) in enumerate(tents_small):
        P, uf, ub, d, _ = tent(s, u1, u2, c, G, 3, along=ax, front=fr, seed=50 + i, lee=lee)
        bed_face = ("west" if ax == "x" else "north")
        xh, zh = P(ub + d, 0); xf, zf = P(ub + 2 * d, 0)
        s.set(xh, G + 1, zh, st.bed("cyan", bed_face, "head"))
        s.set(xf, G + 1, zf, st.bed("cyan", bed_face, "foot"))
        s.set(xf, G + 2, zf, st.lantern(hanging=True))
        x1, z1 = P(ub + d, 1); s.set(x1, G + 1, z1, BARREL)
        x1, z1 = P(ub + d, -1); s.set(x1, G + 1, z1, "minecraft:chest[facing=" + ("east" if ax == "x" else "south") + ",type=single,waterlogged=false]")
        x1, z1 = P(ub + 3 * d, 1); s.set(x1, G + 1, z1, "minecraft:purple_carpet")
        x1, z1 = P(ub + 4 * d, 1); s.set(x1, G + 1, z1, "minecraft:magenta_carpet")
        x1, z1 = P(uf + d, 2)
        s.add_sign(x1, G + 1, z1, "minecraft:spruce_sign[rotation=%d]" % (4 if ax == "x" else 8),
                   [["TENTE 1", "Lena + Marco"], ["TENTE 2", "Yann + Sofia"], ["TENTE 3", "Aziz (guide)"]][i] + ["", ""])

    # ---- plaza: campfire, flag, string lights, lookout deck
    campfire_ring(s, fire[0], fire[1], G)
    s.set(fire[0] - 1, G + 1, fire[1] + 1, "minecraft:water_cauldron[level=3]")
    s.set(fire[0] + 1, G + 1, fire[1] - 1, BARREL)
    lookout_deck(s, 39, 40, G)
    s.add_sign(38, G + 1, 42, "minecraft:spruce_sign[rotation=8]", ["VIGIE", "tour de garde", "2h chacun", "lumieres au N?"])
    flag_pole(s, 27, 21, G, 11, rotation=0)
    s.set(27, G + 12, 21, st.lightning_rod("up"))
    string_lights(s, [(16, 17), (30, 17), (30, 31), (16, 31), (16, 24)], G, top=5)

    # ---- radio mast (37,31): stone base, iron-bars mast, dipoles, lightning rod, 3 face-connected guy lines
    mx, mz = 37, 31
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            s.set(mx + dx, G, mz + dz, "minecraft:polished_deepslate")
    s.set(mx, G, mz, "minecraft:iron_block")
    for y in range(G + 1, G + 13):
        s.set(mx, y, mz, CAMP["flag_pole"])
    s.set(mx, G + 13, mz, st.lightning_rod("up"))
    s.set(mx, G + 11, mz, "minecraft:iron_block")
    for f, (dx, dz) in DXZ.items():
        s.set(mx + dx, G + 11, mz + dz, st.end_rod(f))
    s.set(mx, G + 7, mz, "minecraft:iron_block")                                          # crossbar / guy anchor
    s.set(mx - 1, G + 7, mz, "minecraft:daylight_detector[inverted=false,power=0]")        # dish
    s.set(mx, G + 9, mz, "minecraft:redstone_lamp[lit=true]")                             # warning light
    for dx, dz in ((1, 0), (0, 1), (0, -1)):
        guy_line(s, mx, G + 7, mz, dx, dz, G)
    for dx in (-1, 1):
        s.set(mx + dx, G + 1, mz + 1, "minecraft:polished_deepslate_slab[type=bottom]")
    s.set(mx + 1, G + 1, mz - 1, "minecraft:observer[facing=up,powered=false]")           # transceiver box
    s.set(mx - 1, G + 1, mz - 1, st.lantern(soul=True, hanging=False))
    s.add_sign(mx, G + 1, mz + 1, "minecraft:spruce_wall_sign[facing=south]", ["RADIO", "frequence 121.5", "appel 20h", "pas de reponse"])

    # ---- generator + ground cable to the mast: one straight horizontal chain run at g+1 (single axis)
    gx, gz = 31, 32
    s.set(gx, G + 1, gz, "minecraft:blast_furnace[facing=west,lit=true]")
    s.set(gx + 1, G + 1, gz, "minecraft:iron_block")
    s.set(gx, G + 1, gz + 1, "minecraft:iron_block")
    s.set(gx + 1, G + 1, gz + 1, BARREL)
    s.set(gx, G + 2, gz, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
    s.set(gx + 1, G + 2, gz, st.chain("y"))
    s.set(gx + 1, G + 3, gz, st.chain("y"))
    s.set(gx + 1, G + 4, gz, st.lantern(soul=True, hanging=False))
    s.set(gx, G + 2, gz + 1, "minecraft:lever[face=floor,facing=north,powered=true]")
    s.set(gx - 1, G + 1, gz + 1, "minecraft:redstone_lamp[lit=true]")
    for x in range(gx + 2, mx - 1):
        s.set(x, G + 1, gz, st.chain("x"))                                # ends on the mast's stone base slab

    # ---- weather station (NW, near the lab): mast + 2x2 louvred Stevenson screen + gauges
    wx, wz = 4, 13
    for y in range(G + 1, G + 4):
        s.set(wx, y, wz, FENCE)
    s.set(wx, G + 4, wz, "minecraft:daylight_detector[inverted=false,power=0]")
    s.set(wx, G + 5, wz, st.lightning_rod("up"))
    for dx, dz, f in ((0, 0, "west"), (1, 0, "north"), (1, 1, "east"), (0, 1, "south")):
        s.set(wx + 2 + dx, G + 1, wz + dz, FENCE)
        s.set(wx + 2 + dx, G + 2, wz + dz, st.trapdoor("iron", OPP[f], "bottom", open=True))   # louvres
        s.set(wx + 2 + dx, G + 3, wz + dz, "minecraft:smooth_stone_slab[type=bottom]")
    s.set(wx + 3, G + 4, wz, "minecraft:daylight_detector[inverted=true,power=0]")
    s.set(wx + 1, G + 1, wz + 2, FENCE)
    s.set(wx + 1, G + 2, wz + 2, "minecraft:lever[face=floor,facing=north,powered=false]")
    s.set(wx + 3, G + 1, wz + 2, "minecraft:water_cauldron[level=1]")     # rain gauge
    s.add_sign(wx - 1, G + 1, wz + 1, "minecraft:spruce_sign[rotation=12]", ["STATION METEO", "-41 C", "vent N 60kmh", "blizzard J+3?"])

    # ---- supply crates under a tarp (NW corner) + a few dropped things around the depot
    tx, tz = 3, 3
    crate_stack(s, tx, tz, G, 4, 3, hgt=2, seed=61, snow=False)
    for (dx, dz) in ((-1, -1), (4, -1), (-1, 3), (4, 3)):
        for y in range(G + 1, G + 4):
            s.set(tx + dx, y, tz + dz, DARK_FENCE)                          # dark corner posts outline the tarp
    rng = random.Random(62)
    for dx in range(-1, 5):
        for dz in range(-1, 4):
            s.set(tx + dx, G + 4, tz + dz, CYAN if dz == 1 else WOOL_LG)
            if rng.random() < 0.55:
                s.set(tx + dx, G + 5, tz + dz, st.snow_layer(rng.randint(1, 3)))
    for dx in range(-1, 5):
        s.set(tx + dx, G + 3, tz - 2, st.trapdoor("spruce", "north", "top", open=False))
        s.set(tx + dx, G + 3, tz + 4, st.trapdoor("spruce", "south", "top", open=False))
    s.set(tx + 1, G + 3, tz + 1, "minecraft:cyan_shulker_box[facing=up]")
    s.add_sign(tx + 5, G + 1, tz + 1, "minecraft:spruce_sign[rotation=12]", ["DEPOT", "vivres 40 j", "inventaire", "chaque lundi"])
    for (x, z, blk) in ((9, 3, BARREL), (10, 4, st.log(LOG, "x")), (8, 8, "minecraft:hay_block[axis=z]"),
                        (11, 7, BARREL), (2, 9, st.log(LOG, "z"))):
        s.set(x, G + 1, z, blk)
        s.set(x, G + 2, z, st.snow_layer(1))

    # ---- fuel dump (SW): fenced square, orange corner markers, lying drums, hazard patch
    fx, fz = 3, 31
    for (dx, dz) in ((0, 0), (3, 0), (0, 3), (3, 3)):
        s.set(fx + dx, G + 1, fz + dz, ORANGE)
        s.set(fx + dx, G + 2, fz + dz, FENCE)
    for k in (1, 2):
        s.set(fx + k, G + 1, fz, FENCE); s.set(fx + k, G + 1, fz + 3, FENCE)
        s.set(fx, G + 1, fz + k, FENCE)
    s.set(fx + 3, G + 1, fz + 1, st.fence_gate("spruce", "east"))
    s.set(fx + 3, G + 1, fz + 2, FENCE)
    for (dx, dz) in ((1, 1), (2, 1), (1, 2), (2, 2)):
        s.set(fx + dx, G + 1, fz + dz, "minecraft:barrel[facing=east,open=false]")
    s.set(fx + 1, G + 2, fz + 1, "minecraft:barrel[facing=east,open=false]")
    s.set(fx + 2, G + 2, fz + 2, st.snow_layer(2))
    for (dx, dz) in ((4, 1), (4, 2), (5, 1), (5, 2), (6, 1)):
        s.set(fx + dx, G + 1, fz + dz, "minecraft:orange_carpet")
    s.add_sign(fx + 5, G + 1, fz, "minecraft:spruce_sign[rotation=12]", ["CARBURANT", "DANGER", "pas de feu", "a 10 m"])

    # ---- latrine shed (NE corner): cherry planks, spruce door, iron-trapdoor vents, snow on the roof
    lx, lz = 39, 2
    shed_cherry(s, lx, G + 1, lz, 3, 3, 3)
    s.set(lx + 1, G + 1, lz + 2, st.door("spruce", "south", "lower"))
    s.set(lx + 1, G + 2, lz + 2, st.door("spruce", "south", "upper"))
    s.set(lx + 1, G + 1, lz + 1, st.stairs("spruce", "north"))
    s.set(lx + 1, G + 3, lz + 1, st.lantern(hanging=True))
    s.set(lx + 2, G + 3, lz + 1, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(lx, G + 3, lz + 1, st.trapdoor("iron", "east", "bottom", open=True))
    for dx in range(3):
        for dz in range(3):
            if (dx + dz) % 3 != 1:
                s.set(lx + dx, G + 5, lz + dz, st.snow_layer(1 + (dx + dz) % 3))
    s.add_sign(lx + 1, G + 3, lz + 3, "minecraft:spruce_wall_sign[facing=south]", ["WC", "frappez avant", "", ""])

    # ---- sled-dog pen (SE) with cherry kennels, hay, water, sled parked beside
    px1, pz1, px2, pz2 = 30, 37, 36, 42
    for x in range(px1, px2 + 1):
        s.set(x, G + 1, pz1, FENCE); s.set(x, G + 1, pz2, FENCE)
    for z in range(pz1, pz2 + 1):
        s.set(px1, G + 1, z, FENCE); s.set(px2, G + 1, z, FENCE)
    s.set(px1, G + 1, pz1 + 2, st.fence_gate("spruce", "east"))
    for kz in (pz1 + 1, pz1 + 4):
        s.set(px2 - 1, G + 1, kz, CHERRY)
        s.set(px2 - 2, G + 1, kz, "minecraft:hay_block[axis=x]")
        s.set(px2 - 1, G + 2, kz, st.slab("cherry", "bottom")); s.set(px2 - 2, G + 2, kz, st.slab("cherry", "bottom"))
        s.set(px2 - 3, G + 1, kz, st.stairs("cherry", "east", "top"))     # kennel porch
    s.set(px1 + 1, G + 1, pz2 - 1, "minecraft:water_cauldron[level=3]")
    s.set(px1 + 2, G + 1, pz2 - 1, "minecraft:barrel[facing=up,open=true]")
    s.set(px1 + 1, G + 1, pz1 + 1, "minecraft:hay_block[axis=y]")
    sh.ground_disc(s, (px1 + px2) / 2, (pz1 + pz2) / 2, 2.4, G, TRODDEN, seed=77, noise=0.4, depth=1)
    s.add_sign(px1 - 1, G + 1, pz1, "minecraft:spruce_sign[rotation=4]", ["CHIENS x8", "attention", "ils mordent", ""])
    sled(s, 25, 38, G, facing="west")
    for x in range(22, 25):
        s.set(x, G + 1, 38, st.chain("x"))                                # trace rope laid out in front

    # ---- snowmobiles parked by the entrance
    snowmobile(s, 17, 40, G, facing="west")
    snowmobile(s, 17, 43, G, facing="west")
    s.set(24, G + 1, 41, BARREL)

    # ---- entrance gate (south): two log posts, a log beam, hanging signs, lanterns, cyan + lavender banners
    ex, ez = 27, 42
    for y in range(G + 1, G + 5):
        s.set(ex - 2, y, ez, st.log(LOG, "y"))
        s.set(ex + 2, y, ez, st.log(LOG, "y"))
    sh.box(s, ex - 1, G + 5, ez, ex + 1, G + 5, ez, st.log(LOG, "x"))
    s.set(ex - 2, G + 5, ez, st.log(LOG, "x")); s.set(ex + 2, G + 5, ez, st.log(LOG, "x"))
    s.set(ex - 2, G + 6, ez, st.banner("cyan", 0))
    s.set(ex + 2, G + 6, ez, st.banner("magenta", 0))
    hanging_sign(s, ex - 1, G + 4, ez, 0, ["CAMP DE BASE", "expedition NEIGE", "12 personnes", "bienvenue"])
    hanging_sign(s, ex + 1, G + 4, ez, 0, ["PROCHAIN", "RAVITAILLEMENT", "J+12", "econome!"])
    s.set(ex, G + 4, ez, st.lantern(hanging=True))
    s.set(ex - 1, G + 6, ez, st.snow_layer(1)); s.set(ex + 1, G + 6, ez, st.snow_layer(2))
    # lantern poles
    lantern_pole(s, 20, 20, G, height=3)
    lantern_pole(s, 27, 29, G, height=3)

    # ---- paths (trodden snow) linking everything
    xm, zm = PM(ufM + 2 * dM, 0)
    xs_, zs_ = PS(ufS + 2 * dS, 0)
    path(s, [(ex - 1, 43), (ex - 1, 36), (fire[0] - 1, fire[1] + 4)], G, width=2, seed=81)       # gate -> plaza
    path(s, [(fire[0] - 1, fire[1] - 4), (fire[0] - 1, 20), (xm - 1, zm - 1)], G, width=2, seed=82)  # plaza -> mess
    path(s, [(fire[0] - 4, fire[1] - 1), (16, 23), (xs_, zs_ - 1)], G, width=2, seed=83)          # plaza -> lab
    path(s, [(fire[0] + 4, fire[1] - 1), (31, 20), (32, 20)], G, width=2, seed=84)               # plaza -> tents
    path(s, [(32, 19), (32, 10)], G, width=2, seed=85)
    path(s, [(32, 15), (33, 15)], G, width=2, seed=86)
    footprints(s, [(fire[0] - 3, fire[1] + 2), (18, 30), (14, 32)], G, seed=95)
    footprints(s, [(33, 22), (34, 28), (mx, mz + 2)], G, seed=87)
    footprints(s, [(xs_, zs_ - 6), (wx + 2, wz + 4)], G, seed=88)
    footprints(s, [(fire[0] - 2, fire[1] + 6), (fx + 7, fz + 1)], G, seed=89)
    footprints(s, [(32, 10), (lx + 1, lz + 6)], G, seed=90)
    footprints(s, [(ex + 3, 40), (px1 - 1, pz1 + 2)], G, seed=91)
    path_edges(s, G, seed=96)
    sh.texturize(s, TRODDEN, PATH_MIX, seed=92)
    sh.texturize(s, WOOL, WOOL_MIX, seed=94)
    ground_pad(s, G, seed=97)
    sh.snow_cover(s, y_min=G + 1, prob=0.3, seed=93,
                  skip=["wool", "concrete", "bed", "carpet", "cake", "planks", "shulker", "orange", "stripped", "hay",
                        "snow_block", "deepslate"])
    return s.cropped(pad=1)


def build():
    return {"camp_small": build_small(), "camp_base": build_base()}

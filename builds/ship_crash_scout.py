"""'Le Chasseur' - a sleek single-seat interceptor that nose-dived into a snow bank.

Story: it came sliding in from the east, gouged a long furrow with pushed-up lips and a spray fan, clipped a crystal
spike that tore the north wing off, then buried its nose in a drift. The pilot blew the canopy hatch (it lies in the
snow south of the cockpit), grabbed what he could, planted a beacon and walked north. The north engine burst and is
still smoking blue, the south nozzle keeps a dying cyan glow.

Layout (x = east, z = south): nose at low x (buried), tail at high x (raised ~6 blocks). Hull lofted along x with a
rising centreline so the whole ship is tilted. Attached delta wing on the south side, torn stub on the north,
the torn wing lying ~10 blocks north-east in the snow, root sunk, tip propped on a drift.

Build order matters: hull loft -> bevel pass (slabs on top edges, stairs on the belly) -> zone recolour (belly,
keel, rib rings, purpur cheat line) -> cockpit -> canopy (narrow, dark ribs, holes) -> wings -> nacelles -> fin ->
props -> texture -> snow.
"""
import math
import random

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_SCORCH

# ---- block families: (full block, slab material, stairs material). The bevel pass builds the hull in WHITE and
#      `recolour` swaps a cell to another family while keeping its shape (slab/stairs state).
WHITE = ("minecraft:quartz_block", "smooth_quartz", "smooth_quartz")
BELLY = ("minecraft:deepslate_tiles", "deepslate_tile", "deepslate_tile")
DARK = ("minecraft:polished_deepslate", "polished_deepslate", "polished_deepslate")
ACCENT = ("minecraft:purpur_block", "purpur", "purpur")
SCORCH = ("minecraft:blackstone", "blackstone", "blackstone")

HULL = WHITE[0]
MIX_SKIN = [("minecraft:quartz_block", 8), ("minecraft:smooth_quartz", 2)]        # two close shades only: calm skin
GLASS = SHIP["glass"]
PANE = SHIP["glass_pane"]
SNOW = GROUND["snow"]
PACKED = "minecraft:white_concrete_powder"
BARS = "minecraft:iron_bars"
FURROW_MIX = ["minecraft:gray_concrete_powder", "minecraft:gray_concrete_powder", "minecraft:light_gray_concrete_powder",
              "minecraft:light_gray_concrete_powder", "minecraft:light_gray_concrete_powder", "minecraft:black_concrete_powder"]

D4 = (("north", 0, -1), ("south", 0, 1), ("west", -1, 0), ("east", 1, 0))
OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}


def _family_of(block):
    for fam in (WHITE, BELLY, DARK, ACCENT, SCORCH):
        if block == fam[0] or block.startswith("minecraft:" + fam[1] + "_slab") or block.startswith("minecraft:" + fam[2] + "_stairs"):
            return fam
    return None


def recolour(s, cells, fam):
    """Swap every cell in `cells` (iterable of (x,y,z) or a bool mask) to family `fam`, keeping slab/stair shape."""
    if isinstance(cells, np.ndarray):
        cells = [tuple(int(v) for v in c) for c in np.argwhere(cells)]
    for (x, y, z) in cells:
        b = s.get(x, y, z)
        src = _family_of(b)
        if src is None:
            continue
        if b == src[0]:
            s.set(x, y, z, fam[0])
        elif "_slab[" in b:
            _, p = st.parse(b)
            s.set(x, y, z, st.slab(fam[1], p.get("type", "bottom")))
        elif "_stairs[" in b:
            _, p = st.parse(b)
            s.set(x, y, z, st.stairs(fam[2], p.get("facing", "north"), p.get("half", "bottom")))


def bevel(s, mask, fam, y_min_bottom=0, do_top=True, do_bottom=True):
    """Round the edges of a solid `mask`. TOP: wherever a column's top is higher than a neighbour's the top block
    becomes a bottom slab (slabs only: no stair sawtooth on the roofline). BELLY: the mirror with top-half stairs
    (tall side toward the higher neighbour) or top slabs. Only touches full blocks of family `fam`."""
    W, H, L = mask.shape
    top, bot = {}, {}
    for x in range(W):
        for z in range(L):
            col = np.nonzero(mask[x, :, z])[0]
            if len(col):
                top[(x, z)] = int(col.max())
                bot[(x, z)] = int(col.min())

    def pick(sides, half):
        if len(sides) == 1:
            return st.stairs(fam[2], OPP[sides[0]], half)
        if len(sides) == 2 and OPP[sides[0]] != sides[1]:
            xd = [d for d in sides if d in ("east", "west")][0]
            return st.stairs(fam[2], OPP[xd], half)
        return st.slab(fam[1], half)

    if do_top:
        for (x, z), T in top.items():
            if bot[(x, z)] == T or s.get(x, T, z) != fam[0] or not mask[x, T - 1, z]:
                continue
            lows = [d for d, dx, dz in D4 if top.get((x + dx, z + dz), -1) < T]
            if lows:
                s.set(x, T, z, st.slab(fam[1], "bottom"))
    if do_bottom:
        for (x, z), B in bot.items():
            if top[(x, z)] == B or B <= y_min_bottom or s.get(x, B, z) != fam[0] or not mask[x, B + 1, z]:
                continue
            highs = [d for d, dx, dz in D4 if bot.get((x + dx, z + dz), 99) > B]
            if highs:
                s.set(x, B, z, pick(highs, "top"))


def build():
    W, H, L, G = 46, 24, 36, 4
    CZ = 18
    s = Schematic(W, H, L, ground=G)
    rng = random.Random(7)
    sh.ground_slab(s, G, SNOW, depth=5)

    # ------------------------------------------------------------------ hull centreline (tilted: nose buried, tail up)
    SECS = [(3, 2.6, CZ, 0.7, 0.9), (9, 4.1, CZ, 2.3, 3.1), (17, 5.9, CZ, 3.2, 4.3), (26, 8.3, CZ, 2.7, 3.5),
            (34, 11.0, CZ, 1.2, 1.6)]
    SX = [p[0] for p in SECS]

    def cy(x):
        return float(np.interp(x, SX, [p[1] for p in SECS]))

    def ry(x):
        return float(np.interp(x, SX, [p[3] for p in SECS]))

    def rz(x):
        return float(np.interp(x, SX, [p[4] for p in SECS]))

    xs = np.arange(W)[:, None, None]
    ys = np.arange(H)[None, :, None]
    zs = np.arange(L)[None, None, :]
    CY = np.interp(xs.astype(float), SX, [p[1] for p in SECS])

    # ------------------------------------------------------------------ terrain: skid furrow (east) + snow bank (west)
    # furrow: 2 deep near the ship, 1 deep further east, dirty powder floor, raised snow lips, a snow-layer spray fan
    for x in range(23, W - 1):
        deep = x <= 38
        for z in range(CZ - 11, CZ + 12):
            if not (0 <= z < L):
                continue
            d = abs(z - CZ)
            if deep:
                dep = 2 if d <= 2 else (1 if d == 3 else 0)
                lip = d == 4
                lip_d = 4
            else:
                dep = 1 if d <= 1 else (1 if d == 2 and rng.random() < 0.6 else 0)
                lip = (d == 3) or (d == 2 and dep == 0)
                lip_d = 3
            if dep:
                for y in range(G - dep + 1, G + 1):
                    s.set(x, y, z, "air")
                dirty = (d <= 1) or (deep and d <= 2)
                s.set(x, G - dep, z, rng.choice(FURROW_MIX) if dirty and rng.random() < 0.85 else PACKED)
            elif lip:
                if rng.random() < 0.92:
                    s.set(x, G + 1, z, SNOW)                                   # pushed-up lip
                    if rng.random() < 0.4:
                        s.set(x, G + 2, z, st.snow_layer(rng.randint(2, 4)))
                else:
                    s.set(x, G + 1, z, st.snow_layer(rng.randint(4, 7)))
            elif d > lip_d:
                fan = 4.5 + (x - 28) * 0.55                                    # spray widens behind the tail
                if d <= fan:
                    p = 0.55 * (1 - (d - lip_d) / (fan - lip_d + 1))
                    if rng.random() < p:
                        s.set(x, G + 1, z, st.snow_layer(rng.randint(2, 5)))
    # snow bank the nose dived into: noisy drift, a bow-wave in front of the nose, ice and crystal shards
    for x in range(0, 16):
        for z in range(CZ - 10, CZ + 11):
            nx, nz = (x - 2) / 10.0, (z - CZ) / 8.0
            f = 1 - nx * nx - nz * nz
            if f <= 0:
                continue
            n = sh.value_noise2(x, z, 21, 5.0)
            n2 = sh.value_noise2(x + 40, z + 40, 33, 2.5)
            h = 3.2 * f * (0.5 + 0.9 * n) + 0.7 * (n2 - 0.5)
            h += 1.4 * max(0.0, 1 - abs(x - 2) / 3.0) * max(0.0, 1 - abs(z - CZ) / 5.0)   # bow wave ahead of the nose
            hi = int(h)
            for y in range(G + 1, G + 1 + hi):
                s.set(x, y, z, SNOW)
            frac = h - hi
            if frac > 0.12 and s.is_air(x, G + 1 + hi, z):
                s.set(x, G + 1 + hi, z, st.snow_layer(max(1, min(7, int(frac * 8)))))
            elif hi >= 1 and rng.random() < 0.12:
                s.set(x, G + hi, z, "minecraft:packed_ice")                    # compacted ice in the drift
    for (x, z, hgt) in ((2, CZ - 6, 1), (5, CZ + 7, 2), (1, CZ + 3, 1)):       # blue-ice shards poking out of the drift
        ty = s.top_y(x, z)
        if s.get(x, ty, z).startswith("minecraft:snow["):
            s.set(x, ty, z, "air")
            ty -= 1
        s.set(x, ty, z, "minecraft:blue_ice")                                # base sunk into the drift
        for y in range(ty + 1, ty + 1 + hgt):
            s.set(x, y, z, "minecraft:blue_ice" if y < ty + hgt else GROUND["ice_glass"])

    # ------------------------------------------------------------------ hull: loft, bevel, zones
    mask = sh.loft(s, SECS, HULL, axis="x")
    surf = sh.surface_mask(s, mask)
    bevel(s, mask, WHITE, y_min_bottom=G + 1)
    recolour(s, mask & (ys <= CY - 1.4), BELLY)                              # dark belly
    recolour(s, surf & (ys <= CY - 1.6) & (np.abs(zs - CZ) <= 0.6), DARK)    # keel line
    RINGS = (9, 21, 28)
    recolour(s, surf & np.isin(xs, RINGS), DARK)                             # rib rings / canopy frames

    def width_at(x, y):
        row = np.nonzero(mask[x, y, :])[0]
        return int(np.abs(row - CZ).max()) if len(row) else -1

    # continuous lavender cheat line: the widest white row of every section, outermost cell on both flanks
    stripe, prev = [], None
    for x in range(6, 32):
        y_lo = int(math.floor(cy(x) - 1.4)) + 1                              # first row above the dark belly
        best = max(range(y_lo, y_lo + 3), key=lambda y: (width_at(x, y), -y))
        if prev is not None:
            best = max(prev - 1, min(prev + 1, best))
        prev = best
        for side in (-1, 1):
            z = CZ
            while 0 <= z + side < L and mask[x, best, z + side]:
                z += side
            if mask[x, best, z] and abs(z - CZ) >= 2:
                stripe.append((x, best, z))
    recolour(s, stripe, ACCENT)

    # ------------------------------------------------------------------ cockpit interior (x 9..22)
    inner = sh.loft_mask(s, SECS, "x", shrink=1.0) & (xs >= 9) & (xs <= 22)
    floor_y = {x: int(math.floor(cy(x) - 1.2)) for x in range(9, 23)}
    fl = np.array([floor_y.get(x, 99) for x in range(W)])[:, None, None]
    s.data[inner & (ys > fl)] = 0
    # hull breach on the north flank at the nose: torn open, exposed ribs, one chain
    bx, by, bz = 10, cy(10) + 0.2, CZ - rz(10) - 0.3
    br = sh._mask_ellipsoid(s, bx, by, bz, 2.2, 1.7, 2.5)
    hole = br & mask
    s.data[hole] = 0
    for (x, y, z) in np.argwhere(hole & surf):
        x, y, z = int(x), int(y), int(z)
        if (x + y) % 2 == 0:
            s.set(x, y, z, BARS)
    for (x, y, z) in np.argwhere(sh.surface_mask(s, mask & ~hole) & mask & ~hole):
        x, y, z = int(x), int(y), int(z)
        if abs(x - bx) <= 2.7 and abs(y - by) <= 2.2 and z <= CZ - 1 and abs(z - bz) <= 3.0 and s.get(x, y, z) == HULL:
            s.set(x, y, z, DARK[0])                                      # dark torn rim
    s.set(11, floor_y[11] + 1, CZ - 2, st.chain("y"))
    # floor + furniture
    for x in range(9, 23):
        fy = floor_y[x]
        for z in range(CZ - 4, CZ + 5):
            if mask[x, fy, z] and s.data[x, fy + 1, z] == 0:
                s.set(x, fy, z, "minecraft:light_gray_concrete")
    s.set(14, floor_y[14], CZ, SHIP["light"])
    s.set(19, floor_y[19], CZ, SHIP["light"])
    s.set(17, floor_y[17], CZ - 2, SHIP["light"])
    for z in (CZ - 1, CZ, CZ + 1):
        s.set(12, floor_y[12] + 1, z, "minecraft:daylight_detector")
    s.set(11, floor_y[11] + 1, CZ, st.redstone_lamp(True))
    s.set(11, floor_y[11] + 1, CZ + 1, "minecraft:observer[facing=east]")
    s.set(11, floor_y[11] + 2, CZ, "minecraft:observer[facing=east]")
    s.set(15, floor_y[15] + 1, CZ, st.stairs("polished_deepslate", "east"))            # empty ejection seat
    s.set(15, floor_y[15] + 1, CZ - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(15, floor_y[15] + 1, CZ + 1, st.trapdoor("iron", "south", "bottom", open=True))
    s.set(15, floor_y[15], CZ, "minecraft:polished_deepslate")
    s.set(18, floor_y[18] + 1, CZ + 1, st.facing_block("minecraft:lectern", "west"))
    s.add_chest(19, floor_y[19] + 1, CZ - 1, "west", "minecraft:chests/shipwreck_supply")
    s.set(20, floor_y[20] + 1, CZ, "minecraft:barrel[facing=up,open=false]")
    s.set(21, floor_y[21] + 1, CZ + 1, "minecraft:cyan_shulker_box[facing=up]")
    s.add_sign(13, floor_y[13] + 1, CZ + 2, "minecraft:warped_sign[rotation=12]",
               ["JOURNAL 12", "ejection OK", "carburant 0", "marche vers N"])

    # ------------------------------------------------------------------ canopy: narrow bubble x 11..20, |dz|<=1 glass,
    # dark rails on the slab rows either side, dark ribs, windscreen + rear frame, 6 missing panes where the hatch blew
    def hull_top(x, z):
        col = np.nonzero(mask[x, :, z])[0]
        return int(col.max()) if len(col) else -1

    def hull_bot(x, z):
        col = np.nonzero(mask[x, :, z])[0]
        return int(col.min()) if len(col) else 99

    CAN_X0, CAN_X1 = 11, 20
    RIBS = (11, 14, 17)                                                       # windscreen bar + 2 ribs; ring x=21 closes it
    HOLES = {(12, 1), (13, 1), (13, 0), (15, 1), (15, 0), (18, 1)}
    glass_cells = []
    for x in range(CAN_X0, CAN_X1 + 1):
        T0 = hull_top(x, CZ)
        for dz in (-2, -1, 0, 1, 2):
            z = CZ + dz
            T = hull_top(x, z)
            if abs(dz) == 2:
                continue                                                     # white slab rows stay: bubble edge
            if x in RIBS:
                s.set(x, T, z, DARK[0])
            elif (x, dz) in HOLES:
                s.set(x, T, z, "air")
                glass_cells.append((x, T, z))
            else:
                s.set(x, T, z, GLASS)
                glass_cells.append((x, T, z))
    # make sure the interior is visible: a hull block right under canopy glass with air below it becomes glass
    for (x, y, z) in glass_cells:
        if s.get(x, y - 1, z) == HULL and s.is_air(x, y - 2, z):
            s.set(x, y - 1, z, GLASS)

    # ------------------------------------------------------------------ wings
    SPAN = 9

    def wing_cells():
        """(u, v, kind) in wing-local coords: u = span 0..SPAN, v = chord. kind: le / te / body / stripe / tip."""
        out = []
        for u in range(0, SPAN + 1):
            v0, v1 = int(round(1.2 * u)), int(round(12.0 + 0.3 * u))
            prev_v0 = int(round(1.2 * (u - 1))) if u > 0 else v0
            for v in range(min(v0, prev_v0 + 1), v1 + 1):
                if v <= v0:
                    kind = "le"
                elif v == v1:
                    kind = "te"
                elif v == 9:
                    kind = "stripe"
                else:
                    kind = "body"
                if u == SPAN and kind in ("body", "stripe"):
                    kind = "tip"
                out.append((u, v, kind))
        return out

    WING = wing_cells()
    WX0 = 13

    def wing_block(u, kind, slab_type):
        if kind == "le":
            return ACCENT[0] if u <= SPAN - 2 else st.slab(ACCENT[1], slab_type)   # purpur leading edge
        if kind == "te":
            return st.slab(WHITE[1], slab_type)
        if kind == "tip":
            return st.slab(ACCENT[1], slab_type)
        if kind == "stripe":
            return DARK[0] if u <= 6 else st.slab(DARK[1], slab_type)            # dark spar line
        return HULL if u <= 6 else st.slab(WHITE[1], slab_type)

    def y0(x):
        return int(round(cy(x) - 0.6))

    def attached_wing(side, max_u=None, torn=False):
        """side=+1 south wing, -1 north stub. Root rows get a dark spar layer + fairing stair; the plate steps up
        along x with stairs; TE/tip taper to slabs."""
        root_u = {}
        for u, v, kind in WING:
            if max_u is not None and u > max_u:
                continue
            x, z = WX0 + v, CZ + side * (3 + u)
            y = y0(x)
            if mask[x, y, z]:
                continue
            root_u.setdefault(x, u)
            ru = root_u[x]
            if torn and u == ru + 1:                                        # torn cross-section: spars + bars
                if v % 3 == 0:
                    s.set(x, y, z, DARK[0])
                elif v % 3 == 1:
                    s.set(x, y, z, BARS)
                continue
            blk = wing_block(u, kind, "top")
            if y0(x) > y0(x - 1) and kind in ("le", "body", "stripe") and u <= 6:
                fam = _family_of(blk) or WHITE
                blk = st.stairs(fam[2], "east", "bottom")
            s.set(x, y, z, blk)
            if kind != "te" and u - ru <= 2 and s.is_air(x, y + 1, z):
                if u - ru < 2:
                    s.set(x, y + 1, z, DARK[0])                               # spar layer at the root
                else:
                    s.set(x, y + 1, z, st.stairs(DARK[2], "north" if side > 0 else "south", "bottom"))

    attached_wing(+1)
    tip_x = WX0 + 13
    s.set(tip_x, y0(tip_x), CZ + 3 + SPAN + 1, st.end_rod("south"))          # nav light
    attached_wing(-1, max_u=1, torn=True)
    # torn stub: scorch patch on the flank above the root, cables hanging to the snow, ripped cables sticking out
    for x in range(16, 23):
        for y in ((y0(x) + 1, y0(x) + 2) if 18 <= x <= 20 else (y0(x) + 1,)):
            z = CZ
            while z - 1 >= 0 and mask[x, y, z - 1]:
                z -= 1
            if mask[x, y, z] and rng.random() < 0.85 and _family_of(s.get(x, y, z)) is WHITE:
                recolour(s, [(x, y, z)], SCORCH)
    for x in (19, 22):                                                       # hang from the dark spars (v%3==0)
        y = y0(x) - 1
        while y > G + 1 and s.is_air(x, y, CZ - 4):
            s.set(x, y, CZ - 4, st.chain("y"))
            y -= 1
    for x, n in ((16, 2), (21, 1), (24, 2)):                                 # torn cables sticking out sideways
        for k in range(n):
            if s.is_air(x, y0(x), CZ - 5 - k):
                s.set(x, y0(x), CZ - 5 - k, st.chain("z"))
    # torn-off wing lying north-east, rotated ~15 deg: root sunk 1 into the snow, mid on the surface, tip propped
    # on a drift with a stair ramp; jagged root row, bars protruding
    ox, oz = 26.0, 7.0
    du, dv = (0.26, -0.97), (0.97, 0.26)

    def wpos(u, v):
        return int(round(ox + u * du[0] + v * dv[0])), int(round(oz + u * du[1] + v * dv[1]))

    torn = {}
    for u, v, kind in WING:
        for fu in (0.0, 0.5):
            for fv in (0.0, 0.5):
                x = int(round(ox + (u + fu) * du[0] + (v + fv) * dv[0]))
                z = int(round(oz + (u + fu) * du[1] + (v + fv) * dv[1]))
                torn.setdefault((x, z), (u, v, kind))
    for (x, z), (u, v, kind) in torn.items():
        if not (0 <= x < W and 0 <= z < L):
            continue
        if u <= 1:
            y = G                                                            # root dug into the snow
        elif u >= 6:
            s.set(x, G + 1, z, SNOW)
            y = G + 2
        else:
            y = G + 1
        if u == 0:                                                           # jagged torn root row
            r = v % 4
            if r == 0:
                s.set(x, y, z, DARK[0])
            elif r == 1:
                s.set(x, y, z, BARS)
            elif r == 2:
                s.set(x, y, z, st.slab(DARK[1], "bottom"))
            continue
        s.set(x, y, z, wing_block(u, kind, "bottom"))
        if u == 1 and kind != "te":
            s.set(x, y + 1, z, DARK[0])                                      # spar
        if u == 5 and kind in ("body", "stripe", "le"):
            s.set(x, y + 1, z, st.stairs((_family_of(wing_block(u, kind, "bottom")) or WHITE)[2], "north", "bottom"))
    for v in (4, 10):                                                        # bars protruding from the root
        x, z = wpos(-1, v)
        if s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, BARS)
    for (x, z) in ((int(round(ox + 3 * du[0] + 15 * dv[0] + 1)), int(round(oz + 3 * du[1] + 15 * dv[1] + 1))),
                   (int(round(ox + 7 * du[0] + 12 * dv[0] - 1)), int(round(oz + 7 * du[1] + 12 * dv[1] + 1)))):
        if s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, st.snow_layer(3))

    # ------------------------------------------------------------------ engines: two slim nacelles hung off the flanks
    NX0, NX1 = 26, 34
    for side, burst in ((-1, True), (1, False)):
        nz = CZ + side * 7
        NS = [(NX0, cy(NX0) + 0.6, nz, 1.0, 1.0), (NX1, cy(NX1) + 0.6, nz, 1.0, 1.0)]
        nm = sh.loft(s, NS, HULL, axis="x")
        nsurf = sh.surface_mask(s, nm)
        bevel(s, nm, WHITE, y_min_bottom=G + 1)
        recolour(s, nsurf & (xs == NX0), DARK)                              # intake ring
        recolour(s, nsurf & (xs >= NX0 + 1) & (xs <= NX0 + 2), ACCENT)      # purpur ring behind the intake
        yn = int(round(cy(NX0) + 0.6))
        s.set(NX0, yn, nz, "minecraft:tinted_glass")                        # dark intake mouth
        # nozzle behind the rear ring: dark shroud; intact = 3 sea lanterns behind cyan glass, burst = dead pane
        yc = int(round(cy(NX1 + 1) + 0.6))
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dy or dz:
                    s.set(NX1 + 1, yc + dy, nz + dz, DARK[0])
        s.set(NX1 + 2, yc + 1, nz, st.stairs(DARK[2], "west", "top"))
        s.set(NX1 + 2, yc - 1, nz, st.stairs(DARK[2], "west", "bottom"))
        if not burst:
            for dz in (-1, 0, 1):
                s.set(NX1 + 1, yc, nz + dz, SHIP["engine_core"])
                s.set(NX1 + 2, yc, nz + dz, SHIP["engine_glow"])
            s.set(NX1 + 3, yc, nz, "minecraft:cyan_stained_glass_pane")
        else:
            s.set(NX1 + 1, yc, nz, "minecraft:tinted_glass")
            s.set(NX1 + 2, yc, nz, "minecraft:cyan_stained_glass_pane")
        # pylons: polished deepslate walls bridging the daylight gap between hull and nacelle
        for x in (28, 32):
            y = int(round(cy(x) + 0.6))
            z = CZ
            while abs(z - CZ) < 9:
                if not mask[x, y, z] and not nm[x, y, z] and s.is_air(x, y, z):
                    s.set(x, y, z, "minecraft:polished_deepslate_wall")
                if nm[x, y, z]:
                    break
                z += side
        if burst:
            ncy = np.interp(xs.astype(float), [NX0, NX1], [cy(NX0) + 0.6, cy(NX1) + 0.6])
            recolour(s, nsurf & (xs >= 29) & (xs <= 33) & (ys >= ncy - 0.2), SCORCH)   # scorched half-shell
            sh.fill_mask(s, nm & ~nsurf & (xs >= 28) & (xs <= 33), DARK[0])           # dark innards behind the holes
            y = int(round(cy(31) + 0.6))
            sh.erode(s, 29, y - 1, nz - 1, 33, y + 1, nz + 1, prob=0.4, seed=4, only=["blackstone"])
            s.set(31, y + 1, nz, st.campfire(soul=True))                     # burst casing, blue smoke
            s.set(30, y + 1, nz, st.trapdoor("iron", "east", "bottom", open=True))    # peeled skin panels
            s.set(32, y + 1, nz, st.trapdoor("iron", "west", "bottom", open=True))
            s.set(31, y + 1, nz - side, st.trapdoor("iron", "south" if side < 0 else "north", "bottom", open=True))
            for k in (1, 2):                                                 # cable hanging out of the nacelle belly
                s.set(33, y - 1 - k, nz, st.chain("y"))
            # soot ellipse on the snow below
            for x in range(27, 36):
                for z in range(nz - 3, nz + 4):
                    if ((x - 31) / 4.2) ** 2 + ((z - nz) / 2.6) ** 2 <= 1 and s.get(x, G, z) == SNOW:
                        above = s.get(x, G + 1, z)
                        if above.startswith("minecraft:snow[") or s.is_air(x, G + 1, z):
                            s.set(x, G + 1, z, "air")
                            s.set(x, G, z, "minecraft:black_concrete_powder" if rng.random() < 0.55
                                  else "minecraft:gray_concrete_powder")

    # ------------------------------------------------------------------ tail fin (swept), ventral blade, tail cone
    fin_h = {x: int(0.85 * (x - 25) + 0.5) for x in range(26, 35)}
    for x in range(26, 35):
        T = hull_top(x, CZ)
        h = fin_h[x]
        s.set(x, T, CZ, HULL)                                                # solid root under the fin
        for y in range(T + 1, T + 1 + h):
            top = (y == T + h)
            if x == 34:
                blk = st.log("minecraft:purpur_pillar", "y")                 # lavender rudder
            elif x == 33 and y >= T + h - 1:
                blk = ACCENT[0]
            elif top and fin_h.get(x + 1, 0) > h:
                blk = st.stairs(WHITE[2], "east", "bottom")                  # leading edge ramp
            else:
                blk = HULL
            s.set(x, y, CZ, blk)
    ft = s.top_y(34, CZ)
    s.set(34, ft + 1, CZ, st.lightning_rod("up"))
    s.set(33, s.top_y(33, CZ) + 1, CZ, st.end_rod("up"))
    # ventral blade (1 wide) under the raised tail
    for x in range(30, 34):
        B = hull_bot(x, CZ)
        if x == 30:
            s.set(x, B - 1, CZ, st.stairs(BELLY[2], "east", "top"))
            continue
        s.set(x, B - 1, CZ, BELLY[0])
        if x >= 32:
            s.set(x, B - 2, CZ, BELLY[0] if x == 33 else st.stairs(BELLY[2], "east", "top"))
    s.set(33, hull_bot(33, CZ) - 3, CZ, st.slab(BELLY[1], "top"))
    # icicles hanging from the belly
    for (x, dz) in ((27, -1), (29, 1), (32, -2), (34, 1)):
        B = hull_bot(x, CZ + dz)
        if B < 99 and s.is_air(x, B - 1, CZ + dz):
            s.set(x, B - 1, CZ + dz, st.pointed_dripstone("down", "tip"))
    # tail cone + tail light
    tcy = int(round(cy(34)))
    for dy, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set(35, tcy + dy, CZ + dz, DARK[0] if (dy, dz) == (0, 0) else
              st.stairs(DARK[2], "west", "top" if dy > 0 else "bottom") if dz == 0 else DARK[0])
    s.set(36, tcy, CZ, st.end_rod("east"))
    # flank vents behind the canopy (iron trapdoors flat against the hull)
    for x in (23, 24, 25):
        for side in (-1, 1):
            y = int(round(cy(x) + 0.9))
            z = CZ + side * int(round(rz(x) + 0.5))
            while mask[x, y, z]:
                z += side
            if s.is_air(x, y, z) and mask[x, y, z - side]:
                s.set(x, y, z, st.trapdoor("iron", "south" if side > 0 else "north", "top", open=True))

    # ------------------------------------------------------------------ story props
    # blown-off ejection hatch: a 3x2 slanted panel half sunk in a snow pile, south of the cockpit
    hx, hz = 9, CZ + 6
    for dx in range(3):
        s.set(hx + dx, G + 1, hz, st.stairs(WHITE[2], "south", "bottom"))
        s.set(hx + dx, G + 1, hz + 1, GLASS)
        s.set(hx + dx, G + 2, hz + 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(hx + 1, G + 1, hz + 1, PANE)
    for (dx, dz, n) in ((-1, 0, 3), (-1, 1, 4), (3, 0, 2), (3, 1, 3), (0, 2, 4), (1, 2, 5), (2, 2, 3), (0, -1, 2), (2, -1, 2)):
        if s.is_air(hx + dx, G + 1, hz + dz):
            s.set(hx + dx, G + 1, hz + dz, st.snow_layer(n))
    s.set(hx + 4, G + 1, hz + 2, "minecraft:barrel[facing=east,open=false]")   # dropped supply barrel
    s.set(hx + 4, G + 1, hz - 1, st.slab(DARK[1], "bottom"))
    # distress beacon planted on the way north: dark base sunk in the snow, bars pole, froglight lamp with a red cap
    bx, bz = 9, CZ - 11
    s.set(bx, G, bz, DARK[0])
    s.set(bx, G + 1, bz, DARK[0])
    for (dx, dz, n) in ((1, 0, 3), (-1, 0, 2), (0, 1, 4), (0, -1, 2), (1, 1, 2)):
        if s.is_air(bx + dx, G + 1, bz + dz):
            s.set(bx + dx, G + 1, bz + dz, st.snow_layer(n))
    for y in range(G + 2, G + 4):
        s.set(bx, y, bz, BARS)
    s.set(bx, G + 4, bz, SHIP["light_warm"])
    s.set(bx, G + 5, bz, "minecraft:red_stained_glass")
    s.set(bx, G + 6, bz, st.lightning_rod("up"))
    s.add_sign(bx, G + 1, bz + 1, "minecraft:warped_wall_sign[facing=south]", ["S.O.S.", "FAUCON-3", "pilote vivant", "-> nord"])
    # crystal spike the wing clipped (east of the torn wing), tip snapped off and lying beside it
    cxs, czs = 44, 6
    for y in range(G - 1, G + 5):
        s.set(cxs, y, czs, "minecraft:amethyst_block")
    s.set(cxs, G + 1, czs + 1, "minecraft:amethyst_block")
    s.set(cxs, G + 2, czs + 1, "minecraft:medium_amethyst_bud[facing=up]")
    s.set(cxs - 1, G + 1, czs, "minecraft:amethyst_block")
    s.set(cxs - 1, G + 2, czs, "minecraft:amethyst_cluster[facing=up]")
    s.set(cxs, G + 5, czs, "minecraft:amethyst_cluster[facing=up]")
    s.set(cxs - 1, G + 3, czs, "minecraft:amethyst_cluster[facing=west]")
    s.set(cxs - 3, G + 1, czs + 1, "minecraft:amethyst_block")
    s.set(cxs - 4, G + 1, czs + 1, "minecraft:large_amethyst_bud[facing=up]")
    # last-log sign on the north flank, above the wing stub
    sy = int(round(cy(14))) + 2
    sz = CZ
    while mask[14, sy, sz]:
        sz -= 1
    s.add_sign(14, sy, sz, "minecraft:warped_wall_sign[facing=north]", ["FAUCON-3", "ejection OK", "cap nord", "balise posee"])

    # ------------------------------------------------------------------ debris: a cone behind the ship along the furrow
    def free_flat(cells):
        tys = set()
        for (x, z) in cells:
            if not (0 <= x < W and 0 <= z < L):
                return None
            ty = s.top_y(x, z)
            b = s.get(x, ty, z)
            if not (b == SNOW or b.endswith("_concrete_powder") or b.startswith("minecraft:snow[")):
                return None
            if b.startswith("minecraft:snow["):
                ty -= 1
            tys.add(ty)
        return tys.pop() if len(tys) == 1 else None

    def clear_layers(cells):
        for (x, z) in cells:
            if s.get(x, s.top_y(x, z), z).startswith("minecraft:snow["):
                s.set(x, s.top_y(x, z), z, "air")

    def panel(x, z, kind):
        cells = [(x, z), (x + 1, z)] if kind in ("plate", "stair") else [(x, z), (x, z + 1)]
        ty = free_flat(cells)
        if ty is None:
            return False
        clear_layers(cells)
        y = ty + 1
        if kind == "plate":
            s.set(x, y, z, HULL); s.set(x + 1, y, z, HULL)
            s.set(x, y + 1, z, st.trapdoor("iron", "north", "bottom", open=False))
        elif kind == "stair":
            s.set(x, y, z, st.stairs(WHITE[2], rng.choice(["north", "south", "east", "west"]), "bottom"))
            s.set(x + 1, y, z, st.slab(DARK[1], "bottom"))
        elif kind == "stripe":
            s.set(x, y, z, HULL)
            s.set(x, y, z + 1, st.slab(ACCENT[1], "bottom"))
            s.set(x, y + 1, z, st.trapdoor("iron", "west", "bottom", open=True))
        else:  # frame
            s.set(x, y, z, SHIP["damage_fill"])
            s.set(x, y, z + 1, BARS)
        return True

    kinds = ["plate", "stair", "stripe", "frame", "plate", "stair", "plate", "stripe"]
    placed, tries = 0, 0
    while placed < 7 and tries < 300:
        tries += 1
        x = 27 + int(rng.random() ** 1.6 * 17)
        dz = rng.randint(-5, 5)
        if abs(dz) <= 2 and rng.random() < 0.5:
            continue
        if panel(x, CZ + dz, kinds[placed % len(kinds)]):
            placed += 1
    # trail between the torn stub and the loose wing (north-east)
    for (x, z, k) in ((15, CZ - 8, "frame"), (18, CZ - 9, "plate"), (21, CZ - 8, "stair"), (24, CZ - 7, "stripe"),
                      (23, CZ - 10, "frame")):
        panel(x, z, k)

    # ------------------------------------------------------------------ texture, weathering, footprints
    sh.texturize(s, HULL, MIX_SKIN, seed=5)
    sh.texturize(s, SCORCH[0], MIX_SCORCH, seed=9)
    sh.snow_cover(s, 0, CZ - 10, 11, CZ + 10, y_min=G + 1, prob=0.35, seed=2,
                  skip=["glass", "purpur", "lamp", "iron", "cyan", "lantern", "detector", "observer", "deepslate",
                        "blue_ice", "packed_ice"])
    for i in range(0, 14):                                                   # footprints leaving north
        x, z = 12 + (i % 3) - 1, CZ - 6 - i
        if z < 0:
            break
        ty = s.top_y(x, z)
        b = s.get(x, ty, z)
        if b.startswith("minecraft:snow["):
            s.set(x, ty, z, "air")
        elif b == SNOW:
            s.set(x, ty, z, PACKED)
    return {"ship_crash_scout": s.cropped(pad=1)}

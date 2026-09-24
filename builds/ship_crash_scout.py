"""'Le Chasseur' - a sleek single-seat interceptor that nose-dived into a snow bank.

Story: it came sliding in from the east, gouged a furrow, clipped a crystal spike that tore the north wing off,
then buried its nose in a drift. The pilot blew the canopy hatch (it lies in the snow south of the cockpit),
grabbed what he could, planted a beacon and walked north. The north engine is still smoking blue, both nozzles
keep a dying cyan glow.

Layout (x = east, z = south): nose at low x (buried), tail at high x (raised ~6 blocks). Hull lofted along x with a
rising centreline so the whole ship is tilted. Attached delta wing on the south side, torn stub on the north,
the torn wing lying ~10 blocks north-east in the snow.

Build order matters: hull loft -> bevel pass (stairs/slabs on every top / belly edge) -> zone recolour (belly,
keel, rib rings, cheat line) -> cockpit -> canopy -> wings -> nacelles -> fin -> props -> texture -> snow.
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
MIX_SKIN = [("minecraft:quartz_block", 7), ("minecraft:smooth_quartz", 2), ("minecraft:calcite", 1)]
GLASS = SHIP["glass"]
PANE = SHIP["glass_pane"]
SNOW = GROUND["snow"]
PACKED = "minecraft:white_concrete_powder"
BARS = "minecraft:iron_bars"

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
    """Round the top and belly edges of a solid `mask`: wherever a column's top is higher than a neighbour's the top
    block becomes a bottom-half stair (tall side toward the higher neighbour) or a bottom slab; the mirror on the
    underside with top-half stairs / top slabs. Only touches full blocks of family `fam`."""
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
                s.set(x, T, z, pick(lows, "bottom"))
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
    for x in range(24, W):
        depth = 2 if x <= 38 else 1
        for z in range(CZ - 5, CZ + 6):
            d = abs(z - CZ)
            dep = depth if d <= 1 else (max(1, depth - 1) if d == 2 else 0)
            if dep:
                for y in range(G - dep + 1, G + 1):
                    s.set(x, y, z, "air")
                s.set(x, G - dep, z, PACKED if rng.random() < 0.8 else SNOW)
            elif d == 3 and rng.random() < 0.85:
                s.set(x, G + 1, z, SNOW)                                   # pushed-up rim
            elif d == 4 and rng.random() < 0.7:
                s.set(x, G + 1, z, st.snow_layer(rng.randint(3, 6)))
            elif d == 5 and rng.random() < 0.35:
                s.set(x, G + 1, z, st.snow_layer(rng.randint(1, 3)))
    # snow bank the nose dived into: a mound, higher in front (west) of the nose
    for x in range(0, 15):
        for z in range(CZ - 9, CZ + 10):
            nx, nz = (x - 3) / 9.0, (z - CZ) / 7.5
            f = 1 - nx * nx - nz * nz
            if f <= 0:
                continue
            n = sh.value_noise2(x, z, 21, 5.0)
            h = 3.0 * f * (0.6 + 0.8 * n)
            hi = int(h)
            for y in range(G + 1, G + 1 + hi):
                s.set(x, y, z, SNOW)
            frac = h - hi
            if frac > 0.15 and s.is_air(x, G + 1 + hi, z):
                s.set(x, G + 1 + hi, z, st.snow_layer(max(1, min(7, int(frac * 8)))))

    # ------------------------------------------------------------------ hull: loft, bevel, zones
    mask = sh.loft(s, SECS, HULL, axis="x")
    surf = sh.surface_mask(s, mask)
    bevel(s, mask, WHITE, y_min_bottom=G + 1)
    recolour(s, mask & (ys <= CY - 1.4), BELLY)                              # dark belly
    recolour(s, surf & (ys <= CY - 1.6) & (np.abs(zs - CZ) <= 0.6), DARK)    # keel line
    stripe = []                                                              # lavender cheat line: one flank cell per side
    for x in range(6, 32):
        y = int(round(cy(x) + 1.5))
        for side in (-1, 1):
            z = CZ + side
            while mask[x, y, z + side]:
                z += side
            if mask[x, y, z] and mask[x, y + 1, z] and abs(z - CZ) >= 2:
                stripe.append((x, y, z))
    recolour(s, stripe, ACCENT)
    RINGS = (9, 21, 28)
    recolour(s, surf & np.isin(xs, RINGS), DARK)                             # rib rings / canopy frames

    # ------------------------------------------------------------------ cockpit interior (x 9..22)
    inner = sh.loft_mask(s, SECS, "x", shrink=1.0) & (xs >= 9) & (xs <= 22)
    floor_y = {x: int(math.floor(cy(x) - 1.2)) for x in range(9, 23)}
    fl = np.array([floor_y.get(x, 99) for x in range(W)])[:, None, None]
    s.data[inner & (ys > fl)] = 0
    # hull breach on the north flank at the nose: torn open, exposed ribs, one chain
    bx, by, bz = 10, cy(10) + 0.2, CZ - rz(10) - 0.3
    br = sh._mask_ellipsoid(s, bx, by, bz, 2.2, 1.7, 2.5)
    rim = sh.surface_mask(s, mask & ~br) & br            # hull cells left on the breach edge
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

    # ------------------------------------------------------------------ canopy (x 10..20), cracked, hatch blown off
    canopy = surf & (xs >= 10) & (xs <= 20) & (ys >= CY + 0.9) & (np.abs(zs - CZ) <= 2.2)
    for (x, y, z) in np.argwhere(canopy):
        x, y, z = int(x), int(y), int(z)
        if 13 <= x <= 15 and abs(z - CZ) <= 1:
            s.set(x, y, z, "air")                                            # hatch gone
        elif rng.random() < 0.15:
            s.set(x, y, z, PANE)                                             # cracked pane
        else:
            s.set(x, y, z, GLASS)
    # make sure the interior is visible: a hull block right under canopy glass with air below it becomes glass
    for (x, y, z) in np.argwhere(canopy):
        x, y, z = int(x), int(y), int(z)
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
            return DARK[0] if u <= SPAN - 2 else st.slab(DARK[1], slab_type)
        if kind == "te":
            return st.slab(WHITE[1], slab_type)
        if kind == "tip":
            return st.slab(ACCENT[1], slab_type)
        if kind == "stripe":
            return ACCENT[0] if u <= 6 else st.slab(ACCENT[1], slab_type)
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
    for (x, z) in ((18, CZ - 4), (23, CZ - 4)):                             # cables hanging from the stub to the snow
        y = y0(x) - 1
        while y > G + 1 and s.is_air(x, y, z):
            s.set(x, y, z, st.chain("y"))
            y -= 1
    # torn-off wing lying north-east, rotated ~15 deg, tip propped on a drift; root row torn
    ox, oz = 26.0, 7.0
    du, dv = (0.26, -0.97), (0.97, 0.26)
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
        y = G + 1
        if u >= 6:
            s.set(x, G + 1, z, SNOW)
            y = G + 2
        if u == 0:
            if v % 3 == 0:
                s.set(x, y, z, DARK[0])
            elif v % 3 == 1:
                s.set(x, y, z, BARS)
            continue
        s.set(x, y, z, wing_block(u, kind, "bottom"))
        if u == 1 and kind != "te":
            s.set(x, y + 1, z, DARK[0])
    for (x, z) in ((int(round(ox + 3 * du[0] + 15 * dv[0] + 1)), int(round(oz + 3 * du[1] + 15 * dv[1] + 1))),
                   (int(round(ox + 7 * du[0] + 12 * dv[0] - 1)), int(round(oz + 7 * du[1] + 12 * dv[1] + 1)))):
        if s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, st.snow_layer(3))

    # ------------------------------------------------------------------ engines: two slim nacelles hung off the flanks
    NX0, NX1 = 26, 34
    for side, smoking in ((-1, True), (1, False)):
        nz = CZ + side * 7
        NS = [(NX0, cy(NX0) + 0.6, nz, 1.0, 1.0), (NX1, cy(NX1) + 0.6, nz, 1.0, 1.0)]
        nm = sh.loft(s, NS, HULL, axis="x")
        nsurf = sh.surface_mask(s, nm)
        bevel(s, nm, WHITE, y_min_bottom=G + 1)
        recolour(s, nsurf & (xs == NX0), DARK)                              # intake ring
        yn = int(round(cy(NX0) + 0.6))
        s.set(NX0, yn, nz, "minecraft:tinted_glass")                        # dark intake mouth
        # nozzle cone behind the rear ring: dark shroud, sea-lantern core, cyan glass, dying glow pane
        yc = int(round(cy(NX1 + 1) + 0.6))
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dy or dz:
                    s.set(NX1 + 1, yc + dy, nz + dz, DARK[0])
        s.set(NX1 + 1, yc, nz, SHIP["engine_core"])
        s.set(NX1 + 2, yc + 1, nz, st.stairs(DARK[2], "west", "top"))
        s.set(NX1 + 2, yc - 1, nz, st.stairs(DARK[2], "west", "bottom"))
        s.set(NX1 + 2, yc, nz, SHIP["engine_glow"])
        s.set(NX1 + 3, yc, nz, "minecraft:cyan_stained_glass_pane")
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
        if smoking:
            ncy = np.interp(xs.astype(float), [NX0, NX1], [cy(NX0) + 0.6, cy(NX1) + 0.6])
            recolour(s, nsurf & (xs >= 29) & (xs <= 33) & (ys >= ncy - 0.2), SCORCH)   # scorched half-shell
            y = int(round(cy(31) + 0.6))
            s.set(31, y + 1, nz, st.campfire(soul=True))                     # burst casing, blue smoke
            s.set(30, y + 1, nz, BARS)
            s.set(32, y + 1, nz, BARS)
            s.set(31, y + 1, nz - side, "air")
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
    def hull_top(x, z):
        col = np.nonzero(mask[x, :, z])[0]
        return int(col.max()) if len(col) else -1

    def hull_bot(x, z):
        col = np.nonzero(mask[x, :, z])[0]
        return int(col.min()) if len(col) else 99

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
    # distress beacon planted on the way north: iron pole, 2x2 froglight head in a red pane cage
    bx, bz = 9, CZ - 11
    ty = G
    s.set(bx, ty + 1, bz, "minecraft:iron_block")
    s.set(bx + 1, ty + 1, bz, st.slab(DARK[1], "bottom"))
    s.set(bx, ty + 1, bz + 1, st.slab(DARK[1], "bottom"))
    for y in range(ty + 2, ty + 5):
        s.set(bx, y, bz, BARS)
    for dx in (0, 1):
        for dz in (0, 1):
            s.set(bx + dx, ty + 5, bz + dz, SHIP["light_warm"])
    for dx in (0, 1):
        s.set(bx + dx, ty + 5, bz - 1, "minecraft:red_stained_glass_pane")
        s.set(bx + dx, ty + 5, bz + 2, "minecraft:red_stained_glass_pane")
    for dz in (0, 1):
        s.set(bx - 1, ty + 5, bz + dz, "minecraft:red_stained_glass_pane")
        s.set(bx + 2, ty + 5, bz + dz, "minecraft:red_stained_glass_pane")
    s.set(bx, ty + 6, bz, st.lightning_rod("up"))
    s.set(bx + 1, ty + 6, bz + 1, "minecraft:red_stained_glass_pane")
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
    # callsign sign on the north flank, above the wing stub
    sy = int(round(cy(14))) + 2
    sz = CZ
    while mask[14, sy, sz]:
        sz -= 1
    s.add_sign(14, sy, sz, "minecraft:warped_wall_sign[facing=north]", ["CHASSEUR", "FAUCON-3", "pilote: 1", "sortie 14"])

    # ------------------------------------------------------------------ debris: a cone behind the ship along the furrow
    def free_flat(cells):
        tys = set()
        for (x, z) in cells:
            if not (0 <= x < W and 0 <= z < L):
                return None
            ty = s.top_y(x, z)
            b = s.get(x, ty, z)
            if not (b == SNOW or b == PACKED or b.startswith("minecraft:snow[")):
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
    # small cluster at the wing-break root (north)
    for (x, z, k) in ((15, CZ - 8, "frame"), (18, CZ - 9, "plate"), (21, CZ - 8, "stair")):
        panel(x, z, k)

    # ------------------------------------------------------------------ texture, weathering, footprints
    sh.texturize(s, HULL, MIX_SKIN, seed=5)
    sh.texturize(s, SCORCH[0], MIX_SCORCH, seed=9)
    sh.snow_cover(s, 0, CZ - 10, 13, CZ + 10, y_min=G + 1, prob=0.5, seed=2,
                  skip=["glass", "purpur", "lamp", "iron", "cyan", "lantern", "detector", "observer", "deepslate"])
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

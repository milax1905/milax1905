"""Le Cargo: a big interstellar freighter that crash-landed in the snow and broke in two.

Main hull (nose west, plowed into the snow) lofted from elliptical sections; the loft swells into a raised "head"
at the front that holds the cockpit behind a stepped, raked windscreen. Swept wings with engine nacelles (the south
one sheared off and lying in the snow), cargo bay mid-ship with a big open breach on the south flank showing the
stacked containers, crew quarters at the severed end. The engine/tail section lies ~14 blocks behind, yawed
sideways, with a swept fin plate and three nozzles still glowing cyan and smoking. Long scorched furrow with dark
rims and skid gouges running to the east edge, dark debris trail, snow drift on the north (leeward) flank, lit
furnished interior, loot, French signs, lavender (purpur / froglight / amethyst) accents of the Neige world.
"""
import math
import random

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_LIGHT_GRAY, MIX_DARK, MIX_SCORCH

W, H, L, G = 108, 32, 58, 5
AIR = "minecraft:air"

# (x, cy, cz, ry, rz) - body of the main hull: used for colour zones, belt line, centre line
MAIN = [
    (6, 8.0, 21.0, 1.5, 1.5),
    (12, 8.8, 21.5, 3.0, 4.0),
    (20, 9.8, 22.0, 5.0, 6.5),
    (30, 10.5, 23.0, 7.0, 9.0),
    (52, 10.5, 24.5, 7.0, 9.0),
    (60, 11.0, 25.0, 6.5, 8.0),
    (66, 11.0, 25.5, 6.0, 7.0),
]
# geometry of the main hull: the body plus a raised "head" (cy and ry both raised -> the keel line is unchanged,
# the top swells up ~4 blocks between x=22 and x=37 to house the cockpit)
HULL = [
    (6, 8.0, 21.0, 1.5, 1.5),
    (12, 8.8, 21.5, 3.0, 4.0),
    (20, 9.8, 22.0, 5.0, 6.5),
    (22, 10.8, 22.2, 6.5, 7.2),
    (25, 12.0, 22.5, 8.5, 8.2),
    (33, 12.5, 23.1, 9.0, 9.0),
    (38, 10.5, 23.4, 7.0, 9.0),
    (52, 10.5, 24.5, 7.0, 9.0),
    (60, 11.0, 25.0, 6.5, 8.0),
    (66, 11.0, 25.5, 6.0, 7.0),
]
# severed engine section: yawed (cz drifts) and 14 blocks behind, keel down in the furrow
TAIL = [
    (80, 10.5, 30.0, 6.0, 7.0),
    (88, 10.5, 32.5, 6.0, 7.0),
    (93, 11.0, 34.0, 5.5, 6.0),
]

WHITE, LGRAY, DARK = SHIP["hull_light"], SHIP["hull"], SHIP["hull_dark"]
UNDER = SHIP["hull_underside"]
IRON = SHIP["frame"]
GLASS = SHIP["glass"]
LANTERN = SHIP["light"]
FROG = SHIP["light_warm"]
PDS = "minecraft:polished_deepslate"
PURPUR = "minecraft:purpur_block"
PGLASS = "minecraft:purple_stained_glass"
BASALT_P = "minecraft:polished_basalt"
MIX_HULL_WHITE = [("minecraft:white_concrete", 8), ("minecraft:quartz_block", 2)]


def _interp(secs, x, col):
    xs = [p[0] for p in secs]
    return float(np.interp(x, xs, [p[col] for p in secs]))


def cy_of(secs, x):
    return _interp(secs, x, 1)


def cz_of(secs, x):
    return _interp(secs, x, 2)


def ry_of(secs, x):
    return _interp(secs, x, 3)


def rz_of(secs, x):
    return _interp(secs, x, 4)


def zone(secs, x, y):
    """Colour zone of a hull block: 'white' (upper), 'gray' (lower flank), 'dark' (keel / underside)."""
    cy = cy_of(secs, x)
    if y >= cy - 0.5:
        return "white"
    if y >= cy - 3.5:
        return "gray"
    return "dark"


ZONE_BLOCK = {"white": WHITE, "gray": LGRAY, "dark": UNDER}
ZONE_STAIR = {"white": "quartz", "gray": "polished_andesite", "dark": "deepslate_tile"}


def paint_shell(s, secs, outer, x_lo, x_hi):
    """Colour the outer layer of a hull by zone."""
    for x in range(x_lo, x_hi + 1):
        for y in range(H):
            for z in range(L):
                if outer[x, y, z]:
                    s.set(x, y, z, ZONE_BLOCK[zone(secs, x, y)])


def bevel_hull(s, outer, secs, x_lo, x_hi, skip=None):
    """Fill the staircase steps of the lofted ellipse with stairs so the hull reads rounded."""
    for x in range(x_lo, x_hi + 1):
        for y in range(G + 1, H - 1):
            for z in range(1, L - 1):
                if outer[x, y, z] or not s.is_air(x, y, z):
                    continue
                if skip and skip(x, y, z):
                    continue
                below, above = outer[x, y - 1, z], outer[x, y + 1, z]
                if below == above:
                    continue
                n, so = outer[x, y, z - 1], outer[x, y, z + 1]
                if n and so:
                    continue
                sides = []
                if n:
                    sides.append("north")
                if so:
                    sides.append("south")
                if not sides:
                    if outer[x - 1, y, z] and not outer[x + 1, y, z]:
                        sides.append("west")
                    elif outer[x + 1, y, z] and not outer[x - 1, y, z]:
                        sides.append("east")
                if len(sides) != 1:
                    continue
                half = "bottom" if below else "top"
                s.set(x, y, z, st.stairs(ZONE_STAIR[zone(secs, x, y)], sides[0], half))


def container(s, x1, y1, z1, length, color, doors="west"):
    """A 3-high cargo crate: coloured concrete with dark corner frames and an iron-trapdoor door panel."""
    x2, z2 = x1 + length - 1, z1 + 2
    sh.box(s, x1, y1, z1, x2, y1 + 2, z2, color)
    for (x, z) in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        for y in (y1, y1 + 2):
            s.set(x, y, z, PDS)
    zm, xm = (z1 + z2) // 2, (x1 + x2) // 2
    if doors == "west":
        s.set(x1 - 1, y1 + 1, zm, st.trapdoor("iron", "east", "bottom", open=True))
    elif doors == "east":
        s.set(x2 + 1, y1 + 1, zm, st.trapdoor("iron", "west", "bottom", open=True))
    elif doors == "south":
        s.set(xm, y1 + 1, z2 + 1, st.trapdoor("iron", "north", "bottom", open=True))
        s.set(xm + 1, y1 + 1, z2 + 1, st.trapdoor("iron", "north", "bottom", open=True))
    elif doors == "north":
        s.set(xm, y1 + 1, z1 - 1, st.trapdoor("iron", "south", "bottom", open=True))


def ceiling_light(s, x, z, block=LANTERN, y_from=8):
    """Set a light INTO the ceiling above (x, z): replaces the first solid block above y_from."""
    for y in range(y_from, H):
        if not s.is_air(x, y, z):
            s.set(x, y, z, block)
            return


def first_solid_z(s, mask, x, y, from_south):
    rng_ = range(L - 1, -1, -1) if from_south else range(L)
    for z in rng_:
        if mask[x, y, z]:
            return z
    return None


def first_solid_x(mask, y, z, x_lo, x_hi):
    for x in range(x_lo, x_hi + 1):
        if mask[x, y, z]:
            return x
    return None


def wing(s, secs, x1, x2, side, span, y_root, dead=False):
    """Swept wing plate attached to the hull flank (side=-1 north, +1 south), engine nacelle at the tip."""
    tip_z = None
    for k in range(span):
        xa = x1 + int(k * 0.30)
        xb = x2 - int(k * 0.55)
        y = y_root + (k // 6)
        for x in range(xa, xb + 1):
            z = int(round(cz_of(secs, x) + side * (rz_of(secs, x) + 0.5 + k)))
            blk = DARK if x == xa else (LGRAY if k < 2 else WHITE)
            s.set(x, y, z, blk)
            if x == xb:
                s.set(x + 1, y, z, st.slab("smooth_quartz", "bottom"))   # thin trailing edge
            if k < 3:
                s.set(x, y - 1, z, PDS)                                    # wing root fairing
                s.set(x, y + 1, z, st.slab("polished_deepslate", "bottom") if k < 2 else st.slab("smooth_quartz", "bottom"))
            if k == span - 1:
                tip_z = z
        if 2 <= k < span - 3:                                              # one dark panel stripe
            xm = (xa + xb) // 2
            z = int(round(cz_of(secs, xm) + side * (rz_of(secs, xm) + 0.5 + k)))
            s.set(xm, y, z, DARK)
    # nacelle at the tip: cylinder along x, dark rings, lavender band, glowing cyan exhaust, tinted intake
    k = span - 2
    xa = x1 + int(k * 0.30)
    nx1 = xa - 2
    nz = int(round(cz_of(secs, xa) + side * (rz_of(secs, xa) + 0.5 + k)))
    ny = y_root + (k // 6)
    sh.cylinder(s, nx1, ny, nz, 2.2, 11, WHITE, axis="x")
    sh.cylinder(s, nx1, ny, nz, 2.2, 0, PDS, axis="x")
    sh.cylinder(s, nx1 + 3, ny, nz, 2.2, 0, PURPUR, axis="x")
    sh.cylinder(s, nx1 + 6, ny, nz, 2.2, 0, PDS, axis="x")
    sh.cylinder(s, nx1 + 11, ny, nz, 2.4, 0, PDS, axis="x")
    sh.cylinder(s, nx1, ny, nz, 1.3, 0, "minecraft:tinted_glass", axis="x")
    sh.cylinder(s, nx1 + 11, ny, nz, 1.4, 0, SHIP["engine_glow"] if not dead else SHIP["scorch"], axis="x")
    sh.cylinder(s, nx1 + 10, ny, nz, 1.0, 0, LANTERN if not dead else SHIP["scorch"], axis="x")
    s.set(nx1 + 12, ny, nz, st.campfire(soul=True))
    for x in range(nx1 + 1, nx1 + 11):                                     # dark keel line under the nacelle
        s.set(x, ny - 2, nz, UNDER)
    for x in range(nx1 + 1, nx1 + 11, 3):
        s.set(x, ny + 2, nz, st.trapdoor("iron", "north", "top", open=False))
    return tip_z


def furrow_center(x):
    """Centre line of the skid furrow: the body's centre line, then drifting south with the yawed tail."""
    if x <= 66:
        return cz_of(MAIN, max(x, 6))
    return cz_of(MAIN, 66) + (x - 66) * 0.30


def furrow_half(x):
    return 9.5 if x <= 60 else max(4.5, 9.5 - (x - 60) * 0.10)


def build():
    s = Schematic(W, H, L, ground=G)
    rng = random.Random(7)
    xs, ys, zs = np.indices((W, H, L))

    # ------------------------------------------------------------------ ground, furrow, crater
    sh.ground_slab(s, G, GROUND["snow"], depth=4)
    for x in range(4, W):                                   # skid furrow along the ship axis, east = where it came from
        czt = furrow_center(x)
        half = furrow_half(x)
        for z in range(L):
            d = abs(z - czt) / half
            n = sh.value_noise2(x, z, 21, 5.0)
            if d <= 0.85 + 0.25 * n:
                dep = 2 if d < 0.6 else 1
                for y in range(G - dep + 1, G + 1):
                    s.set(x, y, z, AIR)
                n2 = sh.value_noise2(x, z, 27, 3.5)
                floor = SHIP["scorch"] if n2 < 0.72 else ("minecraft:coal_block" if n2 < 0.86 else "minecraft:basalt")
                s.set(x, G - dep, z, floor)
            elif d <= 1.22 + 0.2 * n and x >= 62:           # plowed rim (trodden snow + some tuff), mostly 1 high
                if sh.value_noise2(x, z, 23, 3.0) < 0.42:
                    continue
                h = 1 + (1 if n > 0.72 and d < 1.1 else 0)
                for y in range(G + 1, G + 1 + h):
                    n3 = sh.value_noise2(x + y * 7, z, 29, 3.0)
                    blk = "minecraft:tuff" if n3 > 0.62 else ("minecraft:white_concrete_powder" if n3 > 0.28 else GROUND["snow"])
                    s.set(x, y, z, blk)
    for (z0, z1) in ((-1.0, -6.0), (0.5, -2.0), (-0.5, 3.0), (1.5, 6.5)):   # skid gouges diverging from the centre
        x0, x1 = 68, W - 1
        for x in range(x0, x1 + 1):
            t = (x - x0) / (x1 - x0)
            z = int(round(furrow_center(x) + z0 + (z1 - z0) * t))
            if not (0 < z < L):
                continue
            ty = s.top_y(x, z)
            if ty > G:
                continue
            b = s.get(x, ty, z)
            s.set(x, ty, z, "minecraft:coal_block" if ("blackstone" in b or "basalt" in b or "coal" in b) else SHIP["scorch"])
    sh.crater(s, 14, 21.5, 11, G, SHIP["scorch"], GROUND["snow"], GROUND["snow"], depth=2, rim_height=2, seed=9)
    for x in range(0, 9):                                   # bow wave of snow pushed ahead of the nose
        for z in range(13, 31):
            n = sh.value_noise2(x, z, 4, 4.0)
            h = int(round((3.5 - abs(z - 21.5) * 0.33 - max(0, 5 - x) * 0.5) * (0.7 + 0.6 * n)))
            for y in range(G + 1, G + 1 + h):
                s.set(x, y, z, GROUND["snow"])

    # ------------------------------------------------------------------ main hull
    outer = sh.loft_mask(s, HULL, "x")
    inner1 = sh.loft_mask(s, HULL, "x", shrink=1.0)
    inner2 = sh.loft_mask(s, HULL, "x", shrink=2.0)
    shell_out = outer & ~inner1
    shell_in = inner1 & ~inner2
    sh.fill_mask(s, shell_out, WHITE)
    sh.fill_mask(s, shell_in, LGRAY)
    paint_shell(s, MAIN, shell_out, 6, 66)
    cav = inner2 & (xs >= 20) & (ys >= 7)
    sh.fill_mask(s, cav, AIR)
    sh.fill_mask(s, inner2 & (xs >= 20) & (ys < 7), DARK)
    sh.fill_mask(s, inner2 & (xs == 6), PDS)
    sh.fill_mask(s, inner2 & (xs >= 20) & (ys == 6), PDS)
    sh.fill_mask(s, inner2 & (xs < 20), LGRAY)
    # the head is solid above the corridor (equipment deck) except for the cockpit cavity
    sh.fill_mask(s, inner2 & (xs >= 20) & (xs <= 38) & (ys >= 10), LGRAY)
    ckz = int(round(cz_of(MAIN, 27)))
    cockpit = inner2 & (xs >= 22) & (xs <= 31) & (np.abs(zs - ckz) <= 5)
    sh.fill_mask(s, cockpit & (ys >= 15) & (ys <= 18), AIR)
    sh.fill_mask(s, cockpit & (ys == 14), PDS)

    # belt line (dark, 1 row at the widest point), lavender stripe under it, window strip above it, ribs
    for x in range(14, 67):
        cy, cz = cy_of(MAIN, x), cz_of(MAIN, x)
        yb = int(round(cy - 0.5))
        yw = yb + 3
        for z in range(L):
            if shell_out[x, yb, z] and abs(z - cz) > 2:
                s.set(x, yb, z, DARK)
            if 22 <= x <= 62 and shell_out[x, yb - 1, z] and abs(z - cz) > 4 and not (34 <= x <= 52 and z > cz):
                s.set(x, yb - 1, z, PURPUR)
            if 22 <= x <= 62 and abs(z - cz) >= 5:
                for lay in (shell_out, shell_in):
                    if lay[x, yw, z]:
                        s.set(x, yw, z, IRON if x % 5 == 0 else (PGLASS if x % 5 == 2 else GLASS))
    for xr in (18, 27, 37, 52, 60):
        m = shell_out & (xs == xr)
        sh.fill_mask(s, m, PDS)
        cy = cy_of(MAIN, xr)
        for z in range(L):
            for y in range(H):
                if m[xr, y, z] and abs(y - cy) < 1.5:
                    s.set(xr, y, z, IRON)
    for x in list(range(14, 20)) + list(range(39, 66)):     # dorsal spine along the top ridge (not over the head)
        z = int(round(cz_of(MAIN, x)))
        ty = s.top_y(x, z)
        if ty > G:
            s.set(x, ty, z, DARK)
            s.set(x, ty + 1, z, st.slab("polished_deepslate"))

    # ------------------------------------------------------------------ cockpit windows in the head
    for x in range(19, 27):                                  # stepped raked windscreen (follows the loft's front slope)
        for y in range(14, 22):
            for z in range(ckz - 4, ckz + 5):
                if shell_out[x, y, z] or shell_in[x, y, z]:
                    s.set(x, y, z, IRON if z == ckz else GLASS)
    for x in range(26, 31):                                  # side windows of the cockpit
        for y in (16, 17):
            for z in range(L):
                if abs(z - ckz) >= 5 and (shell_out[x, y, z] or shell_in[x, y, z]):
                    s.set(x, y, z, GLASS if x != 28 else PGLASS)
    for dz in (-3, 0, 3):                                    # landing lights under the windscreen
        for y in (13,):
            x = first_solid_x(outer, y, ckz + dz, 14, 26)
            if x is not None:
                s.set(x, y, ckz + dz, FROG)

    skip_bevel = lambda x, y, z: ((34 <= x <= 52 and z > cz_of(MAIN, x) + 3) or x >= 63
                                  or (19 <= x <= 27 and abs(z - ckz) <= 4 and y >= 14))
    bevel_hull(s, outer, MAIN, 6, 66, skip=skip_bevel)

    # ------------------------------------------------------------------ wings (north intact, south sheared off)
    y_wing = int(cy_of(MAIN, 54))                           # 10
    wing(s, MAIN, 46, 62, -1, 13, y_wing)
    for k in range(0, 3):                                   # south stump, torn
        for x in range(46 + int(k * 0.3), 62 - int(k * 0.55) + 1):
            z = int(round(cz_of(MAIN, x) + rz_of(MAIN, x) + 0.5 + k))
            blk = DARK if x == 46 else (LGRAY if k < 2 else SHIP["damage_fill"])
            if k == 2 and rng.random() < 0.5:
                continue
            s.set(x, y_wing, z, blk)
            if k < 2:
                s.set(x, y_wing - 1, z, PDS)
                s.set(x, y_wing + 1, z, st.slab("polished_deepslate", "bottom"))
    for x in (48, 53, 58):
        z = int(round(cz_of(MAIN, x) + rz_of(MAIN, x) + 3.5))
        s.set(x, y_wing, z, IRON)
        s.set(x, y_wing, z + 1, IRON)
    # the sheared wing lying in the snow south of the wreck (rotated: drawn along z), nacelle dead & smoking
    sh.ground_disc(s, 66, 46, 8, G, SHIP["scorch"], None, seed=15, noise=0.4, depth=1)
    for k in range(12):
        za = 40 + int(k * 0.30)
        zb = 54 - int(k * 0.55)
        x = 58 + k
        y = G + 1 + (k // 5)
        for z in range(za, zb + 1):
            s.set(x, y, z, DARK if z == za else (SHIP["damage_fill"] if k < 2 and rng.random() < 0.5 else WHITE))
            if z == zb:
                s.set(x, y, z + 1, st.slab("smooth_quartz", "bottom"))
        if 2 <= k < 9:
            s.set(x, y, (za + zb) // 2, DARK)
    sh.cylinder(s, 70, G + 3, 43, 2.2, 9, WHITE, axis="z")
    sh.cylinder(s, 70, G + 3, 43, 2.2, 0, PDS, axis="z")
    sh.cylinder(s, 70, G + 3, 46, 2.2, 0, PURPUR, axis="z")
    sh.cylinder(s, 70, G + 3, 52, 2.4, 0, PDS, axis="z")
    sh.cylinder(s, 70, G + 3, 52, 1.4, 0, SHIP["scorch"], axis="z")
    sh.cylinder(s, 70, G + 3, 43, 1.3, 0, "minecraft:tinted_glass", axis="z")
    s.set(70, G + 5, 48, st.campfire(soul=True))
    s.set(70, G + 6, 49, st.slab("polished_deepslate", "bottom"))
    for z in range(44, 52):
        s.set(70, G + 1, z, UNDER)
        s.set(69, G + 1, z, st.stairs("deepslate_tile", "east", "top")) if s.is_air(69, G + 1, z) else None
        s.set(71, G + 1, z, st.stairs("deepslate_tile", "west", "top")) if s.is_air(71, G + 1, z) else None

    # ------------------------------------------------------------------ cockpit interior (inside the lofted head)
    fl = 14
    cons_x = {}
    for z in range(ckz - 4, ckz + 5):                            # curved console row hugging the windscreen
        for x in range(22, 30):
            if s.is_air(x, fl + 1, z) and not s.is_air(x, fl, z):
                cons_x[z] = x
                break
    for z, x in cons_x.items():
        s.set(x, fl + 1, z, "minecraft:daylight_detector")
        if abs(z - ckz) == 4:
            s.set(x, fl + 1, z, st.redstone_lamp(True))
        if abs(z - ckz) == 2:
            s.set(x + 1, fl + 1, z, st.facing_block("minecraft:observer", "west"))
    seat_x = max(cons_x.get(ckz - 1, 24), cons_x.get(ckz + 1, 24)) + 2
    s.set(seat_x, fl + 1, ckz - 1, st.stairs("polished_deepslate", "west"))
    s.set(seat_x, fl + 1, ckz + 1, st.stairs("polished_deepslate", "west"))
    for (x, dz) in ((25, -3), (25, 3), (29, 0)):
        ceiling_light(s, x, ckz + dz, LANTERN, y_from=fl + 2)
    s.set(30, fl + 1, ckz - 4, st.facing_block("minecraft:observer", "up"))
    s.set(30, fl + 2, ckz - 4, st.redstone_lamp(True))
    s.add_chest(30, fl + 1, ckz + 4, "north", "minecraft:chests/shipwreck_treasure")
    s.set(31, fl + 1, ckz + 2, "minecraft:barrel[facing=up,open=false]")
    s.set(32, fl + 2, ckz, LGRAY)
    s.add_sign(31, fl + 2, ckz, "minecraft:warped_wall_sign[facing=west]", ["LE CARGO", "vol 7", "JOURNAL 12", "impact - 04h12"])
    lx, lz = 28, ckz + 3                                         # ladder shaft corridor -> cockpit (off the centre line)
    for y in range(7, fl + 1):
        s.set(lx, y, lz, "minecraft:ladder[facing=north]")
        s.set(lx, y, lz + 1, PDS)
    for x in range(26, 31):
        s.set(x, fl, ckz + 3, LANTERN)
    # head exterior: sensor mast + antennas on the crown
    tz = ckz
    ty = s.top_y(29, tz)
    s.set(29, ty + 1, tz, IRON)
    for y in range(ty + 2, ty + 5):
        s.set(29, y, tz, st.lightning_rod("up"))
    for dz in (-4, 4):
        s.set(25, s.top_y(25, tz + dz) + 1, tz + dz, st.end_rod("up"))
    s.set(34, s.top_y(34, tz - 3) + 1, tz - 3, "minecraft:iron_bars")
    s.set(34, s.top_y(34, tz - 3) + 2, tz - 3, LANTERN)
    for x in range(23, 36):                                       # lavender dorsal stripe on the crown
        if x in (27, 29):
            continue
        ty = s.top_y(x, tz)
        if ty > G and "concrete" in s.get(x, ty, tz):
            s.set(x, ty, tz, PURPUR)
    for x in (24, 32):                                            # crown hatches
        s.set(x, s.top_y(x, tz + 1), tz + 1, st.trapdoor("iron", "north", "top", open=False))

    # ------------------------------------------------------------------ interior: corridor, cargo bay, crew quarters
    for xb in (30, 57):                                          # bulkheads with door openings
        cz = int(round(cz_of(MAIN, xb)))
        m = inner2 & (xs == xb) & (ys >= 7) & (ys <= 9)
        sh.fill_mask(s, m, PDS)
        if xb == 57:
            sh.fill_mask(s, inner2 & (xs == xb) & (ys >= 10), PDS)
        for y in (7, 8, 9):
            for z in (cz - 1, cz):
                s.set(xb, y, z, AIR)
        s.set(xb, 10, cz - 1, LANTERN)
        s.set(xb, 10, cz, LANTERN)
        for z in (cz - 2, cz + 1):
            for y in (7, 8, 9):
                s.set(xb, y, z, IRON)
    for x in range(21, 30):                                      # corridor: ceiling lights, cable, pipe
        cz = int(round(cz_of(MAIN, x)))
        if x % 3 == 0:
            ceiling_light(s, x, cz)
        ceiling_light(s, x, cz - 2, st.log("minecraft:chain", "x"))
        ceiling_light(s, x, cz + 2, "minecraft:oxidized_copper")
    s.add_sign(21, 9, int(round(cz_of(MAIN, 21))), "minecraft:warped_wall_sign[facing=east]", ["PONT AVANT", "cockpit ->", "echelle", ""])
    s.set(20, 9, int(round(cz_of(MAIN, 21))), LGRAY)
    for x in range(31, 57):                                      # cargo bay: floor light strips, ceiling lights
        cz_i = int(round(cz_of(MAIN, x)))
        if x % 4 == 1:
            s.set(x, 6, cz_i - 3, LANTERN)
            s.set(x, 6, cz_i + 3, LANTERN)
        if x % 5 == 3:
            ceiling_light(s, x, cz_i)
            ceiling_light(s, x, cz_i - 4)
            ceiling_light(s, x, cz_i + 4)
    crates = [
        (32, -5, "minecraft:cyan_concrete", 4, True),
        (37, -5, "minecraft:white_concrete", 4, True),
        (42, -5, "minecraft:light_gray_concrete", 4, False),
        (47, -5, "minecraft:cyan_concrete", 4, True),
        (52, -5, "minecraft:white_concrete", 4, False),
        (32, 3, "minecraft:light_gray_concrete", 4, True),
        (52, 3, "minecraft:cyan_concrete", 4, True),
    ]
    for (x, zo, col, ln, two) in crates:
        z1 = int(round(cz_of(MAIN, x + 1))) + zo
        container(s, x, 7, z1, ln, col, doors="east")
        if two:
            container(s, x, 10, z1, ln, "minecraft:light_gray_concrete" if col != "minecraft:light_gray_concrete" else "minecraft:white_concrete", doors="west")
    czc = int(round(cz_of(MAIN, 44)))
    s.set(44, 7, czc + 1, "minecraft:barrel[facing=up,open=false]")
    s.set(45, 7, czc + 1, "minecraft:barrel[facing=east,open=false]")
    s.set(44, 8, czc + 1, "minecraft:barrel[facing=up,open=false]")
    s.set(42, 7, czc + 2, "minecraft:cyan_shulker_box")
    s.add_chest(38, 7, czc - 2, "south", "minecraft:chests/shipwreck_supply")
    s.add_chest(50, 7, czc + 1, "north", "minecraft:chests/shipwreck_supply")
    s.add_sign(39, 9, int(round(cz_of(MAIN, 41))) - 5 + 3, "minecraft:warped_wall_sign[facing=south]", ["SOUTE B", "fret : cristaux", "ne pas ouvrir", ""])
    for x in (59, 62):                                           # crew quarters: 2 double bunks
        cz = int(round(cz_of(MAIN, x)))
        s.set(x, 7, cz - 3, st.bed("cyan", "east", "foot"))
        s.set(x + 1, 7, cz - 3, st.bed("cyan", "east", "head"))
        s.set(x, 9, cz - 3, st.slab("polished_deepslate", "top"))
        s.set(x + 1, 9, cz - 3, st.slab("polished_deepslate", "top"))
        s.set(x, 10, cz - 3, st.bed("white", "east", "foot"))
        s.set(x + 1, 10, cz - 3, st.bed("white", "east", "head"))
    czq = int(round(cz_of(MAIN, 61)))
    s.set(59, 7, czq + 3, "minecraft:barrel[facing=up,open=false]")
    s.set(60, 7, czq + 3, "minecraft:barrel[facing=up,open=false]")
    s.set(60, 8, czq + 3, "minecraft:barrel[facing=up,open=false]")
    s.set(62, 7, czq + 3, st.facing_block("minecraft:lectern", "north"))
    s.set(63, 7, czq + 2, st.stairs("polished_deepslate", "north"))
    s.add_chest(64, 7, czq + 2, "north", "minecraft:chests/shipwreck_supply")
    ceiling_light(s, 61, czq, FROG)
    ceiling_light(s, 64, czq, FROG)
    s.add_sign(58, 9, czq + 1, "minecraft:warped_wall_sign[facing=east]", ["QUARTIERS", "equipage 4", "2 partis au nord", "revenir vite"])

    # ------------------------------------------------------------------ flank breach (south side, cargo bay)
    bcx, bcy = 43.0, 10.5
    for x in range(34, 53):
        cz = cz_of(MAIN, x)
        for y in range(7, 18):
            for z in range(L):
                if z <= cz + 3 or not outer[x, y, z]:
                    continue
                d = ((x - bcx) / 7.5) ** 2 + ((y - bcy) / 4.6) ** 2
                d *= 0.85 + 0.3 * sh.value_noise2(x, y, 33, 3.0)
                if d <= 1.0:
                    s.set(x, y, z, AIR)
                elif d <= 1.35 and rng.random() < 0.5:
                    s.set(x, y, z, SHIP["damage_fill"] if rng.random() < 0.6 else SHIP["scorch"])
    for x in (37, 41, 45, 49):                                   # chains hanging from the top lip of the hole
        z = int(cz_of(MAIN, x) + 7)
        for y in range(16, 8, -1):
            if s.is_air(x, y, z) and not s.is_air(x, y + 1, z):
                for k in range(0, 3):
                    s.set(x, y - k, z, st.chain("y"))
                break
    for (x, y) in ((36, 10), (50, 10), (40, 14), (47, 14)):       # ribs poking out
        cz = int(round(cz_of(MAIN, x)))
        s.set(x, y, cz + 8, IRON)
        s.set(x, y, cz + 9, IRON)
    czb = int(round(cz_of(MAIN, 43)))
    for x in range(35, 52):                                      # lit deck lip along the breach
        if inner2[x, 6, czb + 5] or not s.is_air(x, 5, czb + 5):
            s.set(x, 6, czb + 5, LANTERN)
    container(s, 38, 7, czb + 4, 4, "minecraft:cyan_concrete", doors="south")       # stacks right at the torn edge
    container(s, 38, 10, czb + 4, 4, "minecraft:white_concrete", doors="south")
    container(s, 46, 7, czb + 4, 4, "minecraft:white_concrete", doors="south")
    container(s, 46, 10, czb + 4, 4, "minecraft:cyan_concrete", doors="south")
    for x in (39, 43, 47):                                       # pearlescent glow in the bay ceiling just inside
        ceiling_light(s, x, czb + 3, FROG, y_from=13)
    sh.ground_disc(s, 44, 39, 7, G, SHIP["scorch"], None, seed=12, noise=0.4, depth=1)
    container(s, 41, G + 1, 36, 4, "minecraft:cyan_concrete", doors="south")
    # a container half fallen out of the hole: tilted on the scorch disc, west end propped up
    for i, x in enumerate(range(45, 49)):
        y0 = G + 2 if i < 2 else G + 1
        for z in range(czb + 8, czb + 11):
            for y in range(y0, y0 + 3):
                s.set(x, y, z, "minecraft:cyan_concrete")
            if i in (0, 3):
                s.set(x, y0, z, PDS)
                s.set(x, y0 + 2, z, PDS)
        if i < 2:
            for z in range(czb + 8, czb + 11):
                s.set(x, G + 1, z, st.stairs("deepslate_tile", "west", "bottom"))
    s.set(46, G + 4, czb + 8, st.trapdoor("iron", "south", "bottom", open=True))
    s.set(48, G + 4, czb + 9, st.slab("polished_deepslate", "bottom"))
    s.set(45, G + 1, czb + 7, "minecraft:barrel[facing=west,open=false]")
    s.set(50, G + 1, 39, "minecraft:barrel[facing=up,open=false]")
    s.set(38, G + 1, 40, "minecraft:cyan_shulker_box")
    s.set(49, G + 1, 35, st.campfire(soul=True))
    s.add_sign(45, G + 1, 41, "minecraft:warped_sign[rotation=0]", ["BRECHE COQUE", "soute B", "fret disperse", "prudence"])

    # ------------------------------------------------------------------ severed end of the main hull (x 63..66)
    sh.erode(s, 65, 9, 10, 66, H - 1, 40, prob=0.4, seed=5, only=["concrete", "quartz", "deepslate_tiles", "andesite"])
    for y in range(H):
        for z in range(L):
            if shell_out[66, y, z] and not s.is_air(66, y, z) and rng.random() < 0.35:
                s.set(66, y, z, SHIP["damage_fill"] if rng.random() < 0.5 else SHIP["scorch"])
    cz66, cy66 = cz_of(MAIN, 66), cy_of(MAIN, 66)
    for a in (0.3, 1.2, 2.2, 3.4, 4.4, 5.6):
        y = int(round(cy66 + 5.5 * math.sin(a)))
        z = int(round(cz66 + 7.0 * math.cos(a)))
        for x in (66, 67, 68):
            if s.is_air(x, y, z) or "concrete" in s.get(x, y, z):
                s.set(x, y, z, IRON)
    for z in (int(cz66) - 2, int(cz66) + 1, int(cz66) + 3):
        for y in range(15, 11, -1):
            s.set(67, y, z, st.chain("y"))
    s.set(64, 17, int(cz66), st.campfire(soul=True))
    for x in range(67, 73):                                      # cable lying on the furrow floor
        z = int(cz66) - 4
        s.set(x, s.top_y(x, z) + 1, z, st.log("minecraft:chain", "x"))

    # ------------------------------------------------------------------ tail / engine section
    t_outer = sh.loft_mask(s, TAIL, "x")
    t_in1 = sh.loft_mask(s, TAIL, "x", shrink=1.0)
    t_in2 = sh.loft_mask(s, TAIL, "x", shrink=2.0)
    t_out = t_outer & ~t_in1
    sh.fill_mask(s, t_out, WHITE)
    sh.fill_mask(s, t_in1 & ~t_in2, LGRAY)
    paint_shell(s, TAIL, t_out, 80, 93)
    sh.fill_mask(s, t_in2 & (ys >= 7), AIR)
    sh.fill_mask(s, t_in2 & (ys < 7), DARK)
    sh.fill_mask(s, t_in2 & (ys == 6), PDS)
    for x in range(80, 94):
        cy, cz = cy_of(TAIL, x), cz_of(TAIL, x)
        yb = int(round(cy - 0.5))
        for z in range(L):
            if t_out[x, yb, z] and abs(z - cz) > 2:
                s.set(x, yb, z, DARK)
            if 83 <= x <= 91 and t_out[x, yb - 1, z] and abs(z - cz) > 4:
                s.set(x, yb - 1, z, PURPUR)
            if 84 <= x <= 90 and abs(z - cz) >= 5 and t_out[x, yb + 3, z]:
                s.set(x, yb + 3, z, GLASS if x != 87 else IRON)
    for xr in (84, 90):
        sh.fill_mask(s, t_out & (xs == xr), PDS)
    bevel_hull(s, t_outer, TAIL, 80, 93, skip=lambda x, y, z: x <= 82)
    cyt, czt = cy_of(TAIL, 93), cz_of(TAIL, 93)
    sh.fill_mask(s, t_outer & (xs == 93), PDS)
    sh.fill_mask(s, t_outer & (xs == 92), DARK)
    # three nozzles protruding 5 blocks behind the tail face: basalt cone, iron ring, sea-lantern core, cyan lip
    for (dz, dy, r) in ((-3.6, 0.0, 3.3), (3.6, 0.0, 3.3), (0.0, -3.2, 1.5)):
        ncz, ncy = czt + dz, cyt + dy
        big = r > 2
        sh.cylinder(s, 93, ncy, ncz, r, 5, BASALT_P, axis="x", hollow=big, thickness=1.0, r2=r - 0.5)
        if big:
            sh.cylinder(s, 93, ncy, ncz, r - 1.0, 1, IRON, axis="x", hollow=True, thickness=1.0)
            sh.cylinder(s, 93, ncy, ncz, r - 1.7, 2, LANTERN, axis="x")
            sh.cylinder(s, 96, ncy, ncz, r - 1.3, 1, SHIP["engine_glow"], axis="x")
            sh.cylinder(s, 98, ncy, ncz, r - 0.5, 0, SHIP["engine_glow"], axis="x", hollow=True, thickness=1.0)
            sh.cylinder(s, 98, ncy, ncz, r - 1.5, 0, LANTERN, axis="x")
        else:
            sh.cylinder(s, 97, ncy, ncz, r - 0.5, 1, SHIP["engine_glow"], axis="x")
            sh.cylinder(s, 94, ncy, ncz, r - 1.0, 2, LANTERN, axis="x")
        zi, yi = int(round(ncz)), int(round(ncy))
        top = s.top_y(97, zi)
        s.set(97, top + 1, zi, st.campfire(soul=True))
    s.set(101, s.top_y(101, int(round(czt + 2))) + 1, int(round(czt + 2)), st.campfire(soul=True))
    czr = int(round(cz_of(TAIL, 87)))                            # engine room: reactor core + cables
    sh.box(s, 86, 7, czr - 1, 88, 12, czr + 1, PDS)
    sh.box(s, 87, 8, czr, 87, 11, czr, SHIP["engine_core"])
    for y in (8, 9, 10, 11):
        s.set(86, y, czr, SHIP["engine_glow"])
        s.set(88, y, czr, SHIP["engine_glow"])
        s.set(87, y, czr - 1, SHIP["engine_glow"])
        s.set(87, y, czr + 1, SHIP["engine_glow"])
    for x in range(82, 86):
        ceiling_light(s, x, czr - 3, st.log("minecraft:chain", "x"))
        ceiling_light(s, x, czr + 3, "minecraft:oxidized_copper")
    s.set(84, 7, czr + 3, st.facing_block("minecraft:blast_furnace", "west"))
    s.set(84, 7, czr - 3, "minecraft:cauldron")
    s.add_sign(85, 9, czr - 1, "minecraft:warped_wall_sign[facing=west]", ["REACTEUR", "fuite plasma", "DANGER", "evacuer"])
    ceiling_light(s, 84, czr)
    sh.erode(s, 80, 9, 20, 82, H - 1, 42, prob=0.5, seed=8, only=["concrete", "quartz", "deepslate_tiles", "andesite"])
    cz80, cy80 = cz_of(TAIL, 80), cy_of(TAIL, 80)
    for a in (0.5, 1.6, 2.6, 3.8, 5.0):
        y = int(round(cy80 + 5.5 * math.sin(a)))
        z = int(round(cz80 + 7.0 * math.cos(a)))
        for x in (78, 79, 80):
            if s.is_air(x, y, z) or "concrete" in s.get(x, y, z):
                s.set(x, y, z, IRON)
    for z in (int(cz80) - 1, int(cz80) + 2):
        for y in range(15, 12, -1):
            s.set(79, y, z, st.chain("y"))
    s.set(81, 18, int(cz80), st.campfire(soul=True))
    # swept vertical fin: a 2-thick plate, top edge rising toward the rear, dark leading edge with stair steps,
    # a cyan/purple glass strip, dark trailing edge post
    fin_cols = []
    for x in range(82, 93):
        zc = cz_of(TAIL, x)
        z0 = int(math.floor(zc))
        top = 18.0 + (x - 82) * 0.55
        hi = int(math.floor(top))
        for z in (z0, z0 + 1):
            ty = s.top_y(x, z)
            if ty < G + 2:
                continue
            for y in range(ty + 1, hi + 1):
                s.set(x, y, z, WHITE)
            s.set(x, hi, z, DARK)
            if top - hi >= 0.5:
                s.set(x, hi + 1, z, st.stairs("quartz", "east", "bottom"))
            if 86 <= x <= 90 and hi - 1 > ty + 1:
                s.set(x, hi - 1, z, SHIP["engine_glow"] if x != 88 else PGLASS)
            if x == 92:
                for y in range(ty + 1, hi + 1):
                    s.set(x, y, z, DARK)
        fin_cols.append((x, z0, hi))
    x, z0, hi = fin_cols[-1]
    s.set(x, hi + 1, z0, st.end_rod("up"))
    s.set(82, s.top_y(82, int(math.floor(cz_of(TAIL, 82)))) + 1, int(math.floor(cz_of(TAIL, 82))), st.stairs("quartz", "east", "bottom"))

    # ------------------------------------------------------------------ hull exterior details
    for x in range(24, 62, 6):                                   # iron vent panels on the flanks
        cy = cy_of(MAIN, x)
        y = int(round(cy - 2.5))
        for side in (-1, 1):
            z = first_solid_z(s, outer, x, y, side > 0)
            if z is not None and (side < 0 or not (34 <= x <= 52)):
                s.set(x, y, z, st.trapdoor("iron", "north" if side < 0 else "south", "top", open=False))
    hx, hz = 44, int(round(cz_of(MAIN, 44)))                     # top cargo hatch (open) with ladder into the bay
    ty = s.top_y(hx, hz)
    for x in (hx, hx + 1):
        for z in (hz - 2, hz - 1):
            for y in range(7, ty + 1):
                s.set(x, y, z, AIR)
    for y in range(7, ty + 1):
        if s.is_air(hx, y, hz - 3):
            s.set(hx, y, hz - 3, PDS)
        s.set(hx, y, hz - 2, "minecraft:ladder[facing=south]")
    s.set(hx - 1, ty, hz - 2, st.trapdoor("iron", "east", "top", open=True))
    s.set(hx + 2, ty, hz - 1, st.trapdoor("iron", "west", "top", open=True))
    s.set(hx, ty, hz, LANTERN)
    s.set(hx + 1, ty, hz, LANTERN)
    ax, az = 56, int(round(cz_of(MAIN, 56)))                     # dorsal antenna cluster
    ty = s.top_y(ax, az)
    s.set(ax, ty + 1, az, IRON)
    s.set(ax, ty + 2, az, st.lightning_rod("up"))
    s.set(ax, ty + 3, az, st.lightning_rod("up"))
    s.set(ax + 2, s.top_y(ax + 2, az) + 1, az, st.end_rod("up"))
    s.set(ax - 2, s.top_y(ax - 2, az) + 1, az, st.end_rod("up"))
    for x in range(20, 62, 7):                                   # running lights on the belt line
        cy = cy_of(MAIN, x)
        y = int(round(cy - 0.5))
        for side in (-1, 1):
            z = first_solid_z(s, outer, x, y, side > 0)
            if z is not None and not (34 <= x <= 52 and side > 0):
                s.set(x, y, z, FROG)

    # ------------------------------------------------------------------ crystals of the Neige world around the impact
    for (x, z, h) in ((4, 11, 3), (2, 29, 5), (9, 33, 2), (17, 8, 4), (7, 36, 1), (25, 40, 3)):
        ty = s.top_y(x, z)
        for y in range(ty + 1, ty + 1 + h):
            s.set(x, y, z, "minecraft:amethyst_block")
        s.set(x, ty + 1 + h, z, "minecraft:amethyst_cluster[facing=up]")
        s.set(x + 1, ty + 1, z, "minecraft:large_amethyst_bud[facing=up]")
        s.set(x - 1, ty + 1, z + 1, "minecraft:medium_amethyst_bud[facing=up]")

    # ------------------------------------------------------------------ debris trail, snow drift, weathering
    debris = [IRON, SHIP["damage_fill"], st.slab("deepslate_tile"), st.stairs("deepslate_tile", "east"),
              "minecraft:barrel[facing=up,open=false]", BASALT_P, st.log("minecraft:chain", "x"), PDS]
    for _ in range(46):
        x = rng.randint(64, W - 2)
        half = furrow_half(x)
        z = int(round(furrow_center(x) + rng.uniform(-half + 1.5, half - 1.5)))
        if 0 < z < L - 1 and s.top_y(x, z) <= G:
            s.set(x, s.top_y(x, z) + 1, z, rng.choice(debris))
    for x in range(12, 66):                                      # leeward snow drift against the north flank
        zmin = first_solid_z(s, outer, x, G + 1, False)
        zmin2 = first_solid_z(s, outer, x, G + 2, False)
        zmin = min([v for v in (zmin, zmin2) if v is not None], default=None)
        if zmin is None:
            continue
        for dz in range(0, 7):
            z = zmin - dz
            n = sh.value_noise2(x, z, 17, 5.0)
            h = int(round(3.4 - dz * 0.6 + 1.2 * n - 0.6))
            for y in range(G + 1, G + 1 + h):
                if s.is_air(x, y, z):
                    s.set(x, y, z, GROUND["snow"])
            if h > 0 and s.is_air(x, G + 1 + h, z):
                s.set(x, G + 1 + h, z, st.snow_layer(2 + int(4 * n)))
    for x in range(80, 94):
        zmin = first_solid_z(s, t_outer, x, G + 1, False)
        if zmin is None:
            continue
        for dz in range(0, 5):
            z = zmin - dz
            n = sh.value_noise2(x, z, 19, 5.0)
            h = int(round(2.4 - dz * 0.6 + n))
            for y in range(G + 1, G + 1 + h):
                if s.is_air(x, y, z):
                    s.set(x, y, z, GROUND["snow"])
    for x in range(14, 22, 2):                                   # icicles under the bow overhang
        cz = int(round(cz_of(MAIN, x)))
        for dz in (-3, 3):
            for yy in range(G + 1, 12):
                if s.is_air(x, yy, cz + dz) and not s.is_air(x, yy + 1, cz + dz):
                    s.set(x, yy, cz + dz, st.pointed_dripstone("down", "tip"))
                    break

    sh.texturize(s, WHITE, MIX_HULL_WHITE, seed=5)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=6)
    sh.texturize(s, UNDER, MIX_DARK, seed=7)
    sh.texturize(s, SHIP["scorch"], MIX_SCORCH, seed=8)
    # light snow on true top faces only (hull crowns, wings), never on the head crown, flanks or belt
    snow_rng = random.Random(3)
    snow_skip = ("glass", "iron", "lantern", "rod", "campfire", "froglight", "lamp", "detector", "observer", "cyan",
                 "bed", "chain", "ladder", "trapdoor", "barrel", "chest", "sign", "cauldron", "furnace", "lectern",
                 "copper", "basalt", "slab", "stairs", "snow", "amethyst", "purpur", "tuff", "powder", "bars",
                 "shulker", "coal", "blackstone", "cobbled", "purple")
    for x in range(W):
        for z in range(L):
            ty = s.top_y(x, z)
            if ty <= G + 1 or ty + 1 >= H:
                continue
            b = s.get(x, ty, z)
            if any(k in b for k in snow_skip):
                continue
            ok = False
            if 6 <= x <= 66 and outer[x, ty, z]:
                ok = ty >= cy_of(HULL, x) + ry_of(HULL, x) - 1.5 and not (20 <= x <= 38)
            elif 80 <= x <= 93 and t_outer[x, ty, z]:
                ok = ty >= cy_of(TAIL, x) + ry_of(TAIL, x) - 1.5
            elif ty <= y_wing + 3:
                ok = True                                          # wings, nacelles, spilled crates
            if ok and snow_rng.random() < 0.12 * (0.5 + sh.value_noise2(x, z, 3, 6.0)):
                s.set(x, ty + 1, z, st.snow_layer(1 + int(round(sh.value_noise2(x + 100, z + 100, 10, 5.0)))))
    # cleanup: drop stray isolated debris/hull fragments above ground (keeps signs, lights, chains)
    nz = s.data != 0
    pad = np.zeros((W + 2, H + 2, L + 2), dtype=bool)
    pad[1:-1, 1:-1, 1:-1] = nz
    neigh = (pad[:-2, 1:-1, 1:-1] | pad[2:, 1:-1, 1:-1] | pad[1:-1, :-2, 1:-1] | pad[1:-1, 2:, 1:-1]
             | pad[1:-1, 1:-1, :-2] | pad[1:-1, 1:-1, 2:])
    for (x, y, z) in np.argwhere(nz & ~neigh):
        if y > G and any(k in s.get(x, y, z) for k in ("cobbled", "basalt", "blackstone", "concrete", "quartz", "deepslate", "andesite", "coal")):
            s.set(x, y, z, AIR)
    return {"ship_crash_freighter": s.cropped(pad=1)}

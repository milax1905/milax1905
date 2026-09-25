"""Le Cargo: a big interstellar freighter that crash-landed in the snow and broke in two.

Main hull (nose west, plowed into a 13-radius crater) lofted from elliptical sections that are ROLLED ~6-11 degrees
(north flank down, the list grows toward the break) so the wreck reads crashed, not parked. The loft swells into a
raised "head" at the front holding the cockpit behind a stepped, raked windscreen. Three continuous dark trim lines
(belt line, deck line, dorsal spine) draw the hull from far away. Swept wings with engine nacelles: the north one
dips into the leeward snow drift, the south one sheared off and lies further south-east so it does not screen the
BIG cargo-bay breach (23 blocks long, floor to deck) on the south flank. The engine/tail section lies ~14 blocks
behind, yawed and rolled the other way, with a tall swept fin, dark collars, pipes, vents and three nozzles still
glowing cyan and smoking. Long skid furrow (8 wide, snow lips, shallower toward the touchdown at the east edge),
hull-fragment debris, cables to the ground, lit furnished interior, loot, French signs, lavender accents.
"""
import math
import random

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_LIGHT_GRAY, MIX_DARK, MIX_SCORCH

W, H, L, G = 108, 32, 58, 5
AIR = "minecraft:air"

# (x, cy, cz, ry, rz) - body of the main hull: used for the interior centre line and the wing root height
MAIN = [
    (6, 7.5, 21.0, 1.5, 1.5),
    (12, 8.3, 21.5, 3.0, 4.0),
    (20, 9.6, 22.0, 5.0, 6.5),
    (30, 10.5, 23.0, 8.0, 9.0),
    (52, 10.5, 24.5, 8.0, 9.0),
    (60, 11.0, 25.0, 7.0, 8.0),
    (66, 11.0, 25.5, 6.0, 7.0),
]
# geometry of the main hull: the body plus a raised "head" (cy and ry both raised -> the keel line is unchanged,
# the top swells up ~4 blocks between x=22 and x=37 to house the cockpit)
HULL = [
    (6, 7.5, 21.0, 1.5, 1.5),
    (12, 8.3, 21.5, 3.0, 4.0),
    (20, 9.6, 22.0, 5.0, 6.5),
    (22, 10.8, 22.2, 6.5, 7.2),
    (25, 12.3, 22.5, 9.0, 8.2),
    (33, 13.0, 23.1, 9.5, 9.0),
    (38, 10.5, 23.4, 8.0, 9.0),
    (52, 10.5, 24.5, 8.0, 9.0),
    (60, 11.0, 25.0, 7.0, 8.0),
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
COPPER = SHIP["pipe_thick"]
MIX_HULL_WHITE = [("minecraft:white_concrete", 9), ("minecraft:quartz_block", 1)]   # two close shades only

ZONE_BLOCK = {"white": WHITE, "gray": LGRAY, "dark": UNDER}
ZONE_STAIR = {"white": "quartz", "gray": "polished_andesite", "dark": "deepslate_tile"}


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


def roll_main(xs):
    """Roll (radians) of the main hull: north flank down, 6 deg at the nose growing to 11 deg at the break."""
    return np.radians(-7.0 - 5.0 * np.clip((xs - 6.0) / 60.0, 0.0, 1.0))


def roll_tail(xs):
    return np.full_like(xs, math.radians(10.0))


def rolled_loft(secs, roll_fn, shrink=0.0):
    """Loft mask of elliptical sections rolled about the x axis. Returns (mask, U, V): U = height in the ship
    frame (up), V = sideways in the ship frame (+ = south) for every voxel."""
    xs, ys, zs = (a.astype(float) for a in np.indices((W, H, L)))
    sec = np.array(secs, dtype=float)
    A = sec[:, 0]
    c1 = np.interp(xs, A, sec[:, 1])
    c2 = np.interp(xs, A, sec[:, 2])
    r1 = np.maximum(np.interp(xs, A, sec[:, 3]) + 0.5 - shrink, 0.01)
    r2 = np.maximum(np.interp(xs, A, sec[:, 4]) + 0.5 - shrink, 0.01)
    th = roll_fn(xs)
    dy, dz = ys - c1, zs - c2
    u = dy * np.cos(th) + dz * np.sin(th)
    v = -dy * np.sin(th) + dz * np.cos(th)
    m = (xs >= A[0]) & (xs <= A[-1]) & ((u / r1) ** 2 + (v / r2) ** 2 <= 1.0)
    return m, u, v


def zone_of(u, white_min=-0.5, gray_min=-3.5):
    return "white" if u >= white_min else ("gray" if u >= gray_min else "dark")


def paint_shell(s, mask, U, white_min=-0.5, gray_min=-3.5):
    """Colour a shell layer by ship-frame height: white top, light-gray flank, dark keel."""
    sh.fill_mask(s, mask & (U >= white_min), WHITE)
    sh.fill_mask(s, mask & (U < white_min) & (U >= gray_min), LGRAY)
    sh.fill_mask(s, mask & (U < gray_min), UNDER)


def ridge_of(outer, x_lo, x_hi):
    """z of the highest point of the hull for every x (the rolled top ridge)."""
    ridge = {}
    for x in range(x_lo, x_hi + 1):
        col = outer[x]                                      # (H, L)
        has = col.any(axis=0)
        if not has.any():
            continue
        top = np.where(has, H - 1 - np.argmax(col[::-1, :], axis=0), -1)
        best = np.flatnonzero(top == top.max())
        ridge[x] = int(best[len(best) // 2])
    return ridge


def bevel_hull(s, outer, U, ry_fn, x_lo, x_hi, skip=None, thr=(-0.5, -3.5)):
    """Soften the staircase steps of the lofted ellipse: slabs on the top/bottom surfaces (smooth deck), stairs
    only on the true silhouette edges of the flanks."""
    for x in range(x_lo, x_hi + 1):
        ry = ry_fn(x)
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
                uu = U[x, y - 1 if below else y + 1, z]
                mat = ZONE_STAIR[zone_of(uu, *thr)]
                if below and uu > 0.4 * ry:
                    s.set(x, y, z, st.slab(mat, "bottom"))
                elif above and uu < -0.4 * ry:
                    s.set(x, y, z, st.slab(mat, "top"))
                else:
                    s.set(x, y, z, st.stairs(mat, sides[0], "bottom" if below else "top"))


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


def wing(s, outer, x1, x2, side, span, y_root, slope=0.0, dead=False):
    """Swept wing plate attached to the hull flank (side=-1 north, +1 south), engine nacelle at the tip.
    slope = blocks of height per block of span (negative = the wing dips toward the tip)."""
    def root(x):
        return first_solid_z(s, outer, x, y_root, side > 0)

    for k in range(span):
        xa = x1 + int(k * 0.30)
        xb = x2 - int(k * 0.55)
        y = y_root + int(math.floor(k * slope))
        for x in range(xa, xb + 1):
            zr = root(x)
            if zr is None:
                continue
            z = zr + side * (1 + k)
            blk = DARK if x == xa else (LGRAY if k < 2 else WHITE)
            s.set(x, y, z, blk)
            if x == xb:
                s.set(x + 1, y, z, st.slab("smooth_quartz", "bottom"))   # thin trailing edge
            if k < 3:
                s.set(x, y - 1, z, PDS)                                    # wing root fairing
                s.set(x, y + 1, z, st.slab("polished_deepslate", "bottom") if k < 2 else st.slab("smooth_quartz", "bottom"))
        if 2 <= k < span - 3:                                              # one dark panel stripe
            xm = (xa + xb) // 2
            zr = root(xm)
            if zr is not None:
                s.set(xm, y, zr + side * (1 + k), DARK)
    # nacelle at the tip: cylinder along x, dark rings, lavender band, glowing cyan exhaust, tinted intake
    k = span - 2
    xa = x1 + int(k * 0.30)
    nx1 = xa - 2
    zr = root(xa)
    nz = zr + side * (1 + k)
    ny = y_root + int(math.floor(k * slope))
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
    return nz


def furrow_center(x):
    """Centre line of the skid furrow: the body's centre line, then drifting south with the yawed tail."""
    if x <= 66:
        return cz_of(MAIN, max(x, 6))
    return cz_of(MAIN, 66) + (x - 66) * 0.30


def furrow_half(x):
    """Half width: wide under the hull, then a narrow 8-9 wide skid band to the touchdown at the east edge."""
    if x <= 60:
        return 6.5
    if x <= 80:
        return 6.5 - (x - 60) * (2.0 / 20.0)
    return 4.5 if x < 98 else 4.0


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
                dep = 2 if (d < 0.6 and x < 96) else 1
                for y in range(G - dep + 1, G + 1):
                    s.set(x, y, z, AIR)
                n2 = sh.value_noise2(x, z, 27, 3.5)
                if x < 98:
                    floor = SHIP["scorch"] if n2 < 0.72 else ("minecraft:coal_block" if n2 < 0.86 else "minecraft:basalt")
                else:                                       # touchdown: only scuffed, mostly tuff/basalt
                    floor = "minecraft:tuff" if n2 < 0.5 else ("minecraft:basalt" if n2 < 0.8 else SHIP["scorch"])
                s.set(x, G - dep, z, floor)
            elif d <= 1.30 + 0.2 * n and x >= 58:           # plowed snow lips on both sides, 1-2 high
                if sh.value_noise2(x, z, 23, 3.0) < 0.30:
                    continue
                h = 1 + (1 if n > 0.62 and d < 1.15 else 0)
                for y in range(G + 1, G + 1 + h):
                    n3 = sh.value_noise2(x + y * 7, z, 29, 3.0)
                    blk = "minecraft:tuff" if n3 > 0.86 else ("minecraft:white_concrete_powder" if n3 > 0.55 else GROUND["snow"])
                    s.set(x, y, z, blk)
    for (z0, z1) in ((-1.0, -4.0), (0.5, -1.5), (-0.5, 2.0), (1.5, 3.5)):   # skid gouges diverging from the centre
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
    sh.crater(s, 15, 21.5, 13, G, SHIP["scorch"], GROUND["snow"], GROUND["snow"], depth=3, rim_height=2, seed=9)
    for x in range(0, 12):                                  # bow wave of snow pushed ahead of / around the nose
        for z in range(11, 33):
            n = sh.value_noise2(x, z, 4, 4.0)
            h = int(round((4.5 - abs(z - 21.5) * 0.36 - abs(x - 6) * 0.45) * (0.7 + 0.6 * n)))
            for y in range(s.top_y(x, z) + 1, G + 1 + h):
                s.set(x, y, z, GROUND["snow"])

    # ------------------------------------------------------------------ main hull (rolled loft)
    outer, U, V = rolled_loft(HULL, roll_main)
    inner1, _, _ = rolled_loft(HULL, roll_main, shrink=1.0)
    inner2, _, _ = rolled_loft(HULL, roll_main, shrink=2.0)
    shell_out = outer & ~inner1
    shell_in = inner1 & ~inner2
    sh.fill_mask(s, shell_out, WHITE)
    sh.fill_mask(s, shell_in, LGRAY)
    paint_shell(s, shell_out, U)
    cav = inner2 & (xs >= 20) & (ys >= 7)
    sh.fill_mask(s, cav, AIR)
    sh.fill_mask(s, inner2 & (xs >= 20) & (ys < 7), DARK)
    sh.fill_mask(s, inner2 & (xs == 6), PDS)
    sh.fill_mask(s, inner2 & (xs >= 20) & (ys == 6), PDS)
    sh.fill_mask(s, inner2 & (xs < 20), LGRAY)
    # the head is solid above the corridor (equipment deck) except for the cockpit cavity
    sh.fill_mask(s, inner2 & (xs >= 20) & (xs <= 38) & (ys >= 10), LGRAY)
    ridge = ridge_of(outer, 6, 66)
    ckz = ridge[27]
    cockpit = inner2 & (xs >= 22) & (xs <= 31) & (np.abs(zs - ckz) <= 5)
    sh.fill_mask(s, cockpit & (ys >= 15) & (ys <= 18), AIR)
    sh.fill_mask(s, cockpit & (ys == 14), PDS)

    # three continuous trim lines: belt (widest point), deck line (upper flank), dorsal spine (ridge); lavender
    # stripe under the belt, window strip above it, dark ribs
    absV = np.abs(V)
    in_x = (xs >= 14) & (xs <= 66)
    belt = shell_out & in_x & (np.abs(U) <= 0.55) & (absV > 2.5)
    sh.fill_mask(s, belt, DARK)
    for x in range(14, 67):
        ry = ry_of(HULL, x)
        deck = shell_out[x] & (U[x] >= ry - 2.6) & (U[x] < ry - 1.6) & (absV[x] >= 3.0)
        for (y, z) in np.argwhere(deck):
            s.set(x, y, z, DARK)
    breach_side = (xs >= 33) & (xs <= 55) & (V > 0)
    purp = shell_out & (xs >= 22) & (xs <= 62) & (U < -0.6) & (U >= -1.7) & (absV > 4.0) & ~breach_side
    sh.fill_mask(s, purp, PURPUR)
    for x in range(22, 63):
        win = (shell_out[x] | shell_in[x]) & (U[x] >= 2.4) & (U[x] < 3.5) & (absV[x] >= 5.0)
        blk = IRON if x % 5 == 0 else (PGLASS if x % 5 == 2 else GLASS)
        for (y, z) in np.argwhere(win):
            s.set(x, y, z, blk)
    for xr in (18, 27, 37, 52, 60):
        m = shell_out & (xs == xr)
        sh.fill_mask(s, m, PDS)
        sh.fill_mask(s, m & (np.abs(U) < 1.5), IRON)
    for x in range(14, 67):                                  # dorsal spine along the rolled ridge (full length)
        if 19 <= x <= 27:
            continue                                         # the windscreen's centre mullion continues the line
        z = ridge[x]
        ty = s.top_y(x, z)
        if ty > G:
            s.set(x, ty, z, DARK)
            s.set(x, ty + 1, z, st.slab("polished_deepslate"))

    # ------------------------------------------------------------------ cockpit windows in the head
    for x in range(19, 28):                                  # stepped raked windscreen (follows the loft's front slope)
        for y in range(14, 23):
            for z in range(ckz - 4, ckz + 5):
                if shell_out[x, y, z] or shell_in[x, y, z]:
                    s.set(x, y, z, IRON if z == ckz else GLASS)
    for x in range(26, 32):                                  # side windows of the cockpit
        for y in (16, 17):
            for z in range(L):
                if abs(z - ckz) >= 5 and (shell_out[x, y, z] or shell_in[x, y, z]):
                    s.set(x, y, z, GLASS if x != 28 else PGLASS)
    for dz in (-3, 0, 3):                                    # landing lights under the windscreen
        x = first_solid_x(outer, 13, ckz + dz, 14, 26)
        if x is not None:
            s.set(x, 13, ckz + dz, FROG)

    skip_bevel = lambda x, y, z: ((33 <= x <= 55 and V[x, y, z] > 3) or x >= 63
                                  or (19 <= x <= 27 and abs(z - ckz) <= 4 and y >= 14))
    bevel_hull(s, outer, U, lambda x: ry_of(HULL, x), 6, 66, skip=skip_bevel)

    # ------------------------------------------------------------------ wings (north intact & dipping, south sheared)
    y_wing = int(cy_of(MAIN, 54))                           # 10
    wing(s, outer, 46, 62, -1, 13, y_wing, slope=-0.16)
    for k in range(0, 3):                                   # south stump, torn (east of the breach only)
        for x in range(53 + int(k * 0.3), 62 - int(k * 0.55) + 1):
            zr = first_solid_z(s, outer, x, y_wing, True)
            if zr is None:
                continue
            z = zr + 1 + k
            blk = DARK if x == 53 else (LGRAY if k < 2 else SHIP["damage_fill"])
            if k == 2 and rng.random() < 0.5:
                continue
            s.set(x, y_wing, z, blk)
            if k < 2:
                s.set(x, y_wing - 1, z, PDS)
                s.set(x, y_wing + 1, z, st.slab("polished_deepslate", "bottom"))
    for x in (55, 58):
        zr = first_solid_z(s, outer, x, y_wing, True)
        s.set(x, y_wing, zr + 4, IRON)
        s.set(x, y_wing, zr + 5, IRON)
    # the sheared wing lying in the snow south-east of the wreck (drawn along z), nacelle dead & smoking
    sh.ground_disc(s, 71, 50, 6, G, SHIP["scorch"], None, seed=15, noise=0.4, depth=1)
    for k in range(12):
        za = 44 + int(k * 0.30)
        zb = 56 - int(k * 0.55)
        x = 64 + k
        y = G + 1 + (k // 5)
        for z in range(za, zb + 1):
            s.set(x, y, z, DARK if z == za else (SHIP["damage_fill"] if k < 2 and rng.random() < 0.5 else WHITE))
            if z == zb:
                s.set(x, y, z + 1, st.slab("smooth_quartz", "bottom"))
        if 2 <= k < 9:
            s.set(x, y, (za + zb) // 2, DARK)
    nx, nz0 = 76, 46
    sh.cylinder(s, nx, G + 3, nz0, 2.2, 9, WHITE, axis="z")
    sh.cylinder(s, nx, G + 3, nz0, 2.2, 0, PDS, axis="z")
    sh.cylinder(s, nx, G + 3, nz0 + 3, 2.2, 0, PURPUR, axis="z")
    sh.cylinder(s, nx, G + 3, nz0 + 9, 2.4, 0, PDS, axis="z")
    sh.cylinder(s, nx, G + 3, nz0 + 9, 1.4, 0, SHIP["scorch"], axis="z")
    sh.cylinder(s, nx, G + 3, nz0, 1.3, 0, "minecraft:tinted_glass", axis="z")
    s.set(nx, G + 5, nz0 + 5, st.campfire(soul=True))
    s.set(nx, G + 6, nz0 + 6, st.slab("polished_deepslate", "bottom"))
    for z in range(nz0 + 1, nz0 + 9):
        s.set(nx, G + 1, z, UNDER)
        if s.is_air(nx - 1, G + 1, z):
            s.set(nx - 1, G + 1, z, st.stairs("deepslate_tile", "east", "top"))
        if s.is_air(nx + 1, G + 1, z):
            s.set(nx + 1, G + 1, z, st.stairs("deepslate_tile", "west", "top"))

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
    # head exterior: sensor mast + antennas on the crown, lavender accent stripe beside the spine
    tz = ridge[29]
    ty = s.top_y(29, tz)
    s.set(29, ty + 1, tz, IRON)
    for y in range(ty + 2, ty + 5):
        s.set(29, y, tz, st.lightning_rod("up"))
    for dz in (-4, 4):
        s.set(25, s.top_y(25, tz + dz) + 1, tz + dz, st.end_rod("up"))
    s.set(34, s.top_y(34, tz - 3) + 1, tz - 3, "minecraft:iron_bars")
    s.set(34, s.top_y(34, tz - 3) + 2, tz - 3, LANTERN)
    for x in range(23, 37):
        z = ridge[x] + 2
        ty = s.top_y(x, z)
        if ty > G and "concrete" in s.get(x, ty, z):
            s.set(x, ty, z, PURPUR)
    for x in (24, 32):                                            # crown hatches
        z = ridge[x] - 2
        s.set(x, s.top_y(x, z), z, st.trapdoor("iron", "north", "top", open=False))

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
        ceiling_light(s, x, cz + 2, COPPER)
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
    s.add_sign(39, 9, int(round(cz_of(MAIN, 41))) - 2, "minecraft:warped_wall_sign[facing=south]", ["SOUTE B", "fret : cristaux", "ne pas ouvrir", ""])
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
    # a 23-long tear from the bay floor up to the deck; the floor (y=6) and the ridge stay, the rest is peeled away
    bcx, bcy, brx, bry = 44.0, 12.0, 11.5, 7.0
    for x in range(33, 56):
        for y in range(6, 20):
            for z in range(L):
                if not outer[x, y, z] or V[x, y, z] <= 3.0 or (y <= 6 and inner2[x, y, z]):
                    continue
                d = ((x - bcx) / brx) ** 2 + ((y - bcy) / bry) ** 2
                d *= 0.85 + 0.3 * sh.value_noise2(x, y, 33, 3.0)
                if d <= 1.0:
                    s.set(x, y, z, AIR)
                elif d <= 1.14 and rng.random() < 0.65:                 # burnt rim, dark only (no speckle)
                    s.set(x, y, z, SHIP["scorch"])
    lip = {}
    for x in range(34, 55):                                      # top lip of the tear (per column, on the flank)
        zf = first_solid_z(s, outer, x, 12, True)
        if zf is None:
            continue
        for z in (zf, zf - 1, zf - 2):
            for y in range(19, 7, -1):
                if s.is_air(x, y, z) and not s.is_air(x, y + 1, z) and outer[x, y + 1, z]:
                    lip[x] = (y, z)
                    break
            if x in lip:
                break
    for x, (y, z) in lip.items():                                # bent plating hanging from the lip
        if x % 4 == 0:
            s.set(x, y, z, st.trapdoor("iron", "south", "top", open=True))
        elif x % 4 == 2:
            s.set(x, y, z, st.stairs("deepslate_tile", "north", "top"))
    for x in (36, 40, 44, 48, 52):                               # chains hanging from the lip down into the bay
        if x not in lip:
            continue
        y, z = lip[x]
        for k in range(0, 4):
            if s.is_air(x, y - k, z):
                s.set(x, y - k, z, st.chain("y"))
    for (x, y) in ((35, 10), (53, 10), (39, 15), (49, 15)):       # ribs poking out
        zf = first_solid_z(s, outer, x, y, True)
        if zf is not None:
            s.set(x, y, zf + 1, IRON)
            s.set(x, y, zf + 2, IRON)
    czb = int(round(cz_of(MAIN, 44)))
    for x in range(34, 55):                                      # lit deck lip along the whole tear + warm floor strip
        zed = None
        for z in range(L - 1, -1, -1):
            if inner2[x, 6, z]:
                zed = z
                break
        if zed is None:
            continue
        s.set(x, 6, zed, LANTERN)
        if x % 2 == 0 and s.is_air(x, 7, zed - 3):
            s.set(x, 6, zed - 3, FROG)
    container(s, 38, 7, czb + 4, 4, "minecraft:cyan_concrete", doors="south")       # stacks right at the torn edge
    container(s, 38, 10, czb + 4, 4, "minecraft:white_concrete", doors="south")
    container(s, 46, 7, czb + 4, 4, "minecraft:white_concrete", doors="south")
    container(s, 46, 10, czb + 4, 4, "minecraft:cyan_concrete", doors="south")
    for x in (39, 43, 47):                                       # pearlescent glow in the bay ceiling just inside
        ceiling_light(s, x, czb + 3, FROG, y_from=13)
    sh.ground_disc(s, 44, 38, 5, G, SHIP["scorch"], None, seed=12, noise=0.4, depth=1)
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
    for z in (int(cz66) - 2, int(cz66) + 1, int(cz66) + 3):      # torn cables dangling down to the furrow floor
        for y in range(15, s.top_y(67, z), -1):
            if s.is_air(67, y, z):
                s.set(67, y, z, st.chain("y"))
    s.set(64, 17, int(cz66), st.campfire(soul=True))
    for x in range(67, 73):                                      # cable lying on the furrow floor
        z = int(cz66) - 4
        s.set(x, s.top_y(x, z) + 1, z, st.log("minecraft:chain", "x"))

    # ------------------------------------------------------------------ tail / engine section (rolled the other way)
    t_outer, TU, TV = rolled_loft(TAIL, roll_tail)
    t_in1, _, _ = rolled_loft(TAIL, roll_tail, shrink=1.0)
    t_in2, _, _ = rolled_loft(TAIL, roll_tail, shrink=2.0)
    t_out = t_outer & ~t_in1
    sh.fill_mask(s, t_out, WHITE)
    sh.fill_mask(s, t_in1 & ~t_in2, LGRAY)
    paint_shell(s, t_out, TU, white_min=2.0, gray_min=-2.0)      # heavier engine block: more gray / dark
    sh.fill_mask(s, t_in2 & (ys >= 7), AIR)
    sh.fill_mask(s, t_in2 & (ys < 7), DARK)
    sh.fill_mask(s, t_in2 & (ys == 6), PDS)
    absTV = np.abs(TV)
    sh.fill_mask(s, t_out & (np.abs(TU) <= 0.55) & (absTV > 2.5), DARK)                         # belt line
    sh.fill_mask(s, t_out & (xs >= 83) & (xs <= 91) & (TU < -0.6) & (TU >= -1.7) & (absTV > 4), PURPUR)
    sh.fill_mask(s, t_out & (xs >= 83) & (xs <= 91) & (TU < -2.6) & (TU >= -3.6) & (absTV > 3.5), COPPER)   # pipes
    for x in range(84, 91):
        win = t_out[x] & (TU[x] >= 2.4) & (TU[x] < 3.5) & (absTV[x] >= 4.5)
        for (y, z) in np.argwhere(win):
            s.set(x, y, z, GLASS if x != 87 else IRON)
        if x % 3 == 0:                                            # iron vents low on the flanks
            vent = t_out[x] & (TU[x] >= -4.6) & (TU[x] < -3.6) & (absTV[x] >= 2.5)
            for (y, z) in np.argwhere(vent):
                s.set(x, y, z, st.trapdoor("iron", "north" if TV[x, y, z] < 0 else "south", "top", open=False))
    for xr in (84, 87, 90):
        m = t_out & (xs == xr)
        sh.fill_mask(s, m, PDS)
        sh.fill_mask(s, m & (np.abs(TU) < 1.5), IRON)
    t_ridge = ridge_of(t_outer, 80, 93)
    bevel_hull(s, t_outer, TU, lambda x: ry_of(TAIL, x), 80, 93, skip=lambda x, y, z: x <= 82, thr=(2.0, -2.0))
    cyt, czt = cy_of(TAIL, 93), cz_of(TAIL, 93)
    sh.fill_mask(s, t_outer & (xs == 93), PDS)
    sh.fill_mask(s, t_outer & (xs == 92), DARK)
    # three nozzles behind the tail face (two big, a smaller one on top between them): basalt cone with dark collars,
    # iron ring, sea-lantern throat behind cyan glass, cyan lip, soul smoke
    for (dz, dy, r) in ((-3.6, -0.3, 3.3), (3.6, -0.3, 3.3), (0.0, 3.4, 1.7)):
        ncz, ncy = czt + dz, cyt + dy
        big = r > 2
        sh.cylinder(s, 93, ncy, ncz, r, 5, BASALT_P, axis="x", hollow=big, thickness=1.0, r2=r - 0.5)
        sh.cylinder(s, 93, ncy, ncz, r + 0.5, 0, UNDER, axis="x", hollow=True, thickness=1.5)     # root collar
        sh.cylinder(s, 96, ncy, ncz, r + 0.1, 0, UNDER, axis="x", hollow=True, thickness=1.2)     # mid collar
        if big:
            sh.cylinder(s, 93, ncy, ncz, r - 1.0, 1, IRON, axis="x", hollow=True, thickness=1.0)
            sh.cylinder(s, 93, ncy, ncz, r - 1.7, 2, LANTERN, axis="x")
            sh.cylinder(s, 96, ncy, ncz, r - 1.3, 1, SHIP["engine_glow"], axis="x")
            sh.cylinder(s, 98, ncy, ncz, r - 0.5, 0, SHIP["engine_glow"], axis="x", hollow=True, thickness=1.0)
            sh.cylinder(s, 98, ncy, ncz, r - 1.5, 0, LANTERN, axis="x")
        else:
            sh.cylinder(s, 97, ncy, ncz, r - 0.5, 1, SHIP["engine_glow"], axis="x")
            sh.cylinder(s, 94, ncy, ncz, r - 1.0, 2, LANTERN, axis="x")
        zi = int(round(ncz))
        top = s.top_y(97, zi)
        s.set(97, top + 1, zi, st.campfire(soul=True))
    s.set(101, s.top_y(101, int(round(czt + 2))) + 1, int(round(czt + 2)), st.campfire(soul=True))
    for x in range(93, 99):                                      # dark keel skid under the nozzles
        z = int(round(czt))
        for dz in (-1, 0, 1):
            if s.is_air(x, G + 1, z + dz) and not s.is_air(x, G + 2, z + dz):
                s.set(x, G + 1, z + dz, UNDER)
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
        ceiling_light(s, x, czr + 3, COPPER)
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
    for (y, z) in ((8, int(cz80) - 3), (9, int(cz80) + 3)):      # broken pipe stubs sticking out of the cut face
        for x in (77, 78, 79):
            if s.is_air(x, y, z):
                s.set(x, y, z, COPPER)
    for z in (int(cz80) - 1, int(cz80) + 2):                      # cables down to the furrow floor
        for y in range(15, s.top_y(79, z), -1):
            if s.is_air(79, y, z):
                s.set(79, y, z, st.chain("y"))
    s.set(81, 18, int(cz80), st.campfire(soul=True))
    # swept vertical fin: a 2-thick plate on the rolled ridge, top edge rising toward the rear, dark trailing edge
    # post, quartz stair steps on the leading edge, a cyan/purple glass strip
    fin_cols = []
    for x in range(82, 93):
        z0 = t_ridge[x]
        top = 19.0 + (x - 82) * 0.65
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
            if 86 <= x <= 91 and hi - 1 > ty + 1:
                s.set(x, hi - 1, z, SHIP["engine_glow"] if x != 88 else PGLASS)
            if x == 92:
                for y in range(ty + 1, hi + 1):
                    s.set(x, y, z, DARK)
        fin_cols.append((x, z0, hi))
    x, z0, hi = fin_cols[-1]
    s.set(x, hi + 1, z0, st.end_rod("up"))
    s.set(82, s.top_y(82, t_ridge[82]) + 1, t_ridge[82], st.stairs("quartz", "east", "bottom"))

    # ------------------------------------------------------------------ hull exterior details
    for x in range(24, 62, 6):                                   # iron vent panels on the flanks
        cy = cy_of(MAIN, x)
        y = int(round(cy - 2.5))
        for side in (-1, 1):
            z = first_solid_z(s, outer, x, y, side > 0)
            if z is not None and (side < 0 or not (33 <= x <= 55)):
                s.set(x, y, z, st.trapdoor("iron", "north" if side < 0 else "south", "top", open=False))
    hx = 44                                                      # top cargo hatch (open) beside the spine, ladder into the bay
    hz = ridge[hx] + 2
    ty = s.top_y(hx, hz)
    for x in (hx, hx + 1):
        for z in (hz, hz + 1):
            for y in range(7, ty + 1):
                s.set(x, y, z, AIR)
    for y in range(7, ty + 1):
        if s.is_air(hx, y, hz + 2):
            s.set(hx, y, hz + 2, PDS)
        s.set(hx, y, hz + 1, "minecraft:ladder[facing=north]")
    s.set(hx - 1, ty, hz + 1, st.trapdoor("iron", "east", "top", open=True))
    s.set(hx + 2, ty, hz, st.trapdoor("iron", "west", "top", open=True))
    s.set(hx, ty, hz - 1, LANTERN)
    s.set(hx + 1, ty, hz - 1, LANTERN)
    ax, az = 56, ridge[56]                                       # dorsal comms mast: iron lattice, rods, dish arms
    ty = s.top_y(ax, az)
    s.set(ax, ty + 1, az, IRON)
    for y in range(ty + 2, ty + 5):
        s.set(ax, y, az, "minecraft:iron_bars")
    s.set(ax, ty + 5, az, IRON)
    s.set(ax, ty + 6, az, st.lightning_rod("up"))
    s.set(ax, ty + 7, az, st.lightning_rod("up"))
    for dz in (-1, 1):
        s.set(ax, ty + 5, az + dz, st.end_rod("east" if dz < 0 else "west"))
        s.set(ax, ty + 5, az + 2 * dz, st.end_rod("up"))
    s.set(ax + 2, s.top_y(ax + 2, az) + 1, az, st.end_rod("up"))
    s.set(ax - 2, s.top_y(ax - 2, az) + 1, az, st.end_rod("up"))
    for x in range(20, 62, 7):                                   # running lights on the belt line
        for side in (-1, 1):
            if 33 <= x <= 55 and side > 0:
                continue
            cells = np.argwhere(belt[x] & ((V[x] > 0) if side > 0 else (V[x] < 0)))
            if len(cells) == 0:
                continue
            y, z = cells[np.argmax(cells[:, 1] * side)]
            s.set(x, y, z, FROG)

    # ------------------------------------------------------------------ crystals of the Neige world around the impact
    for (x, z, h) in ((3, 9, 3), (2, 33, 5), (9, 37, 2), (18, 6, 4), (7, 40, 1), (26, 43, 3)):
        ty = s.top_y(x, z)
        for y in range(ty + 1, ty + 1 + h):
            s.set(x, y, z, "minecraft:amethyst_block")
        s.set(x, ty + 1 + h, z, "minecraft:amethyst_cluster[facing=up]")
        s.set(x + 1, ty + 1, z, "minecraft:large_amethyst_bud[facing=up]")
        s.set(x - 1, ty + 1, z + 1, "minecraft:medium_amethyst_bud[facing=up]")

    # ------------------------------------------------------------------ debris trail, snow drift, weathering
    debris = [IRON, SHIP["damage_fill"], st.slab("deepslate_tile"), st.stairs("deepslate_tile", "east"),
              "minecraft:barrel[facing=up,open=false]", BASALT_P, st.log("minecraft:chain", "x"), PDS,
              st.trapdoor("iron", "north", "bottom", open=False), st.slab("quartz"), WHITE]
    for _ in range(64):
        x = rng.randint(64, W - 2)
        half = furrow_half(x)
        z = int(round(furrow_center(x) + rng.uniform(-half + 1.0, half - 1.0)))
        if 0 < z < L - 1 and s.top_y(x, z) <= G:
            s.set(x, s.top_y(x, z) + 1, z, rng.choice(debris))
    for (x, z) in ((70, 28), (74, 24), (86, 40), (99, 36), (104, 33), (95, 30)):   # hull-fragment clusters
        ty = s.top_y(x, z)
        if ty > G:
            continue
        s.set(x, ty + 1, z, WHITE)
        s.set(x + 1, ty + 1, z, st.stairs("deepslate_tile", "east"))
        s.set(x, ty + 1, z + 1, st.slab("quartz"))
        s.set(x, ty + 2, z, st.slab("deepslate_tile"))
        s.set(x - 1, ty + 1, z, st.trapdoor("iron", "north", "bottom", open=False))
    for x in range(12, 66):                                      # leeward snow drift wedge against the north flank
        zmin = first_solid_z(s, outer, x, G + 1, False)
        zmin2 = first_solid_z(s, outer, x, G + 2, False)
        zmin = min([v for v in (zmin, zmin2) if v is not None], default=None)
        if zmin is None:
            continue
        for dz in range(0, 9):
            z = zmin - dz
            n = sh.value_noise2(x, z, 17, 5.0)
            h = int(round(4.0 - dz * 0.5 + 1.2 * n - 0.6))
            for y in range(G + 1, G + 1 + h):
                if s.is_air(x, y, z):
                    s.set(x, y, z, GROUND["snow"])
            if h > 0 and s.is_air(x, G + 1 + h, z):
                s.set(x, G + 1 + h, z, st.snow_layer(2 + int(4 * n)))
    for x in range(80, 94):                                      # drift against the tail's north flank
        zmin = first_solid_z(s, t_outer, x, G + 1, False)
        if zmin is None:
            continue
        for dz in range(0, 6):
            z = zmin - dz
            n = sh.value_noise2(x, z, 19, 5.0)
            h = int(round(3.0 - dz * 0.55 + n))
            for y in range(G + 1, G + 1 + h):
                if s.is_air(x, y, z):
                    s.set(x, y, z, GROUND["snow"])
    for z in range(int(cz80) - 6, int(cz80) + 7):                 # drift piled against the tail's cut face
        for dx in range(0, 4):
            x = 79 - dx
            n = sh.value_noise2(x, z, 31, 4.0)
            h = int(round(2.5 - dx * 0.6 - abs(z - cz80) * 0.2 + n))
            for y in range(s.top_y(x, z) + 1, G + 1 + h):
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
    # light snow on the leeward (north) half of the top ridge only, never on the head crown, flanks or belt
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
                ok = U[x, ty, z] >= ry_of(HULL, x) - 1.5 and z <= ridge[x] and not (20 <= x <= 38)
            elif 80 <= x <= 93 and t_outer[x, ty, z]:
                ok = TU[x, ty, z] >= ry_of(TAIL, x) - 1.5 and z <= t_ridge[x]
            elif ty <= y_wing + 3:
                ok = True                                          # wings, nacelles, spilled crates
            if ok and snow_rng.random() < 0.3 * (0.5 + sh.value_noise2(x, z, 3, 6.0)):
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

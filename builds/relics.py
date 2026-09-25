"""Relics: two 'special' set pieces for the snow world.

alien_skeleton  - a giant frozen alien creature, half-buried: curved spine, twelve thin barrel-arched ribs (plus one
                  lying loose), a horned skull with dark eye sockets, pelvis, one fore-limb bent and reaching over the
                  snow with three curled claws, tall tapered blue crystal spikes grown through the bones, a wind-blown
                  snow drift filling the south half of the ribcage and a small scientists' camp (4-high A-frame tent,
                  survey grid, lantern posts, journal).
mech_wreck      - a downed bipedal walker (~20 tall standing) kneeling in the snow, built from clearly articulated
                  parts: one leg folded (knee in the snow, shin flat behind, foot up on its toes), the other planted
                  forward, a boxy tilted torso with an inset chest panel, purpur accents and dark seams, a glass
                  cockpit with a cracked corner, a sensor head with a red eye, an arm cannon dug into a crater, the
                  other arm raised with a 3-finger claw, exhaust stacks with blue smoke, torn cables, scorched snow.
"""
import math
import random

import numpy as np

from tools.schem import Schematic, AIR
from tools import shapes as sh, states as st
from tools.palette import GROUND, SHIP, CAMP, CRYSTAL, MIX_SCORCH, MIX_SNOW, MIX_WHITE

BONE = "minecraft:bone_block"
BONE_DARK = "minecraft:polished_deepslate"          # shadow / structure line on the underside of bones
SNOW = GROUND["snow"]


# ----------------------------------------------------------------------------------------------- small helpers
def bone(axis="y"):
    return st.log(BONE, axis)


def axis_of(dx, dy, dz):
    ax, ay, az = abs(dx), abs(dy), abs(dz)
    if ax >= ay and ax >= az:
        return "x"
    return "y" if ay >= az else "z"


def line6(p1, p2):
    """Integer cells from p1 to p2 that are 6-connected (never a diagonal-only step), without duplicates."""
    n = max(int(math.ceil(2 * max(abs(p2[k] - p1[k]) for k in range(3)))), 1)
    out, seen, prev = [], set(), None
    for i in range(n + 1):
        t = i / n
        cur = [int(round(p1[k] + (p2[k] - p1[k]) * t)) for k in range(3)]
        if prev is None:
            step = [cur]
        else:
            step, cell = [], list(prev)
            for k in (1, 0, 2):                                  # y first, then x, then z
                while cell[k] != cur[k]:
                    cell[k] += 1 if cur[k] > cell[k] else -1
                    step.append(list(cell))
        for c in step:
            c = tuple(c)
            if c not in seen:
                seen.add(c)
                out.append(c)
        prev = cur
    return out


def bone_line(s, p1, p2, r=1.0):
    """A solid bone (3 thick when r=1) with the pillar axis following the segment."""
    ax = axis_of(p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    if r <= 0:
        for (x, y, z) in line6(p1, p2):
            s.set(x, y, z, bone(ax))
    else:
        sh.line(s, p1, p2, bone(ax), radius=r)


def clip_below(s, y_keep, replace):
    """Everything strictly under y_keep becomes `replace` (bones sinking into the ground)."""
    sub = s.data[:, :y_keep, :]
    sub[sub != 0] = s.pid(replace)


def crystal_spike(s, base, tip, r0, seed=1):
    """A tall tapered crystal spike leaning off vertical: wide blue-ice base thinning to a single block, then a
    pointed-dripstone point; light-blue glass facets, amethyst clusters growing out of the flanks, a sea lantern
    buried under the base for a cold glow."""
    rng = random.Random(seed)
    n = max(int(2 * max(abs(tip[k] - base[k]) for k in range(3))), 2)
    top = None
    for i in range(n + 1):
        t = i / n
        x, y, z = (base[k] + (tip[k] - base[k]) * t for k in range(3))
        r = r0 * (1 - t) ** 1.15
        if r < 0.1:
            break
        if t < 0.15:
            blk = GROUND["ice"] if rng.random() < 0.5 else GROUND["ice_light"]
        else:
            blk = GROUND["ice_glass"] if rng.random() < 0.28 else GROUND["ice_light"]
        sh.sphere(s, x, y, z, r, blk)
        top = (round(x), round(y), round(z))
    if top is not None:                                          # dripstone point on top of the last crystal block
        x, y, z = top
        ty = s.top_y(x, z)
        if ty >= y and s.is_air(x, ty + 1, z) and s.is_air(x, ty + 2, z):
            s.set(x, ty + 1, z, st.pointed_dripstone("up", "frustum"))
            s.set(x, ty + 2, z, st.pointed_dripstone("up", "tip"))
    s.set(round(base[0]), round(base[1]) - 1, round(base[2]), CRYSTAL["glow_cold"])
    # clusters / buds growing sideways out of the flanks
    for t in (0.18, 0.32, 0.46, 0.6):
        x, y, z = (round(base[k] + (tip[k] - base[k]) * t) for k in range(3))
        for (dx, dz, facing) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            if rng.random() < 0.55:
                continue
            for d in range(1, 4):
                px, pz = x + dx * d, z + dz * d
                if s.is_air(px, y, pz):
                    nb = s.get(px - dx, y, pz - dz)
                    if "ice" in nb or "glass" in nb:
                        blk = CRYSTAL["cluster"] if rng.random() < 0.6 else CRYSTAL["bud"]
                        s.set(px, y, pz, blk + f"[facing={facing}]")
                    break


# =================================================================================================== SKELETON
def build_skeleton():
    W, H, L, G = 60, 26, 30, 3
    s = Schematic(W, H, L, ground=G)
    rng = random.Random(7)
    sh.ground_slab(s, G, SNOW, depth=4)
    ZC = 15

    # ---------------------------------------------------------------- spine path (parametric)
    X0, X1 = 16, 59

    def spine(x):
        t = (x - X0) / (X1 - X0)
        if t <= 0.5:
            y = G + 5.5 + 5.0 * math.sin(math.pi * t)
        else:
            y = G + 10.5 - 8.0 * ((t - 0.5) / 0.5) ** 2.2
        z = ZC + 1.8 * math.sin(2 * math.pi * t) + (6.0 * ((t - 0.75) / 0.25) ** 1.3 if t > 0.75 else 0)
        return y, z

    rib_xs = list(range(17, 52, 3))                          # 12 ribs, 3 apart (1 wide -> 2-block gaps)
    spine_xs = rib_xs[::2] + [54]                            # vertebrae carrying a neural spine

    def rib_rz(x):
        sz = 1 - 0.5 * ((x - 34) / 16.0) ** 2
        return 2.0 + 7.5 * sz

    # ---------------------------------------------------------------- rib cage: thin barrel arcs
    icicles = []
    dark_pts = []

    def rib_points(x0, side, ys, zs, ry, rz, phi_max, sweep):
        pts = []
        n = 60
        for k in range(n + 1):
            u = k / n
            phi = math.radians(phi_max) * u
            pts.append((x0 + sweep * u, ys - 1 - ry * (1 - math.cos(phi)), zs + side * (1 + rz * math.sin(phi)), phi, u))
        return pts

    def draw_rib(s, pts, side, break_at=None):
        cells = []
        prev = None
        for (x, y, z, phi, u) in pts:
            if break_at is not None and phi > break_at:
                break
            cur = (round(x), round(y), round(z))
            if prev is None:
                cells.append((cur, phi, u))
            elif cur != prev:
                for c in line6(prev, cur)[1:]:                    # keep the arc 6-connected
                    cells.append((c, phi, u))
            prev = cur
        seen = set()
        got_icicle = False
        for ((xi, yi, zi), phi, u) in cells:
            if (xi, yi, zi) in seen:
                continue
            seen.add((xi, yi, zi))
            ax = axis_of(0.2, -math.sin(phi), math.cos(phi))
            s.set(xi, yi, zi, bone(ax))
            if u > 0.5:                                          # dark structure line on the cage side, lower part only
                dark_pts.append((xi, yi, zi - side))
            if side == -1 and not got_icicle and 0.3 < u < 0.42:
                icicles.append((xi, yi - 1, zi))
                got_icicle = True

    for i, x in enumerate(rib_xs):
        ys, zs = spine(x)
        rz = rib_rz(x)
        ry = ys - 1 - G
        for side in (-1, 1):
            if side == -1 and i == 4:                          # missing rib (lies loose on the snow, see below)
                continue
            broken = None
            if side == -1 and i in (2, 7):                     # two broken ribs on the exposed (north) side
                broken = math.radians(50 if i == 2 else 72)
            pts = rib_points(x, side, ys, zs, ry, rz, 115, 2.0)
            draw_rib(s, pts, side, broken)
    # the missing rib lies broken on the snow north of the cage (two pieces)
    for (a, b) in (((28, G + 1, 4), (34, G + 1, 3)), ((36, G + 1, 4), (40, G + 2, 6))):
        bone_line(s, a, b, r=0.6)
    s.set(40, G + 1, 6, bone("z"))

    # ---------------------------------------------------------------- vertebral column (drawn after the ribs)
    prev = None
    for x in range(X0, X1 + 1):
        y, z = spine(x)
        yi, zi = round(y), round(z)
        ax = axis_of(1, y - prev[0], z - prev[1]) if prev else "x"
        s.set(x, yi, zi, bone(ax))
        if 18 <= x <= 54:                                      # thick thoracic + lumbar column, dark underside
            s.set(x, yi, zi - 1, bone(ax)); s.set(x, yi, zi + 1, bone(ax))
            s.set(x, yi - 1, zi, BONE_DARK)
        elif x > 54:                                           # tail: 2 wide, always 6-connected to the previous vertebra
            s.set(x, yi, zi - 1, bone(ax)); s.set(x - 1, yi, zi, bone(ax))
        if x in spine_xs:                                      # neural spines on every other rib vertebra
            hgt = 2 if 26 <= x <= 46 else 1
            for k in range(1, hgt + 1):
                s.set(x, yi + k, zi, bone("y"))
            s.set(x, yi + hgt + 1, zi, st.pointed_dripstone("up", "tip"))
        prev = (y, z)
    for (x, y, z) in dark_pts:                                 # dark structure line on the inner face of each rib
        if s.is_air(x, y, z) or "bone" in s.get(x, y, z):
            s.set(x, y, z, BONE_DARK)

    # ---------------------------------------------------------------- pelvis + hind leg
    px = 54
    py, pz = spine(px)
    py, pz = round(py), round(pz)
    for side in (-1, 1):
        hip = (px, py - 2, pz + side * 4)
        for (ex, ey, ez) in ((px - 3, py - 4, pz + side * 5), (px + 3, py - 4, pz + side * 5)):
            bone_line(s, (px, py, pz + side), (ex, ey, ez), r=0.7)
        bone_line(s, (px, py, pz + side), hip, r=0.9)
        sh.sphere(s, *hip, 1.6, BONE)                          # hip socket knob
    # north hind leg: femur rising out of the snow to a knee, shin sinking back in
    hip_n = (px, py - 2, pz - 4)
    knee = (50, G + 5, pz - 9)
    bone_line(s, hip_n, knee, r=1.0)
    sh.sphere(s, *knee, 1.6, BONE)
    bone_line(s, knee, (46, G + 1, pz - 12), r=0.9)
    bone_line(s, (46, G + 1, pz - 12), (44, G - 1, pz - 13), r=0.9)

    # ---------------------------------------------------------------- skull (snout raised to the sky, jaw open)
    secs = [(1, G + 7.2, ZC, 1.0, 1.1), (4, G + 6.6, ZC, 1.8, 2.0), (8, G + 5.8, ZC, 2.7, 3.0),
            (12, G + 5.2, ZC, 3.6, 4.2), (16, G + 5.0, ZC, 3.4, 3.8), (18, G + 5.2, ZC, 2.4, 2.4)]
    sh.loft(s, secs, BONE, axis="x")
    sh.ellipsoid(s, 14, G + 6.2, ZC, 4.2, 2.8, 4.4, BONE)      # brow ridges + cranium dome
    for side in (-1, 1):                                       # eye sockets: recessed dark hollows
        cz = ZC + side * 4.0
        bone_mask = s.data == s.pid(BONE)
        outer = sh._mask_ellipsoid(s, 12.5, G + 6.5, cz, 2.1, 1.7, 1.9) & bone_mask
        inner = sh._mask_ellipsoid(s, 12.5, G + 6.5, cz + side * 0.8, 1.3, 1.0, 1.4)
        sh.fill_mask(s, outer, "minecraft:blackstone")
        sh.fill_mask(s, inner, AIR)
    for side in (-1, 1):                                       # nostrils
        s.set(3, G + 8, ZC + side, "minecraft:blackstone")
    for side in (-1, 1):                                       # swept-back horns
        bone_line(s, (15, G + 8, ZC + side * 2), (19, G + 10, ZC + side * 4), r=1.0)
        bone_line(s, (19, G + 10, ZC + side * 4), (22, G + 11, ZC + side * 6), r=0.6)
        s.set(23, G + 12, ZC + side * 6, st.pointed_dripstone("up", "tip"))
    # lower jaw: two bones from the hinge to the tip, resting on the snow
    for side in (-1, 1):
        bone_line(s, (15, G + 3, ZC + side * 4), (9, G + 2, ZC + side * 3), r=0.7)
        bone_line(s, (9, G + 2, ZC + side * 3), (3, G + 1, ZC + side * 1.5), r=0.6)
    bone_line(s, (3, G + 1, ZC - 2), (2, G + 1, ZC + 2), r=0.4)
    # teeth: upper (hanging under the snout) and lower (on the jaw bones)
    for x in range(3, 13, 2):
        for side in (-1, 1):
            zz = round(ZC + side * (1.2 + (x - 3) * 0.28))
            col = [y for y in range(G + 1, H) if "bone" in s.get(x, y, zz)]
            if col:
                ylow = min(col)
                if s.is_air(x, ylow - 1, zz) and ylow - 1 > G + 1:
                    s.set(x, ylow - 1, zz, st.pointed_dripstone("down", "tip"))
    for x in range(4, 12, 3):
        for side in (-1, 1):
            zz = round(ZC + side * (1.5 + (x - 3) * 0.28))
            ty = s.top_y(x, zz)
            if ty >= G + 1 and "bone" in s.get(x, ty, zz) and s.is_air(x, ty + 1, zz):
                s.set(x, ty + 1, zz, st.pointed_dripstone("up", "tip"))

    # ---------------------------------------------------------------- bent fore-limb reaching over the north side
    sy, sz_ = spine(26)
    shoulder = (26, round(sy) - 1, 11)                                       # scapula, just under the column
    elbow = (31, G + 13, 6)                                                   # humerus leans back (towards the tail)
    wrist = (25, G + 18, 5)                                                   # forearm leans forward, over the ribs
    bone_line(s, (26, round(sy), round(sz_) - 1), shoulder, r=1.0)
    bone_line(s, shoulder, elbow, r=1.2)                                     # humerus
    bone_line(s, elbow, wrist, r=0.9)                                        # forearm
    sh.sphere(s, *shoulder, 1.8, BONE)
    sh.sphere(s, *elbow, 1.9, BONE)
    sh.sphere(s, elbow[0], elbow[1] - 1, elbow[2], 1.0, BONE_DARK)          # dark shadow under the elbow
    sh.sphere(s, *wrist, 1.4, BONE)
    # three curled digits: knuckle up and forward, tip curling down, dripstone claw
    for k in (-1, 0, 1):
        knuckle = (22, G + 20 + (1 if k == 0 else 0), 5 + 2 * k)
        tip = (19, G + 18, 5 + 3 * k)
        for (a, b, fat) in (((wrist[0] - 1, wrist[1] + 1, wrist[2] + k), knuckle, True), (knuckle, tip, False)):
            cells = line6(a, b)
            for j, (x, y, z) in enumerate(cells):
                s.set(x, y, z, bone(axis_of(b[0] - a[0], b[1] - a[1], b[2] - a[2])))
                if fat and j < len(cells) // 2:                 # thicker at the base of the digit
                    s.set(x, y - 1, z, bone("y"))
        s.set(tip[0], tip[1] - 1, tip[2], st.pointed_dripstone("down", "frustum"))
        s.set(tip[0], tip[1] - 2, tip[2], st.pointed_dripstone("down", "tip"))
    s.set(24, G + 17, 5, CRYSTAL["ice"])                                     # crystal grown in the palm
    s.set(24, G + 16, 5, CRYSTAL["cluster"] + "[facing=down]")
    s.set(23, G + 18, 5, CRYSTAL["cluster"] + "[facing=west]")
    # the other fore-limb: buried, only the shoulder blade shows on the south side
    sy2, sz2 = spine(27)
    bone_line(s, (27, round(sy2) - 1, round(sz2) + 2), (29, G + 1, round(sz2) + 8), r=1.0)

    # ---------------------------------------------------------------- bones sink into the ground
    clip_below(s, G + 1, SNOW)
    s.data[:, :G + 1, :][s.data[:, :G + 1, :] == 0] = s.pid(SNOW)

    # ---------------------------------------------------------------- crystals grown through the bones
    crystal_spike(s, (39, G + 1, 20), (42, G + 13, 24), 2.1, seed=1)        # grows through rib 38 (south)
    crystal_spike(s, (37, G + 1, 23), (36, G + 6, 25), 1.2, seed=11)
    crystal_spike(s, (31, G + 1, 9), (27, G + 12, 6), 1.9, seed=2)          # through rib 29 (north, the missing one)
    crystal_spike(s, (33, G + 1, 8), (34, G + 6, 6), 1.1, seed=12)
    crystal_spike(s, (47, G + 1, 21), (49, G + 10, 24), 1.5, seed=3)
    crystal_spike(s, (22, G + 1, 24), (20, G + 8, 26), 1.2, seed=4)
    crystal_spike(s, (55, G + 1, 25), (58, G + 9, 27), 1.4, seed=5)
    crystal_spike(s, (57, G + 1, 23), (59, G + 5, 23), 0.9, seed=13)
    for (x, y, z) in icicles:                                              # icicles under the north ribs
        if s.is_air(x, y, z) and not s.is_air(x, y + 1, z):
            s.set(x, y, z, st.pointed_dripstone("down", "frustum"))
            if s.is_air(x, y - 1, z):
                s.set(x, y - 1, z, st.pointed_dripstone("down", "tip"))
    for _ in range(16):                                                    # amethyst clusters on random bones
        x, z = rng.randint(16, 54), rng.randint(3, 27)
        ty = s.top_y(x, z)
        if ty > G and "bone" in s.get(x, ty, z) and s.is_air(x, ty + 1, z):
            s.set(x, ty + 1, z, (CRYSTAL["cluster"] if rng.random() < 0.7 else CRYSTAL["bud"]) + "[facing=up]")

    # ---------------------------------------------------------------- wind-blown drift filling the south half of the cage
    for x in range(22, 60):
        sy_, szx = spine(x)
        zw = szx + 1 + rib_rz(x) * 0.95                                    # where the south rib wall meets the snow
        prof = max(0.0, 1 - ((x - 40) / 18.0) ** 2)
        for z in range(ZC - 2, L):
            d = z - zw
            if d >= 0:
                f = max(0.0, 1 - (d / 3.5) ** 2)                           # spills 2-3 blocks outside the last rib
            else:
                f = max(0.0, 1 - (-d / 10.0) ** 1.4)                       # fades towards the spine
            h = 5.2 * prof * f * (0.8 + 0.4 * sh.value_noise2(x, z, 21, 7.0))
            if x > 52:                                                     # tail buried under a long dune
                h = max(h, 3.0 * max(0.0, 1 - ((z - szx) / 7.0) ** 2) * (1 - (x - 52) / 9.0))
            for y in range(G + 1, G + 1 + int(round(h))):
                s.set_if_air(x, y, z, SNOW)
    # small drifts against the skull, the north ribs and the femur
    for (cx, cz, r, hh) in ((6, ZC + 4, 4, 1.5), (10, ZC - 5, 4, 1.5), (34, ZC - 12, 6, 1.5), (47, 4, 4, 1.5), (56, ZC + 2, 5, 2)):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                d = math.hypot(x - cx, z - cz) / r
                if d < 1:
                    h = hh * (1 - d * d) * (0.7 + 0.6 * sh.value_noise2(x, z, 5, 4.0))
                    for y in range(G + 1, G + 1 + int(round(h))):
                        s.set_if_air(x, y, z, SNOW)
    # loose shards / a half-buried vertebra filling the empty north quadrant
    for (x, z, ax) in ((33, 9, "x"), (45, 5, "x"), (52, 5, "z"), (12, 5, "z"), (22, 3, "x"), (49, 26, "x")):
        ty = s.top_y(x, z)
        s.set(x, ty + 1, z, bone(ax))
        if ax == "x":
            s.set(x + 1, ty + 1, z, bone(ax))
        for (dx, dz) in ((0, 1), (0, -1), (-1, 0), (2 if ax == "x" else 1, 0)):
            if s.is_air(x + dx, ty + 1, z + dz):
                s.set(x + dx, ty + 1, z + dz, st.snow_layer(rng.randint(1, 3)))
    sh.sphere(s, 46, G + 1, 7, 1.2, BONE)                                  # a vertebra sticking out of the drift

    # ---------------------------------------------------------------- scientists' camp (south-west, by the skull)
    tx1, tx2, tz = 9, 15, 24                                               # A-frame tent, ridge along x, 4 high
    RIDGE = "minecraft:stripped_spruce_log"
    for x in range(3, 21):                                                 # trodden pad (irregular)
        for z in range(18, 29):
            if math.hypot((x - 12) / 8.5, (z - 24) / 5.0) < 0.75 + 0.5 * sh.value_noise2(x, z, 9, 3.0):
                s.set(x, G, z, CAMP["trodden_snow"])
    for x in range(tx1 + 1, tx2):                                          # plank floor inside
        for dz in range(-2, 3):
            s.set(x, G, tz + dz, CAMP["plank_light"])
    for x in range(tx1, tx2 + 1):
        for dy in range(4):
            y = G + 1 + dy
            for side in (-1, 1):
                facing = "north" if side == 1 else "south"                 # tall side towards the ridge
                s.set(x, y, tz + side * (4 - dy), st.stairs("quartz", facing))
                if 3 - dy > 0:
                    blk = CAMP["tent_accent"] if x in (tx1 + 3,) else CAMP["tent"]
                    s.set(x, y, tz + side * (3 - dy), blk)
        s.set(x, G + 4, tz, st.log(RIDGE, "x"))                            # dark ridge beam
    for dy in range(3):                                                    # east gable closed (cyan diamond)
        for dz in range(-(2 - dy), 3 - dy):
            blk = CAMP["tent_accent"] if abs(dz) + dy <= 1 else CAMP["tent"]
            s.set(tx2, G + 1 + dy, tz + dz, blk)
    s.set(tx1, G + 3, tz, CAMP["tent_accent"])                             # west gable open, small cyan peak
    # guy ropes at both gables + banners
    for (gx, dx) in ((tx1, -1), (tx2, 1)):
        s.set(gx + dx, G + 4, tz, st.chain("x"))
        s.set(gx + 2 * dx, G + 4, tz, st.chain("x"))
        for y in range(G + 1, G + 5):
            s.set(gx + 3 * dx, y, tz, CAMP["pole"])
    s.set(tx1 - 3, G + 2, tz + 1, st.wall_banner("cyan", "south"))
    s.set(tx2 + 3, G + 2, tz - 1, st.wall_banner("white", "north"))
    # interior: bed, hanging lantern under the ridge, table with candle, barrel, loot chest
    s.set(12, G + 1, tz - 1, st.bed(CAMP["bed"], "east", "head"))
    s.set(11, G + 1, tz - 1, st.bed(CAMP["bed"], "east", "foot"))
    s.set(12, G + 3, tz, st.lantern(hanging=True))
    s.set(13, G + 1, tz + 1, CAMP["table"])
    s.set(13, G + 2, tz + 1, st.candle("cyan", 2))
    s.set(14, G + 1, tz + 1, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(14, G + 1, tz - 1, "west", "minecraft:chests/igloo_chest")
    # leeward (north) drift piling against the tent
    for x in range(tx1 - 1, tx2 + 2):
        for dz in (5, 6, 7):
            h = (3 - (dz - 5)) * (0.5 + 0.5 * sh.value_noise2(x, dz, 17, 3.0)) - (0.6 if x in (tx1 - 1, tx2 + 1) else 0)
            for y in range(G + 1, G + 1 + int(round(h))):
                s.set_if_air(x, y, tz - dz, SNOW)
    # outside: campfire ring, lantern posts, journal on a lectern, crates + radio
    s.set(5, G + 1, tz, st.campfire())
    for (x, z) in ((4, tz - 1), (6, tz - 1), (4, tz + 1), (6, tz + 1)):
        s.set(x, G + 1, z, st.slab("polished_deepslate"))
    for (x, z) in ((6, 20), (19, 27)):
        s.set(x, G + 1, z, CAMP["pole"]); s.set(x, G + 2, z, CAMP["pole"]); s.set(x, G + 3, z, st.lantern())
    s.set(19, G + 1, 24, st.facing_block("minecraft:lectern", "east"))
    s.add_sign(20, G + 1, 24, "minecraft:warped_sign[rotation=4]", ["JOURNAL 12", "os de 40m", "pas terrestre", "cristaux vivants"])
    s.set(19, G + 1, 21, "minecraft:barrel[facing=up,open=false]")
    s.set(20, G + 1, 21, "minecraft:barrel[facing=east,open=false]")
    s.set(19, G + 2, 21, CAMP["radio"] + "[facing=west]")
    s.set(20, G + 2, 21, CAMP["antenna"] + "[facing=up]")
    s.set(16, G + 1, 27, SHIP["container"])                               # sample box
    s.add_sign(8, G + 1, 20, "minecraft:warped_sign[rotation=12]", ["CAMP OS-7", "equipe 3", "retour dans", "4 jours"])
    # survey grid: fence markers with cyan banners joined by rope lines (chains)
    markers_n = [(20, 2), (32, 2), (44, 2)]
    markers_s = [(26, 28), (38, 28), (50, 28)]
    for (x, z) in markers_n + markers_s + [(8, 8), (57, 20)]:
        ty = s.top_y(x, z)
        if "snow[" in s.get(x, ty, z):
            s.set(x, ty, z, AIR); ty -= 1
        s.set(x, ty, z, CAMP["trodden_snow"])
        s.set(x, ty + 1, z, CAMP["pole"]); s.set(x, ty + 2, z, CAMP["pole"])
        s.set(x, ty + 3, z, st.banner("cyan", (x * 3 + z) % 16))
    for row in (markers_n, markers_s):
        for (a, b) in zip(row[:-1], row[1:]):
            for x in range(a[0] + 1, b[0]):
                s.set_if_air(x, G + 3, a[1], st.chain("x"))
    s.add_sign(21, G + 2, 3, "minecraft:warped_sign[rotation=8]", ["SPECIMEN 7", "ne pas", "toucher", "les os"])
    s.set(21, G + 1, 3, CAMP["plank"])
    s.set(9, G + 1, 9, CAMP["pole"]); s.set(9, G + 2, 9, CAMP["pole"]); s.set(9, G + 3, 9, st.lantern(soul=True))

    # ---------------------------------------------------------------- weathering
    sh.snow_cover(s, y_min=G + 1, prob=0.14, seed=3, layers=(1, 2),
                  skip=["wool", "quartz", "glass", "ice", "amethyst", "bed", "lectern", "barrel", "concrete_powder",
                        "deepslate", "campfire", "planks", "table", "spruce"])
    sh.snow_cover(s, x1=22, z1=ZC - 2, x2=59, z2=L - 1, y_min=G + 2, prob=0.38, seed=8, layers=(1, 2),
                  skip=["bone", "ice", "glass", "amethyst", "deepslate", "wool", "quartz", "spruce", "concrete_powder"])
    sh.texturize(s, SNOW, MIX_SNOW, seed=4, region=(0, G + 1, 0, W - 1, H - 1, L - 1))
    return s.cropped(pad=1)


# =================================================================================================== MECH WRECK
ARM = "minecraft:white_concrete"
ARM2 = "minecraft:light_gray_concrete"
DARK = "minecraft:polished_deepslate"
DARK2 = "minecraft:deepslate_tiles"
JOINT = "minecraft:polished_basalt"
ACC = "minecraft:purpur_block"
IRON = "minecraft:iron_block"
_OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def vent(s, x, y, z, wall_dir):
    """Open iron trapdoor lying flat against the wall block in direction `wall_dir` from this cell."""
    s.set(x, y, z, st.trapdoor("iron", _OPP[wall_dir], "bottom", open=True))


def limb(s, p1, p2, r, plate=ARM, under=DARK):
    """Armoured limb segment: white armour tube with a dark strip along its underside."""
    sh.line(s, p1, p2, plate, radius=r)
    n = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), abs(p2[2] - p1[2]), 1)
    ri = int(round(r)) + 1
    for i in range(n + 1):
        t = i / n
        x, y, z = (round(p1[k] + (p2[k] - p1[k]) * t) for k in range(3))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                for dy in range(-ri, 1):
                    if s.get(x + dx, y + dy, z + dz) == plate and s.is_air(x + dx, y + dy - 1, z + dz):
                        s.set(x + dx, y + dy, z + dz, under)


def joint(s, x, y, z, r):
    sh.sphere(s, x, y, z, r, DARK)
    sh.sphere(s, x, y, z, r - 1.0, JOINT)


def build_mech():
    W, H, L, G = 34, 32, 30, 3
    s = Schematic(W, H, L, ground=G)
    ZC = 15
    sh.ground_slab(s, G, SNOW, depth=4)
    # scorched, trampled snow under the wreck (ragged edge, grey half-melted rim) + crater where the cannon dug in
    sh.ground_disc(s, 15, ZC, 9.0, G, SHIP["scorch"], rim_block=None, seed=8, noise=0.4, depth=1)
    grng = random.Random(15)
    for x in range(W):
        for z in range(L):
            d = math.hypot(x - 15, z - ZC)
            if 7.5 < d < 11 and s.get(x, G, z) == SHIP["scorch"] and sh.value_noise2(x, z, 13, 3.0) < 0.3:
                s.set(x, G, z, SNOW)
            elif 8 <= d < 11.5 and s.get(x, G, z) == SNOW and grng.random() < 0.3:
                s.set(x, G, z, "minecraft:gray_concrete_powder" if grng.random() < 0.5 else "minecraft:tuff")
    sh.crater(s, 4, 6, 3.5, G, SHIP["scorch"], SNOW, "minecraft:tuff", depth=2, rim_height=1, seed=2)
    sh.texturize(s, SHIP["scorch"], MIX_SCORCH, seed=6)

    HIP_Y = G + 8
    # ---------------------------------------------------------------- pelvis + hip joints
    sh.box(s, 15, HIP_Y - 1, 13, 19, HIP_Y + 1, 17, DARK)
    sh.box(s, 16, HIP_Y - 1, 14, 18, HIP_Y + 1, 16, DARK2)
    sh.box(s, 15, HIP_Y + 1, 13, 19, HIP_Y + 1, 17, ARM2)                    # waist plate
    for z in (11, 19):
        joint(s, 17, HIP_Y, z, 1.7)

    # ---------------------------------------------------------------- SOUTH leg: folded, knee in the snow, shin flat behind
    hipA, kneeA, ankleA = (17, HIP_Y, 20), (14, G + 2, 21), (22, G + 2, 21)
    limb(s, hipA, kneeA, 1.2)                                                # thigh, nearly vertical
    limb(s, kneeA, ankleA, 1.1)                                              # shin lying on the scorch
    joint(s, *kneeA, 1.5)
    sh.box(s, 22, G + 1, 20, 22, G + 3, 22, DARK)                            # ankle band
    sh.box(s, 23, G + 1, 20, 23, G + 5, 22, ARM)                             # foot up on its toes: plate ...
    sh.box(s, 24, G + 1, 20, 24, G + 5, 22, DARK2)                           # ... and sole
    for z in range(20, 23):
        s.set(23, G + 6, z, st.stairs("quartz", "east"))                     # rounded heel
        s.set(24, G + 6, z, st.slab("polished_deepslate"))
    sh.box(s, 23, G + 3, 20, 23, G + 3, 22, DARK)                            # toe seam
    s.set(23, G + 2, 21, ACC)                                               # purpur toe stripe
    s.set(11, G + 1, 23, st.slab("purpur"))                                  # broken purpur panel by the knee
    s.set(12, G + 1, 24, st.slab("purpur"))
    s.set(11, G + 1, 24, ACC)

    # ---------------------------------------------------------------- NORTH leg: planted forward, knee up
    hipB, kneeB, ankleB = (17, HIP_Y, 10), (9, HIP_Y, 9), (9, G + 4, 9)
    limb(s, hipB, kneeB, 1.2)                                                # thigh horizontal
    limb(s, (9, HIP_Y - 1, 9), ankleB, 1.1)                                  # shin vertical
    joint(s, *kneeB, 2.0)
    sh.box(s, 6, HIP_Y - 1, 8, 6, HIP_Y + 1, 10, "minecraft:quartz_block")   # knee cap
    s.set(6, HIP_Y, 9, ACC)
    sh.box(s, 8, G + 3, 8, 10, G + 3, 10, DARK)                              # ankle band
    sh.box(s, 5, G + 1, 8, 10, G + 1, 10, DARK2)                             # foot: sole ...
    sh.box(s, 6, G + 2, 8, 10, G + 2, 10, ARM)                               # ... plate
    sh.box(s, 8, G + 2, 8, 8, G + 2, 10, DARK)                               # seam
    s.set(6, G + 2, 9, ACC)
    for z in range(8, 11):
        s.set(5, G + 2, z, st.stairs("quartz", "east"))                      # toe bevel
        s.set(4, G + 1, z, st.stairs("deepslate_tile", "east"))

    # ---------------------------------------------------------------- torso: 9 wide x 6 high x 7 deep, tilted forward
    TY0 = HIP_Y + 2                                                          # G+10
    halves_z = (11, 19)

    def torso_x(dy):
        x1 = 14 - dy // 2
        return x1, x1 + 6

    for dy in range(6):
        y = TY0 + dy
        x1, x2 = torso_x(dy)
        sh.box(s, x1, y, 11, x2, y, 19, ARM)
        sh.box(s, x1 + 1, y, 12, x2 - 1, y, 18, DARK2)                       # dark inner frame
        if dy in (0, 2):                                                     # dark base line + belt seam
            sh.box(s, x1, y, 11, x2, y, 19, DARK)
            sh.box(s, x1 + 1, y, 12, x2 - 1, y, 18, DARK2)
        # front plate one block ahead of the box, with the centre inset
        fx = x1 - 1
        for z in range(11, 20):
            if 13 <= z <= 17 and 1 <= dy <= 4:
                continue                                                     # inset centre panel
            s.set(fx, y, z, DARK if dy == 2 or z in (12, 18) else ARM)
        if dy in (1, 3):                                                     # bevel under each tilt step
            for z in range(11, 20):
                if not (13 <= z <= 17 and dy == 1):
                    s.set(fx - 1, y, z, st.stairs("quartz", "east", "top"))
    # inset centre panel: dark border, purpur core, stair frame above and below
    for dy in (1, 4):
        x1, _ = torso_x(dy)
        sh.box(s, x1, TY0 + dy, 13, x1, TY0 + dy, 17, DARK)
    for dy in (2, 3):
        x1, _ = torso_x(dy)
        s.set(x1, TY0 + dy, 13, DARK); s.set(x1, TY0 + dy, 17, DARK)
        sh.box(s, x1, TY0 + dy, 14, x1, TY0 + dy, 16, ACC)
    x1, _ = torso_x(5)
    for z in range(13, 18):
        s.set(x1 - 1, TY0 + 5, z, st.stairs("polished_deepslate", "east", "top"))
    x1, _ = torso_x(0)
    for z in range(13, 18):
        s.set(x1 - 1, TY0, z, st.stairs("polished_deepslate", "east"))
    # light strip at shoulder height (sea lantern behind light-blue glass) + vent row under it
    x1, _ = torso_x(5)
    for z in (11, 12, 18, 19):
        if z in (12, 18):
            s.set(x1, TY0 + 5, z, SHIP["light"])
        s.set(x1 - 1, TY0 + 5, z, SHIP["glass"])
    x1, _ = torso_x(4)
    for z in (11, 12, 18, 19):
        vent(s, x1 - 2, TY0 + 4, z, "east")
    # side purpur panels with a dark frame, side vents
    for z in halves_z:
        for dy in (3, 4):
            for x in range(14, 19):
                s.set(x, TY0 + dy, z, ACC if 15 <= x <= 17 else DARK)
        for x in range(15, 18):
            s.set(x, TY0 + 5, z, DARK)
        zz = z - 1 if z == 11 else z + 1
        for x in (16, 18):
            vent(s, x, TY0 + 1, zz, "south" if z == 11 else "north")
    # top plate with a bevelled rim (stairs facing inwards) and a dark centre seam
    yt = TY0 + 6                                                             # G+16
    sh.box(s, 11, yt, 11, 18, yt, 19, ARM)
    for z in range(11, 20):
        s.set(18, yt, z, st.stairs("quartz", "west"))
        if z < 13 or z > 17:
            s.set(11, yt, z, st.stairs("quartz", "east"))
    for x in range(12, 18):
        s.set(x, yt, 11, st.stairs("quartz", "south"))
        s.set(x, yt, 19, st.stairs("quartz", "north"))
    sh.box(s, 12, yt, 15, 17, yt, 15, DARK)

    # ---------------------------------------------------------------- cockpit: glass canopy on the front, cracked corner
    sh.box(s, 9, TY0 + 2, 14, 11, TY0 + 2, 16, DARK2)                        # chin support under the floor
    for z in range(13, 18):
        s.set(8, TY0 + 2, z, st.stairs("deepslate_tile", "east", "top"))
    for x in range(9, 12):
        s.set(x, TY0 + 2, 13, st.stairs("deepslate_tile", "south", "top"))
        s.set(x, TY0 + 2, 17, st.stairs("deepslate_tile", "north", "top"))
    sh.box(s, 7, TY0 + 3, 13, 10, TY0 + 3, 17, DARK2)                        # cockpit floor
    sh.box(s, 7, TY0 + 4, 13, 10, TY0 + 6, 17, SHIP["glass"])                # canopy
    sh.box(s, 8, TY0 + 4, 14, 10, TY0 + 5, 16, AIR)                          # interior
    sh.box(s, 7, TY0 + 6, 13, 7, TY0 + 6, 17, AIR)                           # slanted front top
    for z in (13, 17):
        sh.box(s, 7, TY0 + 4, z, 7, TY0 + 5, z, DARK)                        # frame posts
        s.set(8, TY0 + 6, z, DARK)
    sh.box(s, 10, TY0 + 6, 13, 10, TY0 + 6, 17, DARK)                        # roll bar at the back of the canopy
    s.set(7, TY0 + 5, 14, AIR)                                              # cracked north-west corner
    s.set(7, TY0 + 4, 14, st.glass_pane("light_blue"))
    s.set(7, TY0 + 5, 15, st.glass_pane("light_blue"))
    s.set(8, TY0 + 6, 14, st.glass_pane("light_blue"))
    s.set(10, TY0 + 4, 15, st.stairs("polished_deepslate", "east"))          # pilot seat
    s.set(8, TY0 + 4, 15, "minecraft:daylight_detector")                     # console
    s.set(8, TY0 + 4, 14, st.redstone_lamp(True))
    s.set(9, TY0 + 3, 15, SHIP["light"])                                     # floor light under the seat

    # ---------------------------------------------------------------- sensor head: red eye + antenna
    sh.box(s, 12, yt + 1, 14, 14, yt + 2, 16, DARK)
    s.set(13, yt, 15, DARK2)
    s.set(13, yt + 1, 15, SHIP["light"])
    s.set(12, yt + 1, 15, "minecraft:red_stained_glass")
    s.set(13, yt + 3, 15, st.end_rod("up"))
    s.set(13, yt + 4, 15, st.lightning_rod("up"))
    s.set(14, yt + 3, 15, st.end_rod("up"))

    # ---------------------------------------------------------------- shoulders: south pauldron, north one torn off
    SJ_Y = TY0 + 3                                                           # shoulder joint height (G+13)
    joint(s, 14, SJ_Y, 21, 1.6)
    sh.box(s, 12, TY0 + 4, 20, 17, yt, 22, ARM)                              # pauldron block
    sh.box(s, 12, TY0 + 4, 20, 17, TY0 + 4, 22, DARK)
    for x in range(12, 18):
        s.set(x, yt, 22, st.stairs("quartz", "north"))                       # rounded outer edge
        s.set(x, TY0 + 5, 22, ACC if 13 <= x <= 16 else DARK)                # purpur stripe
    s.set(11, TY0 + 5, 21, st.stairs("quartz", "east")); s.set(11, yt, 21, st.stairs("quartz", "east"))
    s.set(18, TY0 + 5, 21, st.stairs("quartz", "west")); s.set(18, yt, 21, st.stairs("quartz", "west"))
    joint(s, 14, SJ_Y, 9, 1.6)
    sh.box(s, 13, TY0 + 4, 7, 15, TY0 + 4, 10, DARK2)                        # bare mounting bracket
    sh.box(s, 13, TY0 + 5, 8, 15, TY0 + 5, 10, DARK)
    # the torn-off pauldron lying in the snow to the north-east
    sh.box(s, 24, G + 1, 2, 27, G + 1, 4, ARM)
    sh.box(s, 25, G + 2, 2, 26, G + 2, 4, ARM)
    sh.box(s, 25, G + 2, 3, 26, G + 2, 3, ACC)
    for z in range(2, 5):
        s.set(24, G + 2, z, st.stairs("quartz", "east")); s.set(27, G + 2, z, st.stairs("quartz", "west"))

    # ---------------------------------------------------------------- back: radiator, exhaust stacks with blue smoke
    for z in range(14, 17):
        vent(s, 19, TY0 + 4, z, "west"); vent(s, 19, TY0 + 5, z, "west")
    for z in (13, 17):
        sh.cylinder(s, 18, TY0 + 4, z, 1.0, 4, DARK2, axis="y")
        sh.cylinder(s, 18, TY0 + 8, z, 1.0, 0, IRON, axis="y")               # iron lip
        s.set(18, TY0 + 8, z, DARK)
        s.set(18, TY0 + 9, z, st.campfire(soul=True))

    # ---------------------------------------------------------------- NORTH arm: cannon dug into the crater
    el_n = (9, G + 9, 6)
    limb(s, (14, SJ_Y, 9), el_n, 1.1)
    joint(s, *el_n, 1.8)
    muzzle = (3, G + 1, 5)
    sh.line(s, el_n, muzzle, ARM2, radius=1.6)                              # barrel, 5 wide
    for t, blk, rr in ((0.3, DARK, 1.9), (0.52, ACC, 1.6), (0.74, DARK, 1.9)):   # dark rings + thin purpur band
        x, y, z = (round(el_n[k] + (muzzle[k] - el_n[k]) * t) for k in range(3))
        sh.sphere(s, x, y, z, rr, blk)
        sh.sphere(s, x, y, z, 1.1, ARM2)
    sh.sphere(s, *muzzle, 1.9, DARK2)                                        # muzzle ring in the crater
    sh.sphere(s, *muzzle, 1.0, "minecraft:coal_block")
    sh.texturize(s, ARM2, [(ARM2, 7), ("minecraft:polished_andesite", 2), ("minecraft:smooth_stone", 1)], seed=17)
    sh.box(s, 8, G + 9, 4, 10, G + 9, 8, ARM)                                # forearm plate over the elbow
    sh.box(s, 8, G + 9, 6, 10, G + 9, 6, ACC)

    # ---------------------------------------------------------------- SOUTH arm: raised, bent, 3-finger claw
    el_s = (14, SJ_Y + 1, 26)
    limb(s, (14, SJ_Y, 21), el_s, 1.1)                                       # upper arm out to the side
    joint(s, *el_s, 1.8)
    wr = (13, SJ_Y + 8, 26)
    limb(s, el_s, wr, 1.5)                                                   # heavy forearm / gauntlet
    sh.sphere(s, *wr, 1.7, IRON)                                             # iron wrist ring
    sh.sphere(s, *wr, 0.9, DARK)
    palm_y = wr[1] + 2
    sh.box(s, 12, palm_y, 25, 14, palm_y, 27, DARK)                          # palm
    s.set(13, palm_y, 26, SHIP["light"])
    s.set(13, palm_y + 1, 26, st.end_rod("up"))                              # sparks between the fingers
    fingers = (((12, palm_y + 1, 26), (9, palm_y + 4, 26), (10, palm_y + 5, 26), "east"),
               ((14, palm_y + 1, 27), (17, palm_y + 4, 28), (16, palm_y + 5, 28), "west"),
               ((14, palm_y + 1, 25), (17, palm_y + 4, 23), (16, palm_y + 5, 23), "west"))
    for (a, b, c, fc) in fingers:
        cells = line6(a, b)
        for j, (x, y, z) in enumerate(cells):
            s.set(x, y, z, DARK if j < len(cells) // 2 else ARM)
        for (x, y, z) in line6(b, c)[1:]:
            s.set(x, y, z, ARM)
        s.set(c[0], c[1] + 1, c[2], st.trapdoor("iron", fc, "bottom", open=True))   # claw tip
    s.set(11, palm_y + 1, 27, st.end_rod("up"))
    s.set(15, palm_y + 1, 26, st.end_rod("up"))

    # ---------------------------------------------------------------- armour texture
    sh.texturize(s, ARM, MIX_WHITE, seed=9)

    # ---------------------------------------------------------------- cables, sparks, debris, story
    hangs = ((12, 22, TY0 + 3, G + 7), (16, 22, TY0 + 3, G + 9), (13, 7, TY0 + 3, G + 5), (15, 7, TY0 + 3, G + 8))
    for (x, z, top, bot) in hangs:
        for y in range(bot, top + 1):
            s.set_if_air(x, y, z, st.chain("y"))
    s.set(12, G + 6, 22, st.lightning_rod("down"))                           # torn connector at the end of a cable
    s.set(13, G + 4, 7, st.end_rod("down"))
    for x in range(4, 10):                                                   # cable dragged from the cannon
        s.set_if_air(x, G + 1, 3, st.chain("x"))
    s.set(10, G + 1, 3, st.lightning_rod("east"))
    plates = [st.slab("quartz"), st.slab("quartz", "top"), st.trapdoor("iron", "north", "bottom", open=True),
              st.stairs("quartz", "west"), st.slab("polished_deepslate"), st.trapdoor("iron", "south", "top")]
    drng = random.Random(5)
    for _ in range(10):                                                      # armour plates in pairs, half-sunk
        x, z = drng.randint(1, W - 3), drng.randint(1, L - 3)
        if 9 < math.hypot(x - 15, z - ZC) and s.top_y(x, z) == G and s.is_air(x + 1, G + 1, z):
            p = drng.choice(plates)
            s.set(x, G + 1, z, p)
            s.set(x + drng.choice((0, 1)), G + 1, z + drng.choice((-1, 1)), drng.choice(plates))
            s.set(x - 1, G + 1, z, st.snow_layer(2))
    sh.scatter(s, 3, 18, 11, 26, ["minecraft:blackstone_slab", "minecraft:polished_blackstone_slab",
                                  "minecraft:cobbled_deepslate_slab", "minecraft:basalt"], 6, seed=21, on=["snow_block", "concrete_powder"])
    s.add_chest(12, G + 1, 12, "west", "minecraft:chests/pillager_outpost")   # pilot's survival kit under the cockpit
    s.add_sign(11, G + 1, 12, "minecraft:warped_sign[rotation=12]", ["UNITE K-7", "genou HS", "pilote ejecte", "sud"])
    s.set(11, G, 12, SHIP["scorch"])
    s.set(10, G + 1, 19, st.campfire(soul=True))

    sh.snow_cover(s, y_min=G + 9, prob=0.3, seed=4, layers=(1, 2),
                  skip=["glass", "rod", "campfire", "lamp", "chain", "purpur", "trapdoor", "deepslate", "basalt", "iron", "red_"])
    sh.snow_cover(s, y_min=G + 1, prob=0.1, seed=5, layers=(1, 2),
                  skip=["glass", "rod", "campfire", "lamp", "chain", "purpur", "trapdoor", "deepslate", "basalt", "iron",
                        "tuff", "powder", "blackstone", "coal"])
    return s.cropped(pad=1)


def build():
    return {"alien_skeleton": build_skeleton(), "mech_wreck": build_mech()}

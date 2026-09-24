"""Relics: two 'special' set pieces for the snow world.

alien_skeleton  - a giant frozen alien creature, half-buried: curved spine, nine barrel-arched ribs (plus one lying
                  loose), a horned skull with dark eye sockets, pelvis, one fore-limb raised out of the snow with
                  claws open to the sky, tall blue crystal spikes grown through the bones, a snow drift filling
                  half the ribcage and a small scientists' camp (A-frame tent, survey grid, lantern posts, journal).
mech_wreck      - a downed bipedal walker (~16 tall standing) kneeling in the snow: one leg buckled and lying flat,
                  the other crouched, torso tilted, a lofted cockpit with cracked glass, one arm cannon dug into a
                  crater, the other arm reaching up, hanging cables, sparks, blue smoke, scorched snow.
"""
import math
import random

import numpy as np

from tools.schem import Schematic, AIR
from tools import shapes as sh, states as st
from tools.palette import GROUND, SHIP, CAMP, CRYSTAL, MIX_SCORCH, MIX_SNOW

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


def path(pts):
    """Dense integer positions along a float polyline (8-connected, no duplicates)."""
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(int(math.ceil(2 * max(abs(b[k] - a[k]) for k in range(3)))), 1)
        for i in range(n + 1):
            t = i / n
            p = tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))
            if not out or out[-1] != p:
                out.append(p)
    return out


def bone_line(s, p1, p2, r=1.0):
    """A solid bone (3 thick when r=1) with the pillar axis following the segment."""
    ax = axis_of(p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    sh.line(s, p1, p2, bone(ax), radius=r)


def clip_below(s, y_keep, replace):
    """Everything strictly under y_keep becomes `replace` (bones sinking into the ground)."""
    sub = s.data[:, :y_keep, :]
    sub[sub != 0] = s.pid(replace)


def crystal_spike(s, base, tip, r0, seed=1):
    """A tall tilted crystal spike: light-blue glass skin at the base fading to blue ice, dripstone point,
    amethyst clusters growing out of its flanks and a sea lantern buried under the base for a glow."""
    rng = random.Random(seed)
    n = max(int(2 * max(abs(tip[k] - base[k]) for k in range(3))), 2)
    for i in range(n + 1):
        t = i / n
        x, y, z = (base[k] + (tip[k] - base[k]) * t for k in range(3))
        r = r0 * (1 - t) ** 0.75
        if r < 0.3:
            break
        blk = GROUND["ice_glass"] if t < 0.28 else (GROUND["ice"] if t < 0.5 and rng.random() < 0.3 else GROUND["ice_light"])
        sh.sphere(s, x, y, z, r, blk)
    x, y, z = (round(tip[k]) for k in range(3))
    if s.is_air(x, y, z):
        s.set(x, y, z, st.pointed_dripstone("up", "tip"))
    s.set(round(base[0]), round(base[1]) - 1, round(base[2]), CRYSTAL["glow_cold"])
    # clusters on the flanks
    for t in (0.22, 0.4, 0.58):
        x, y, z = (round(base[k] + (tip[k] - base[k]) * t) for k in range(3))
        for (dx, dz, facing) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            if rng.random() < 0.5:
                continue
            for d in range(1, 4):
                px, pz = x + dx * d, z + dz * d
                if s.is_air(px, y, pz):
                    if "ice" in s.get(px - dx, y, pz - dz) or "glass" in s.get(px - dx, y, pz - dz):
                        s.set(px, y, pz, CRYSTAL["cluster"] + f"[facing={facing}]")
                    break


# =================================================================================================== SKELETON
def build_skeleton():
    W, H, L, G = 60, 24, 30, 3
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

    rib_xs = list(range(18, 51, 4))                          # 9 ribs, 4 apart (2 wide -> 2-block gaps)

    # ---------------------------------------------------------------- rib cage: barrel arcs
    icicles = []
    dark_pts = []

    def rib_points(x0, side, ys, zs, ry, rz, phi_max, sweep):
        pts = []
        n = 90
        for k in range(n + 1):
            u = k / n
            phi = math.radians(phi_max) * u
            pts.append((x0 + sweep * u, ys - 1 - ry * (1 - math.cos(phi)), zs + side * (1 + rz * math.sin(phi)), phi, u))
        return pts

    def draw_rib(s, pts, side, break_at=None):
        seen = set()
        for (x, y, z, phi, u) in pts:
            if break_at is not None and phi > break_at:
                break
            xi, yi, zi = round(x), round(y), round(z)
            if (xi, yi, zi) in seen:
                continue
            seen.add((xi, yi, zi))
            wx = 2 if u < 0.8 else 1
            fat = u < 0.6
            ax = axis_of(0.2, -math.sin(phi), math.cos(phi))
            # inner (cage-side) neighbour: below near the top of the arch, towards the spine near the ground
            inner = (0, -1, 0) if abs(math.cos(phi)) >= abs(math.sin(phi)) else (0, 0, -side)
            for w in range(wx):
                s.set(xi + w, yi, zi, bone(ax))
                if fat:                                        # 2-thick ribbon: bone outside, dark structure inside
                    s.set(xi + w, yi + inner[1], zi + inner[2], bone(ax))
                    dark_pts.append((xi + w, yi + inner[1], zi + inner[2]))
            if side == -1 and fat and 0.35 < u < 0.42 and xi % 2 == 0:
                icicles.append((xi, yi - 2, zi))

    for i, x in enumerate(rib_xs):
        ys, zs = spine(x)
        sz = 1 - 0.5 * ((x - 34) / 16.0) ** 2
        rz = 1.0 + 7.5 * sz
        ry = ys - 1 - G
        for side in (-1, 1):
            if side == -1 and i == 4:                          # missing rib (lies loose on the snow, see below)
                continue
            broken = None
            if side == -1 and i in (2, 6):                     # two broken ribs on the exposed (north) side
                broken = math.radians(55 if i == 2 else 78)
            pts = rib_points(x, side, ys, zs, ry, rz, 102, 2.0)
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
        if x in rib_xs or x == 54:                             # neural spines on the rib vertebrae
            hgt = 2 if 26 <= x <= 46 else 1
            for k in range(1, hgt + 1):
                s.set(x, yi + k, zi, bone("y"))
            s.set(x, yi + hgt + 1, zi, st.pointed_dripstone("up", "tip"))
        prev = (y, z)
    for (x, y, z) in dark_pts:                                 # dark structure line on the inner face of each rib
        if "bone" in s.get(x, y, z):
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

    # ---------------------------------------------------------------- raised fore-limb (north side, outside the cage)
    sy, sz_ = spine(27)
    shoulder = (27, round(sy) - 2, 12)
    elbow = (24, G + 9, 5)
    wrist = (21, G + 15, 5)
    bone_line(s, (27, round(sy), round(sz_) - 1), shoulder, r=1.0)          # scapula joins the column
    bone_line(s, shoulder, elbow, r=1.0)                                    # humerus (3 thick)
    bone_line(s, elbow, wrist, r=1.0)                                       # forearm
    sh.sphere(s, *shoulder, 2.0, BONE)
    sh.sphere(s, *elbow, 2.0, BONE)
    sh.sphere(s, *wrist, 1.6, BONE)
    for (ex, ey, ez) in ((17, G + 17, 3), (20, G + 19, 8), (24, G + 18, 3)):   # claws start inside the wrist ball
        bone_line(s, wrist, (ex, ey, ez), r=0.55)
        if s.inside(ex, ey + 1, ez):
            s.set(ex, ey + 1, ez, st.pointed_dripstone("up", "tip"))
    sh.sphere(s, elbow[0], elbow[1] - 1, elbow[2], 1.0, BONE_DARK)          # dark shadow under the elbow
    # the other fore-limb: buried, only the shoulder blade shows on the south side
    sy2, sz2 = spine(27)
    bone_line(s, (27, round(sy2) - 1, round(sz2) + 2), (29, G + 1, round(sz2) + 8), r=1.0)

    # ---------------------------------------------------------------- bones sink into the ground
    clip_below(s, G + 1, SNOW)
    s.data[:, :G + 1, :][s.data[:, :G + 1, :] == 0] = s.pid(SNOW)

    # ---------------------------------------------------------------- crystals grown through the bones
    crystal_spike(s, (39, G + 1, 20), (41, G + 12, 23), 2.0, seed=1)        # grows through rib 38 (south)
    crystal_spike(s, (31, G + 1, 9), (28, G + 11, 6), 1.8, seed=2)          # through rib 30 (north)
    crystal_spike(s, (47, G + 1, 21), (48, G + 9, 24), 1.4, seed=3)
    crystal_spike(s, (22, G + 1, 24), (20, G + 8, 25), 1.2, seed=4)
    crystal_spike(s, (55, G + 1, 25), (58, G + 8, 27), 1.3, seed=5)
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

    # ---------------------------------------------------------------- snow drift filling the south half of the cage
    for x in range(16, 60):
        for z in range(ZC - 3, L):
            sy_, szx = spine(x)
            sz = max(0.0, 1 - 0.55 * ((x - 35) / 17.0) ** 2)
            d = (z - szx) / 9.0
            if d < -0.3:
                continue
            base_h = 0.5 * (sy_ - G - 1.0) * sz
            h = base_h * max(0.0, 1 - max(0.0, d) ** 1.6) * (0.75 + 0.5 * sh.value_noise2(x, z, 21, 7.0))
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
    tx1, tx2, tz = 9, 14, 24                                               # A-frame tent, ridge along x
    for x in range(3, 20):                                                 # trodden pad (irregular)
        for z in range(18, 29):
            if math.hypot((x - 11) / 8.0, (z - 24) / 5.0) < 0.75 + 0.5 * sh.value_noise2(x, z, 9, 3.0):
                s.set(x, G, z, CAMP["trodden_snow"])
    for x in range(tx1, tx2 + 1):
        for dz in range(-4, 5):
            for dy in range(0, 4):
                lvl = abs(dz) + dy
                z, y = tz + dz, G + 1 + dy
                if lvl == 3:                                               # sloped canvas, one block thick
                    s.set(x, y, z, CAMP["tent_accent"] if dz == 0 else CAMP["tent"])
                elif lvl < 3:
                    gable = x in (tx1, tx2)
                    if gable and not (x == tx1 and dz in (-1, 0) and dy < 2):
                        s.set(x, y, z, CAMP["tent_accent"] if lvl == 2 else CAMP["tent"])
                    else:
                        s.set(x, y, z, AIR)
    for x in range(tx1, tx2 + 1):
        s.set(x, G + 5, tz, st.slab("quartz"))                             # ridge cap
    # guy ropes at both gables + banners
    for (gx, dx) in ((tx1, -1), (tx2, 1)):
        s.set(gx + dx, G + 4, tz, st.chain("x"))
        s.set(gx + 2 * dx, G + 4, tz, st.chain("x"))
        for y in range(G + 1, G + 5):
            s.set(gx + 3 * dx, y, tz, CAMP["pole"])
    s.set(tx1 - 1, G + 2, tz + 2, st.wall_banner("cyan", "west"))
    s.set(tx2 + 1, G + 2, tz - 2, st.wall_banner("white", "east"))
    # interior: bed, lantern, table with candle, barrel, loot chest
    s.set(12, G + 1, tz - 1, st.bed(CAMP["bed"], "east", "head"))
    s.set(11, G + 1, tz - 1, st.bed(CAMP["bed"], "east", "foot"))
    s.set(11, G + 3, tz, st.lantern(hanging=True))
    s.set(12, G + 1, tz + 1, CAMP["table"])
    s.set(12, G + 2, tz + 1, st.candle("cyan", 2))
    s.set(13, G + 1, tz + 1, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(13, G + 1, tz - 1, "west", "minecraft:chests/igloo_chest")
    # outside: campfire ring, lantern posts, journal on a lectern, crates + radio
    s.set(5, G + 1, tz, st.campfire())
    for (x, z) in ((4, tz - 1), (6, tz - 1), (4, tz + 1), (6, tz + 1)):
        s.set(x, G + 1, z, st.slab("polished_deepslate"))
    for (x, z) in ((6, 20), (17, 27)):
        s.set(x, G + 1, z, CAMP["pole"]); s.set(x, G + 2, z, CAMP["pole"]); s.set(x, G + 3, z, st.lantern())
    s.set(16, G + 1, 24, st.facing_block("minecraft:lectern", "east"))
    s.add_sign(17, G + 1, 24, "minecraft:warped_sign[rotation=4]", ["JOURNAL 12", "os de 40m", "pas terrestre", "cristaux vivants"])
    s.set(16, G + 1, 21, "minecraft:barrel[facing=up,open=false]")
    s.set(17, G + 1, 21, "minecraft:barrel[facing=east,open=false]")
    s.set(16, G + 2, 21, CAMP["radio"] + "[facing=west]")
    s.set(17, G + 2, 21, CAMP["antenna"] + "[facing=up]")
    s.set(14, G + 1, 27, SHIP["container"])                               # sample box
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
    sh.snow_cover(s, y_min=G + 1, prob=0.16, seed=3, layers=(1, 2),
                  skip=["wool", "quartz", "glass", "ice", "amethyst", "bed", "lectern", "barrel", "concrete_powder",
                        "deepslate", "campfire", "planks", "table"])
    sh.texturize(s, SNOW, MIX_SNOW, seed=4, region=(0, G + 1, 0, W - 1, H - 1, L - 1))
    return s.cropped(pad=1)


# =================================================================================================== MECH WRECK
ARM = "minecraft:white_concrete"
ARM2 = "minecraft:light_gray_concrete"
DARK = "minecraft:polished_deepslate"
DARK2 = "minecraft:deepslate_tiles"
JOINT = "minecraft:polished_basalt"
ACC = "minecraft:purple_concrete"
IRON = "minecraft:iron_block"
MIX_ARMOUR = [(ARM, 8), ("minecraft:quartz_block", 2)]


def limb(s, p1, p2, r, plate=ARM, under=DARK, rings=True):
    """Armoured limb segment: white armour tube with a dark underside strip and dark joint rings."""
    sh.line(s, p1, p2, plate, radius=r)
    n = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), abs(p2[2] - p1[2]), 1)
    ri = int(round(r))
    for i in range(n + 1):
        t = i / n
        x, y, z = (round(p1[k] + (p2[k] - p1[k]) * t) for k in range(3))
        for dz in range(-ri, ri + 1):                          # dark underside
            for dy in (-ri, -ri + 1):
                if s.get(x, y + dy, z + dz) == plate and s.is_air(x, y + dy - 1, z + dz):
                    s.set(x, y + dy, z + dz, under)
        if rings and n >= 6 and (i == n // 3 or i == 2 * n // 3):
            sh.sphere(s, x, y, z, r + 0.3, under)
            sh.sphere(s, x, y, z, r - 0.7, JOINT)


def foot_rot(s, cx, cz, hx, hz, ang, y1, y2, block, shrink=0.0):
    """A rectangle (half sizes hx, hz) rotated by ang around (cx, cz), extruded y1..y2."""
    c, sn = math.cos(ang), math.sin(ang)
    pts = []
    for (ux, uz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px, pz = ux * (hx - shrink), uz * (hz - shrink)
        pts.append((cx + px * c - pz * sn, cz + px * sn + pz * c))
    sh.polygon_prism(s, pts, y1, y2, block)


def build_mech():
    W, H, L, G = 30, 26, 30, 3
    s = Schematic(W, H, L, ground=G)
    ZC = 15
    sh.ground_slab(s, G, SNOW, depth=4)
    # scorched, trampled snow under the wreck (ragged edge) + crater where the cannon dug in
    sh.ground_disc(s, 15, ZC, 8.5, G, SHIP["scorch"], rim_block=None, seed=8, noise=0.45, depth=1)
    for x in range(W):
        for z in range(L):
            d = math.hypot(x - 15, z - ZC)
            if 6.5 < d < 10.5 and s.get(x, G, z) == SHIP["scorch"] and sh.value_noise2(x, z, 13, 3.0) < 0.42:
                s.set(x, G, z, SNOW)
    sh.crater(s, 4, 5, 3.5, G, SHIP["scorch"], SNOW, SNOW, depth=2, rim_height=1, seed=2)
    sh.texturize(s, SHIP["scorch"], MIX_SCORCH, seed=6)

    HIP_Y = G + 7
    # ---------------------------------------------------------------- pelvis + hip spheres
    sh.box(s, 15, HIP_Y - 2, 12, 19, HIP_Y + 1, 18, DARK)
    sh.box(s, 16, HIP_Y - 2, 13, 18, HIP_Y + 1, 17, DARK2)
    sh.box(s, 15, HIP_Y + 1, 13, 19, HIP_Y + 1, 17, ARM2)                    # waist plate
    for z in (10, 20):
        sh.sphere(s, 17, HIP_Y, z, 1.7, DARK)
        sh.sphere(s, 17, HIP_Y, z, 0.8, JOINT)

    # ---------------------------------------------------------------- LEFT leg (south): crouched, foot planted forward
    hip_l = (17, HIP_Y, 20); knee_l = (9, HIP_Y - 1, 21); ankle_l = (8, G + 3, 21)
    limb(s, hip_l, knee_l, 2.0)                                              # thigh: forward and slightly down
    limb(s, knee_l, ankle_l, 1.7, rings=False)                               # shin: down to the foot
    sh.sphere(s, *knee_l, 2.2, DARK)                                         # knee ball
    sh.sphere(s, *knee_l, 1.1, JOINT)
    sh.box(s, knee_l[0] - 3, knee_l[1] - 1, knee_l[2] - 1, knee_l[0] - 3, knee_l[1] + 1, knee_l[2] + 1, "minecraft:quartz_block")   # knee cap
    s.set(knee_l[0] - 3, knee_l[1], knee_l[2], ACC)
    # big foot: dark sole, white plate, toe bevels, dark seam, purple toe band
    sh.box(s, 3, G + 1, 18, 11, G + 1, 24, DARK2)
    sh.box(s, 4, G + 2, 18, 11, G + 2, 24, ARM)
    sh.box(s, 7, G + 3, 19, 11, G + 3, 23, ARM)
    sh.box(s, 6, G + 2, 18, 6, G + 2, 24, DARK)                              # seam between toe and foot plate
    sh.box(s, 4, G + 2, 21, 5, G + 2, 21, ACC)                               # purple toe stripe
    for z in range(18, 25):
        s.set(2, G + 1, z, st.stairs("deepslate_tile", "east"))
        s.set(3, G + 2, z, st.stairs("quartz", "east"))
    for z in (18, 24):
        for x in range(7, 12):
            s.set(x, G + 3, z, st.stairs("quartz", "south" if z == 18 else "north"))
    sh.sphere(s, 8, G + 4, 21, 1.9, DARK)                                    # ankle ring
    sh.sphere(s, 8, G + 4, 21, 0.9, JOINT)

    # ---------------------------------------------------------------- RIGHT leg (north): buckled, knee on the ground, shin flat
    hip_r = (17, HIP_Y, 10); knee_r = (14, G + 2, 7); ankle_r = (22, G + 2, 5)
    limb(s, hip_r, knee_r, 2.0)                                              # thigh down to the ground
    limb(s, knee_r, ankle_r, 2.0)                                            # shin lying flat on the scorch disc
    sh.sphere(s, *knee_r, 2.0, DARK)                                         # knee ball
    sh.sphere(s, *knee_r, 1.2, JOINT)
    # foot turned 45 deg away, half on the snow
    ang = math.radians(35)
    foot_rot(s, 24.5, 4.5, 4.0, 3.0, ang, G + 1, G + 1, DARK2)
    foot_rot(s, 24.5, 4.5, 4.0, 3.0, ang, G + 2, G + 2, ARM, shrink=0.6)
    foot_rot(s, 24.5, 4.5, 4.0, 3.0, ang, G + 3, G + 3, ARM, shrink=1.6)
    sh.line(s, (27, G + 2, 2), (28, G + 2, 6), ACC, radius=0.0)               # purple toe band on the far edge
    sh.sphere(s, 22, G + 3, 5, 1.6, DARK)                                    # ankle
    sh.sphere(s, 22, G + 3, 5, 0.7, JOINT)

    # ---------------------------------------------------------------- torso (tilted forward = shifted per layer)
    TY0 = HIP_Y + 2                                                          # G+9
    NL = 7
    halves = [4, 4, 5, 5, 6, 6, 6]
    torso_boxes = []
    for dy in range(NL):
        y = TY0 + dy
        shift = round(dy * 0.5)
        x1, x2 = 14 - shift, 19 - shift
        half = halves[dy]
        z1, z2 = ZC - half, ZC + half
        sh.box(s, x1, y, z1, x2, y, z2, ARM)
        sh.box(s, x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, DARK2)                 # dark inner frame
        torso_boxes.append((x1, y, z1, x2, z2))
        if dy == 3:                                                          # dark seam ring (belt) at panel line
            sh.box(s, x1, y, z1, x2, y, z2, DARK)
            sh.box(s, x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, DARK2)
        if dy == 0:                                                          # dark underside of the chest
            sh.box(s, x1, y, z1, x2, y, z2, DARK)
        # front bevel (stairs) on the two front corners
        s.set(x1 - 1, y, z1, st.stairs("quartz", "east", "top" if dy % 2 else "bottom"))
        s.set(x1 - 1, y, z2, st.stairs("quartz", "east", "top" if dy % 2 else "bottom"))
    # front chest plate: white with a dark-framed purple centre panel
    for dy in range(1, NL):
        y = TY0 + dy
        shift = round(dy * 0.5)
        x1 = 14 - shift
        half = halves[dy]
        for z in range(ZC - half + 1, ZC + half):
            s.set(x1 - 1, y, z, ARM if dy != 3 else DARK)
    for dy in (1, 2):
        y = TY0 + dy
        x1 = 14 - round(dy * 0.5)
        for z in range(ZC - 2, ZC + 3):
            s.set(x1 - 1, y, z, DARK if abs(z - ZC) == 2 else ACC)
    y = TY0 + 3; x1 = 14 - round(3 * 0.5)
    for z in range(ZC - 2, ZC + 3):
        s.set(x1 - 1, y, z, DARK)
    # side purple panels with a dark inset frame
    for side in (-1, 1):
        for dy in (4, 5):
            y = TY0 + dy
            shift = round(dy * 0.5)
            z = ZC + side * halves[dy]
            for x in range(15 - shift, 19 - shift):
                s.set(x, y, z, ACC if 16 - shift <= x <= 17 - shift else DARK)
        y = TY0 + 6
        shift = 3
        for x in range(15 - shift, 19 - shift):
            s.set(x, y, ZC + side * halves[6], DARK)
    # north breach: one irregular hole in the wall (z = ZC-4) showing the redstone core just behind it
    sh.box(s, 14, TY0 + 1, ZC - 3, 18, TY0 + 2, ZC - 2, st.redstone_lamp(True))
    sh.box(s, 14, TY0 + 2, ZC - 4, 18, TY0 + 2, ZC - 4, st.redstone_lamp(True))     # wall is one block further out on this row
    for x in range(13, 19):
        for y in range(TY0 + 1, TY0 + 3):
            z = ZC - halves[y - TY0]
            n = sh.value_noise2(x * 1.3, y * 1.7, 5, 2.5)
            if 14 <= x <= 17 or n > 0.55:
                s.set(x, y, z, AIR)
    s.set(15, TY0 + 1, ZC - 4, st.end_rod("north"))                          # sparks out of the hole
    s.set(17, TY0 + 2, ZC - 5, st.end_rod("north"))
    s.set(13, TY0 + 1, ZC - 5, st.chain("y")); s.set(13, TY0, ZC - 5, st.chain("y"))
    # side vents
    for dy in (1, 2):
        y = TY0 + dy
        shift = round(dy * 0.5)
        s.set(17 - shift, y, ZC + halves[dy] + 1, st.trapdoor("iron", "south", "bottom", open=True))
    # top plate with a dark seam, flush (no bar)
    yt = TY0 + NL                                                            # G+16
    xs1 = 14 - 3
    sh.box(s, xs1, yt, ZC - 6, xs1 + 5, yt, ZC + 6, ARM)
    sh.box(s, xs1, yt, ZC, xs1 + 5, yt, ZC, DARK)
    for z in range(ZC - 6, ZC + 7):
        s.set(xs1 + 6, yt, z, st.stairs("deepslate_tile", "west", "top"))    # back overhang bevel
    for x in range(xs1, xs1 + 6):
        s.set(x, yt, ZC - 7, st.stairs("quartz", "south"))
        s.set(x, yt, ZC + 7, st.stairs("quartz", "north"))
    # collar behind the cockpit + antenna mast at the back
    sh.box(s, xs1 + 3, yt + 1, ZC - 3, xs1 + 4, yt + 1, ZC + 3, DARK2)
    sh.box(s, xs1 + 4, yt + 2, ZC - 2, xs1 + 4, yt + 2, ZC + 2, DARK)
    mast = (xs1 + 5, yt + 1, ZC)
    sh.box(s, mast[0], mast[1], mast[2], mast[0], mast[1] + 2, mast[2], DARK)
    s.set(mast[0], mast[1] + 3, mast[2], st.lightning_rod("up"))
    s.set(mast[0], mast[1] + 4, mast[2], st.lightning_rod("up"))
    s.set(mast[0], mast[1] + 2, mast[2] - 1, st.end_rod("north"))
    s.set(mast[0], mast[1] + 2, mast[2] + 1, st.end_rod("south"))
    s.set(mast[0] - 1, mast[1] + 1, mast[2], st.end_rod("west"))

    # ---------------------------------------------------------------- cockpit pod (lofted along x, cracked glass)
    cx0 = xs1 - 3
    yc = yt - 1
    pod_secs = [(cx0, yc, ZC, 0.9, 1.3), (cx0 + 2, yc, ZC, 1.8, 2.1), (cx0 + 5, yc, ZC, 1.8, 2.1), (cx0 + 6, yc, ZC, 1.4, 1.8)]
    pod = sh.loft(s, pod_secs, DARK, axis="x")
    inner = sh.loft_mask(s, pod_secs, "x", shrink=1.0)
    sh.fill_mask(s, inner, AIR)
    shell = pod & ~inner
    rng = np.random.default_rng(3)
    xs_ = np.arange(s.w)[:, None, None]; ys_ = np.arange(s.h)[None, :, None]
    glass_zone = shell & (xs_ <= cx0 + 4) & (ys_ >= yc - 1)
    idx = np.argwhere(glass_zone)
    for (x, y, z) in idx:
        r = rng.random()
        if r < 0.6:
            s.set(x, y, z, SHIP["glass"])
        elif r < 0.85:
            s.set(x, y, z, st.glass_pane("light_blue"))
        else:
            s.set(x, y, z, AIR)
    s.set(cx0 + 4, yc - 1, ZC, SHIP["light"])                                 # cockpit light
    s.set(cx0 + 3, yc - 1, ZC, st.stairs("polished_deepslate", "west"))       # pilot seat on the pod floor
    s.set(cx0 + 5, yc - 1, ZC, "minecraft:daylight_detector")                 # console (behind the seat)
    sh.box(s, cx0 + 1, yc - 2, ZC - 1, cx0 + 4, yc - 2, ZC + 1, ARM2)          # pod cradle (chin) under the front
    sh.box(s, cx0 + 1, yc - 2, ZC, cx0 + 4, yc - 2, ZC, DARK)

    # ---------------------------------------------------------------- shoulders (pauldrons)
    for side in (-1, 1):
        z = ZC + side * 8
        sh.ellipsoid(s, xs1 + 2, yt - 2, z, 2.6, 2.0, 2.2, ARM)
        sh.ellipsoid(s, xs1 + 2, yt - 3, z, 2.6, 1.0, 2.2, DARK)               # dark underside
        for x in range(xs1, xs1 + 5):                                        # purple stripe over the pauldron
            if s.get(x, yt - 1, z + side) == ARM:
                s.set(x, yt - 1, z + side, ACC)
        sh.sphere(s, xs1 + 2, yt - 3, z - side * 2, 1.4, JOINT)
    # back: radiator + exhaust stacks with blue smoke
    sh.box(s, 20, TY0 + 1, ZC - 4, 20, TY0 + 5, ZC + 4, DARK2)
    for z in range(ZC - 3, ZC + 4, 2):
        for y in (TY0 + 2, TY0 + 4):
            s.set(21, y, z, st.trapdoor("iron", "west", "bottom", open=True))
    for z in (ZC - 3, ZC + 3):
        sh.cylinder(s, 20, TY0 + 6, z, 1.0, 2, DARK2, axis="y")
        sh.cylinder(s, 20, TY0 + 9, z, 1.0, 0, IRON, axis="y")                  # iron lip
        s.set(20, TY0 + 9, z, DARK)
        s.set(20, TY0 + 10, z, st.campfire(soul=True))

    # ---------------------------------------------------------------- RIGHT arm (north): cannon buried in the crater
    sh_r = (xs1 + 2, yt - 3, ZC - 9); el_r = (8, yt - 6, ZC - 10)
    limb(s, sh_r, el_r, 1.8)
    sh.sphere(s, *el_r, 2.2, DARK)
    sh.sphere(s, *el_r, 1.1, JOINT)
    sh.line(s, el_r, (4, G - 1, 5), DARK2, radius=1.5)
    for i in (3, 6):                                                         # iron barrel rings
        t = i / 9
        x, y, z = (round(el_r[k] + ((4, G - 1, 5)[k] - el_r[k]) * t) for k in range(3))
        sh.sphere(s, x, y, z, 2.0, IRON)
        sh.sphere(s, x, y, z, 1.3, DARK2)
    sh.box(s, 9, yt - 5, ZC - 12, 11, yt - 4, ZC - 11, ARM)                    # forearm plate

    # ---------------------------------------------------------------- LEFT arm (south): reaching up
    sh_l = (xs1 + 2, yt - 3, ZC + 9); el_l = (9, yt - 1, ZC + 11); wr_l = (7, yt + 4, ZC + 11)
    limb(s, sh_l, el_l, 1.8)
    sh.sphere(s, *el_l, 2.2, DARK)
    sh.sphere(s, *el_l, 1.1, JOINT)
    limb(s, el_l, wr_l, 1.6, rings=False)
    sh.sphere(s, *wr_l, 1.3, DARK)
    for (dx, dz) in ((-1, -1), (-1, 1), (1, 0)):                              # hand: 3 fingers + glow
        s.set(wr_l[0] + dx, wr_l[1] + 2, wr_l[2] + dz, DARK)
        s.set(wr_l[0] + dx, wr_l[1] + 3, wr_l[2] + dz, st.end_rod("up"))
    s.set(wr_l[0], wr_l[1] + 2, wr_l[2], SHIP["light"])
    s.set(wr_l[0], wr_l[1] + 1, wr_l[2], "minecraft:cyan_stained_glass")

    # ---------------------------------------------------------------- texture (large plates only) + structure lines
    for (x1, y, z1, x2, z2) in torso_boxes:
        sh.texturize(s, ARM, MIX_ARMOUR, seed=9 + y, region=(x1 - 1, y, z1, x2, y, z2))
    sh.texturize(s, ARM, MIX_ARMOUR, seed=21, region=(3, G + 1, 18, 11, G + 3, 24))
    sh.texturize(s, ARM, MIX_ARMOUR, seed=22, region=(19, G + 1, 0, 29, G + 3, 9))

    # ---------------------------------------------------------------- cables, sparks, debris, story
    for (x, z, top, bot) in ((13, ZC - 1, TY0 - 1, G + 1), (12, ZC + 3, TY0, G + 4), (19, ZC - 6, TY0 + 1, G + 1),
                             (xs1 + 1, ZC - 11, yt - 5, G + 1), (11, ZC + 8, yt - 4, G + 1)):
        for y in range(bot, top + 1):
            s.set_if_air(x, y, z, st.chain("y"))
    for x in range(12, 16):                                                  # loose cable on the snow
        s.set_if_air(x, G + 1, ZC - 10, st.chain("x"))
    plates = [st.slab("quartz"), st.slab("quartz", "top"), st.trapdoor("iron", "north", "bottom", open=True),
              st.trapdoor("iron", "east", "bottom", open=True), st.slab("polished_deepslate"), st.trapdoor("iron", "south", "top")]
    drng = random.Random(5)
    for _ in range(9):                                                       # armour plates in pairs, half-sunk
        x, z = drng.randint(1, W - 3), drng.randint(1, L - 3)
        if 8 < math.hypot(x - 15, z - ZC) and s.top_y(x, z) == G:
            p = drng.choice(plates)
            s.set(x, G + 1, z, p)
            s.set(x + drng.choice((0, 1)), G + 1, z + drng.choice((-1, 1)), drng.choice(plates))
            s.set(x - 1, G + 1, z, st.snow_layer(2))
    s.add_chest(9, G + 1, ZC - 3, "west", "minecraft:chests/pillager_outpost")   # pilot's survival kit
    s.add_sign(9, G + 1, ZC - 2, "minecraft:warped_sign[rotation=12]", ["UNITE K-7", "genou HS", "pilote ejecte", "sud"])
    s.set(9, G, ZC - 2, SHIP["scorch"])
    s.set(9, G + 1, ZC + 7, st.campfire(soul=True))

    sh.snow_cover(s, y_min=G + 2, prob=0.3, seed=4, layers=(1, 2),
                  skip=["glass", "rod", "campfire", "lamp", "chain", "slab", "purple", "trapdoor", "deepslate", "basalt", "iron"])
    return s.cropped(pad=1)


def build():
    return {"alien_skeleton": build_skeleton(), "mech_wreck": build_mech()}

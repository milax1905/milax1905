"""Communications structures: a deep-space dish station (comms_array) and a slender relay/beacon tower
(beacon_tower). Clean white/quartz surfaces on dark deepslate structure, lavender accents, red aviation lamps,
pearlescent lantern at the top of the mast. Both are pasted onto snow (ground=2): only footings / foundations /
anchors go below the surface, so `//paste -a` sits them in the terrain.

The dishes are real paraboloids: every voxel of a box is transformed into the tilted dish frame (u, v across the
face, n = dish axis) and kept when |w - r2 / (4f)| falls inside a thin band (front face white, back light-gray, a
dark rim ring, iron radial struts proud of the back)."""
import math

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, LAB, CAMP, GROUND, MIX_WHITE, MIX_LIGHT_GRAY, MIX_DARK

WHITE = "minecraft:white_concrete"
LGRAY = "minecraft:light_gray_concrete"
DARK = "minecraft:polished_deepslate"
DARK_ALT = "minecraft:deepslate_tiles"
IRON = "minecraft:iron_block"
BARS = "minecraft:iron_bars"
LAMP = st.redstone_lamp(True)
SEA = "minecraft:sea_lantern"
FROG = "minecraft:pearlescent_froglight"
PURPUR = "minecraft:purpur_block"
PURPLE_GLASS = "minecraft:purple_stained_glass"
GLASS = "minecraft:glass"
PANE = "minecraft:glass_pane"
TRODDEN = CAMP["trodden_snow"]
# placeholders for the dish shells: converted at the very end so the global texturize / snow_cover never touch them
DISH_FACE = "minecraft:white_wool"
DISH_BACK = "minecraft:light_gray_wool"
DISH_FACE_MIX = [(WHITE, 7), ("minecraft:quartz_block", 2), ("minecraft:smooth_quartz", 1)]
DISH_BACK_MIX = [(LGRAY, 7), ("minecraft:polished_andesite", 2), ("minecraft:smooth_stone", 1)]


# ----------------------------------------------------------------------------- geometry helpers
def dish_basis(tilt_deg: float, az_deg: float):
    """Orthonormal basis of a dish whose axis is tilted `tilt` degrees from vertical toward azimuth `az`
    (0 = north / -z, 90 = east / +x). Returns (u, v, n) as numpy vectors; n = dish axis (points to the sky)."""
    t, a = math.radians(tilt_deg), math.radians(az_deg)
    n = np.array([-math.sin(t) * math.sin(a), math.cos(t), -math.sin(t) * math.cos(a)])
    u = np.array([math.cos(a), 0.0, -math.sin(a)])
    v = np.cross(n, u)
    return u, v, n


def rp(p):
    return int(math.floor(p[0] + 0.5)), int(math.floor(p[1] + 0.5)), int(math.floor(p[2] + 0.5))


def line6(s, p1, p2, block, ends=None, end_len=0.0):
    """Face-connected (6-neighbour) solid line: every step moves along one axis only, so the line never breaks
    into corner-touching dots. `ends` block replaces `block` within `end_len` of either end (feet)."""
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    length = float(np.linalg.norm(p2 - p1))
    n = max(1, int(math.ceil(length * 3)))
    prev = None
    for i in range(n + 1):
        t = i / n
        c = list(rp(p1 + (p2 - p1) * t))
        d = t * length
        blk = ends if (ends and (d < end_len or length - d < end_len)) else block
        if prev is None:
            s.set(*c, blk)
        else:
            cur = prev[:]
            for ax in range(3):
                while cur[ax] != c[ax]:
                    cur[ax] += 1 if c[ax] > cur[ax] else -1
                    s.set(*cur, blk)
        prev = c


def paraboloid_dish(s, C, R, depth, tilt, az, front=DISH_FACE, back=DISH_BACK, rim=DARK, rim_w=1.0,
                    thick=2.4, front_w=1.4, struts=0, strut_block=IRON, strut_off=-2.6, hub=None, hub_r=1.4,
                    lamps=0, snow=False):
    """Voxel-sampled parabolic dish: bowl radius R, depth `depth` at the rim, vertex at C, axis n tilted `tilt`
    degrees toward azimuth `az`. Each voxel centre p is mapped to (a, b, w) in the dish frame; with
    e = w - k*r^2 (k = depth / R^2) the shell is -thick+0.5 < e <= 0.5. The outer `front_w` of that band is the
    reflecting face, the rest is the back shell; the outer `rim_w` of the radius is the dark rim ring.
    Optional radial struts on the back (proud of the shell), a hub sphere, rim lamps, snow in the low part.
    Returns (u, v, n, k)."""
    C = np.array(C, dtype=float)
    u, v, n = dish_basis(tilt, az)
    k = depth / (R * R)
    reach = int(math.ceil(R + depth + abs(strut_off) + 2))
    cx, cy, cz = rp(C)
    lows = []
    for x in range(max(0, cx - reach), min(s.w, cx + reach + 1)):
        for y in range(max(0, cy - reach), min(s.h, cy + reach + 1)):
            for z in range(max(0, cz - reach), min(s.l, cz + reach + 1)):
                d = np.array([x, y, z], dtype=float) - C
                a, b, w = float(d @ u), float(d @ v), float(d @ n)
                r2 = a * a + b * b
                if r2 > R * R:
                    continue
                e = w - k * r2
                if not (-thick + 0.5 < e <= 0.5):
                    continue
                r = math.sqrt(r2)
                on_face = e > 0.5 - front_w or back is None
                if rim and (r >= R - 0.45 or (on_face and r >= R - rim_w)):
                    blk = rim                                    # rim ring on the face, thin edge on the back
                elif on_face:
                    blk = front
                else:
                    blk = back
                s.set(x, y, z, blk)
                if snow and blk == front and b > 0.35 * R:          # +v points downhill (v = n x u)
                    lows.append((x, y, z, b))
    for i in range(struts):                                          # radial struts proud of the back shell
        ph = 2 * math.pi * (i + 0.5) / struts
        for r in np.arange(0.6, R - 0.3, 0.2):
            a, b = r * math.cos(ph), r * math.sin(ph)
            s.set(*rp(C + u * a + v * b + n * (k * r * r + strut_off)), strut_block)
    if hub:
        sh.sphere(s, *rp(C + n * (strut_off - 0.3)), hub_r, hub)
    for i in range(lamps):                                           # lamps set into the rim, flush with the face
        ph = 2 * math.pi * (i + 0.5) / lamps
        a, b = (R - 0.6) * math.cos(ph), (R - 0.6) * math.sin(ph)
        s.set(*rp(C + u * a + v * b + n * (k * (a * a + b * b))), LAMP)
    if snow and lows:
        bmax = max(l[3] for l in lows)
        for (x, y, z, b) in lows:
            if s.is_air(x, y + 1, z):
                t = (b - 0.35 * R) / max(1e-6, bmax - 0.35 * R)
                s.set(x, y + 1, z, st.snow_layer(max(1, min(4, int(round(1 + 3 * t))))))
    return u, v, n, k


def finish_dishes(s):
    """Convert the dish placeholders into their clean (close-shade) mixes."""
    sh.texturize(s, DISH_FACE, DISH_FACE_MIX, seed=41)
    sh.texturize(s, DISH_BACK, DISH_BACK_MIX, seed=42)


def chain_col(s, x, y1, y2, z):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        s.set(x, y, z, st.chain("y"))


def chain_run(s, p1, p2):
    """Straight horizontal / vertical chain run, axis following the run."""
    dx, dy, dz = abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), abs(p2[2] - p1[2])
    axis = "y" if dy >= max(dx, dz) else ("x" if dx >= dz else "z")
    sh.line(s, p1, p2, st.chain(axis))


def guy_line(s, top, anchor, bars=True):
    """Guy-line as a face-connected path (never a corner-only step) from `top` (must be face-adjacent to a
    structure block) down to a 2x2 polished-deepslate anchor sunk flush with the snow at (x, z), with a
    lightning-rod eye and snow layers around it. bars=True draws it in iron bars (they auto-connect into one
    continuous line); otherwise vertical chains + axis-oriented horizontal chain links."""
    x, y, z = top
    ax, az = anchor
    g = s.ground
    moves = []
    nx, nz = abs(ax - x), abs(az - z)
    sx, sz = (1 if ax > x else -1), (1 if az > z else -1)
    while nx or nz:                                   # interleave x and z moves, longer axis first
        if nx >= nz and nx:
            moves.append(("x", sx)); nx -= 1
        elif nz:
            moves.append(("z", sz)); nz -= 1
    y_bot = g + 2
    m = len(moves)
    cur_y = y
    for j, (axis, sgn) in enumerate(moves):
        yj = y - int(round((j + 1) * (y - y_bot) / (m + 1)))
        if bars:
            sh.box(s, x, yj, z, x, cur_y, z, BARS)
        else:
            chain_col(s, x, cur_y, yj + 1, z)         # vertical run down to just above the step
            s.set(x, yj, z, st.chain(axis))           # horizontal link toward the next column
        if axis == "x":
            x += sgn
        else:
            z += sgn
        cur_y = yj                                    # next column starts beside the link (face contact)
    if bars:
        sh.box(s, x, y_bot, z, x, cur_y, z, BARS)
    else:
        chain_col(s, x, cur_y, y_bot, z)
    s.set(x, g + 1, z, st.lightning_rod("up"))        # anchor eye
    x1, z1 = (x if sx > 0 else x - 1), (z if sz > 0 else z - 1)
    sh.box(s, x1, g - 1, z1, x1 + 1, g, z1 + 1, DARK)
    for (dx, dz) in ((-1, 0), (2, 0), (0, -1), (0, 2), (-1, 1), (2, 1), (1, -1), (1, 2)):
        s.set_if_air(x1 + dx, g + 1, z1 + dz, st.snow_layer(2))
    for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        if s.is_air(x1 + dx, g + 1, z1 + dz):
            s.set(x1 + dx, g + 1, z1 + dz, st.snow_layer(1))


def console(s, x, y, z, facing_wall: str):
    """Desk console: dark base, daylight-detector top, lit screen on the wall behind (facing_wall = wall side)."""
    s.set(x, y, z, DARK)
    s.set(x, y + 1, z, LAB["console"])
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing_wall]
    s.set(x + dx, y + 2, z + dz, LAMP)


def small_dish(s, px, py, pz, az, tilt, R=4, depth=1.1):
    """Small dish on a yoke: light-gray yoke block on the post shows the tilt; single white shell with a dark
    1-block rim, iron hub, feed rod on an iron strut to the focus."""
    s.set(px, py, pz, LGRAY)                                       # yoke
    _, _, n0 = dish_basis(tilt, az)
    Cs = np.array([px, py, pz], dtype=float) + n0 * 2.4
    line6(s, (px, py, pz), Cs, IRON)
    us, vs, ns, ks = paraboloid_dish(s, Cs, R, depth, tilt, az, back=None, rim=DARK, rim_w=0.8, thick=1.7,
                                     front_w=1.7, hub=IRON, hub_r=0.9, strut_off=-1.9)
    Fs = Cs + ns * (R * R / (4 * depth))
    line6(s, Cs, Fs, IRON)
    s.set(*rp(Fs), DARK)
    fx, fy, fz = rp(Fs)
    s.set(fx, fy + 1, fz, st.end_rod("up"))                       # feed tip, face-adjacent to the focus block


def hut_shell(s, hx1, hz1, hx2, hz2, G):
    """White hut with dark corner pillars / base course, light-gray mid band, eave stairs, raised light-gray
    roof deck (full blocks, so it takes snow) with a smooth-stone slab lip, foundation 1 block under the snow."""
    sh.box(s, hx1, G - 1, hz1, hx2, G - 1, hz2, DARK_ALT)              # foundation
    sh.box(s, hx1, G, hz1, hx2, G, hz2, LGRAY)                         # floor at surface level
    sh.hollow_box(s, hx1, G + 1, hz1, hx2, G + 5, hz2, WHITE, floor=False, ceiling=True)
    for (x, z) in ((hx1, hz1), (hx2, hz1), (hx1, hz2), (hx2, hz2)):    # corner pillars
        sh.box(s, x, G + 1, z, x, G + 5, z, DARK)
    for x in range(hx1 + 1, hx2):                                       # base course + light-gray mid band
        for z in (hz1, hz2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    for z in range(hz1 + 1, hz2):
        for x in (hx1, hx2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    sh.box(s, hx1 + 1, G + 1, hz1 + 1, hx2 - 1, G + 4, hz2 - 1, "air")   # interior 4 high
    sh.box_edge_stairs(s, hx1, G + 5, hz1, hx2, hz2, "deepslate_tile", half="top")   # eaves
    sh.box(s, hx1, G + 6, hz1, hx2, G + 6, hz2, st.slab("smooth_stone"))            # roof lip on the wall line
    sh.box(s, hx1 + 1, G + 6, hz1 + 1, hx2 - 1, G + 6, hz2 - 1, LGRAY)               # raised deck


# ----------------------------------------------------------------------------- comms array
def build_comms_array():
    W, H, L, G = 43, 31, 43, 2
    s = Schematic(W, H, L, ground=G)
    cx, cz = 21, 24                                     # dish pedestal

    # --- fence cordon (posts sunk 1 block + 1-high bars) with a gate on the south side
    x1, z1, x2, z2 = 2, 2, 40, 40
    perim = []
    for x in range(x1, x2 + 1):
        perim += [(x, z1), (x, z2)]
    for z in range(z1 + 1, z2):
        perim += [(x1, z), (x2, z)]
    for (x, z) in perim:
        if z == z2 and 19 <= x <= 23:
            continue                                  # gate gap
        post = ((x - x1) % 6 == 0 and z in (z1, z2)) or ((z - z1) % 6 == 0 and x in (x1, x2))
        if post:
            sh.box(s, x, G, z, x, G + 2, z, DARK)
            if (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                s.set(x, G + 3, z, st.end_rod("up"))
        else:
            s.set(x, G + 1, z, BARS)
    for x in (18, 24):                                  # gate posts with red lamps
        sh.box(s, x, G, z2, x, G + 3, z2, DARK)
        s.set(x, G + 4, z2, LAMP)
        s.set(x, G + 2, z2, LGRAY)

    # --- pedestal foundation (2 blocks into the snow), concrete apron at surface level, ground lights
    sh.cylinder(s, cx, G - 2, cz, 5.5, 1, DARK_ALT, axis="y")
    sh.cylinder(s, cx, G, cz, 8.5, 0, LGRAY, axis="y")
    sh.ring(s, cx, G, cz, 8.5, WHITE, thickness=1.0)
    sh.cylinder(s, cx, G, cz, 5.5, 0, DARK_ALT, axis="y")
    for i in range(8):                                  # ground lights around the plinth
        ph = 2 * math.pi * i / 8
        s.set(round(cx + 6.5 * math.cos(ph)), G, round(cz + 6.5 * math.sin(ph)), SEA)

    # --- trodden paths: gate -> pedestal, pedestal -> hut, hut -> generator (surface cells only)
    def path(p1, p2):
        n = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), 1)
        for i in range(n + 1):
            x = round(p1[0] + (p2[0] - p1[0]) * i / n)
            z = round(p1[1] + (p2[1] - p1[1]) * i / n)
            for dx in (0, 1):
                s.set_if_air(x + dx, G, z, TRODDEN)
    path((20, 40), (20, 31)); path((20, 31), (33, 31)); path((33, 31), (33, 36)); path((20, 31), (8, 31))

    # --- plinth with a capped light strip, column with vents / rivets / lavender band, bearing, yoke
    sh.cylinder(s, cx, G + 1, cz, 4.0, 0, DARK, axis="y")
    sh.ring_stairs(s, cx, G + 1, cz, 4.9, "deepslate_tile", half="bottom")
    for (ox, oz, ix, iz) in ((4, 0, 3, 0), (-4, 0, -3, 0), (0, 4, 0, 3), (0, -4, 0, -3),
                             (3, 2, 2, 1), (-3, 2, -2, 1), (3, -2, 2, -1), (-3, -2, -2, -1)):
        s.set(cx + ix, G + 1, cz + iz, SEA)                                # light sunk behind purple glass
        s.set(cx + ox, G + 1, cz + oz, PURPLE_GLASS)
    sh.cylinder(s, cx, G + 2, cz, 2.6, 6, DARK, axis="y")            # column G+2..G+8
    sh.ring(s, cx, G + 5, cz, 3.2, PURPUR, thickness=1.0)              # lavender band
    for i in range(4):                                                 # iron pillars at 45 degrees
        ph = math.pi / 4 + i * math.pi / 2
        x, z = round(cx + 2.9 * math.cos(ph)), round(cz + 2.9 * math.sin(ph))
        sh.box(s, x, G + 2, z, x, G + 8, z, IRON)
    for (dx, dz, fac) in ((3, 0, "east"), (-3, 0, "west"), (0, 3, "south"), (0, -3, "north")):
        for y in (G + 3, G + 7):                                       # vent panels on the cardinal faces
            s.set(cx + dx, y, cz + dz, st.trapdoor("iron", fac, "bottom", open=True))
        s.set(cx + dx, G + 4, cz + dz, st.button("stone", "wall", fac))   # rivets
        s.set(cx + dx, G + 6, cz + dz, st.button("stone", "wall", fac))
    sh.cylinder(s, cx, G + 9, cz, 3.4, 0, DARK, axis="y")             # bearing plate
    sh.ring_stairs(s, cx, G + 9, cz, 4.2, "deepslate_tile", half="top")
    sh.box(s, cx - 3, G + 10, cz - 1, cx + 3, G + 10, cz + 1, DARK)   # yoke base
    for x in (cx - 3, cx + 3):                                         # yoke arms
        sh.box(s, x, G + 11, cz - 1, x, G + 12, cz + 1, DARK)
        s.set(x, G + 13, cz, IRON)
    sh.box(s, cx - 3, G + 13, cz, cx + 3, G + 13, cz, IRON)           # axle
    P = np.array([cx, G + 13, cz], dtype=float)
    tilt, az = 40, 0
    R, depth = 11, 3.6
    u0, v0, n0 = dish_basis(tilt, az)
    C = P + n0 * 3.6
    line6(s, P, C, IRON)                                               # pivot into the hub
    low_back = C + v0 * 5.0 + n0 * (-3.0)                              # actuator strut to the low back of the dish
    line6(s, (cx, G + 10, cz + 3), low_back, IRON)

    # --- control hut (x 30..38, z 31..37), door on the west side facing the pedestal
    hx1, hz1, hx2, hz2 = 30, 31, 38, 37
    hut_shell(s, hx1, hz1, hx2, hz2, G)
    for x in (32, 33, 35, 36):                                          # window strips north + south
        s.set(x, G + 3, hz1, PANE); s.set(x, G + 3, hz2, PANE)
    for z in (33, 34, 35):                                              # east window strip
        s.set(hx2, G + 3, z, PANE)
    s.set(hx1, G + 3, 36, PANE)                                         # west: small window south of the door
    for x in (32, 36):                                                  # lamps in the top course
        s.set(x, G + 5, hz1, LAMP); s.set(x, G + 5, hz2, LAMP)
    s.set(hx2, G + 5, 34, LAMP)
    for (x, z) in ((31, hz1 - 1), (37, hz1 - 1), (31, hz2 + 1), (37, hz2 + 1), (hx2 + 1, 34)):
        s.set(x, G + 4, z, st.end_rod("down"))                          # lights hanging under the eave
    # roof deck furniture: vent stack, AC unit, antenna, rod, edge lights
    sh.box(s, 37, G + 7, 36, 37, G + 9, 36, DARK)                       # vent stack
    s.set(37, G + 10, 36, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(37, G + 8, 35, st.trapdoor("iron", "north", "bottom", open=True))
    sh.box(s, 32, G + 7, 32, 33, G + 7, 33, LAB["machine"])             # roof AC unit
    s.set(32, G + 8, 32, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(33, G + 8, 33, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(36, G + 8, 32, st.lightning_rod("up"))
    s.set(31, G + 8, 36, st.end_rod("up"))
    s.set(35, G + 8, 36, st.end_rod("up"))
    # door (west wall) + buttons + porch light
    s.set(hx1, G + 1, 34, st.door("dark_oak", "east", "lower"))
    s.set(hx1, G + 2, 34, st.door("dark_oak", "east", "upper"))
    s.set(hx1 - 1, G + 2, 33, st.button("stone", "wall", "west"))
    s.set(hx1 + 1, G + 2, 33, st.button("stone", "wall", "east"))
    s.set(hx1 - 1, G + 3, 34, st.wall_torch("west", soul=True))
    s.set(hx1 - 1, G, 34, LGRAY); s.set(hx1 - 2, G, 34, LGRAY)          # door step
    # interior (air G+1..G+4, ceiling G+5)
    s.set(33, G + 5, 34, SEA); s.set(36, G + 5, 34, SEA)
    for x in range(hx1 + 1, hx2):                                       # console desk along the north wall
        if x in (31, 33, 35, 37):
            console(s, x, G + 1, hz1 + 1, "north")
        else:
            s.set(x, G + 1, hz1 + 1, DARK)
            s.set(x, G + 2, hz1 + 1, st.slab("polished_deepslate"))
    sh.box(s, hx2 - 1, G + 1, hz1 + 3, hx2 - 1, G + 3, hz1 + 3, LAB["machine"])       # server rack
    s.set(hx2 - 1, G + 1, hz1 + 4, LAB["machine_dark"])
    s.set(hx2 - 1, G + 2, hz1 + 4, st.facing_block("minecraft:observer", "west"))
    s.set(hx2 - 1, G + 3, hz1 + 4, LAMP)
    s.set(hx2 - 1, G + 4, hz1 + 3, st.trapdoor("iron", "west", "top", open=True))
    s.set(hx1 + 1, G + 1, hz2 - 1, st.facing_block("minecraft:lectern", "east"))
    s.add_chest(hx1 + 2, G + 1, hz2 - 1, "north", "minecraft:chests/igloo_chest")
    s.set(hx1 + 3, G + 1, hz2 - 1, st.facing_block("minecraft:barrel", "up"))
    s.set(hx2 - 2, G + 1, hz2 - 1, st.bed("cyan", "east", "head"))
    s.set(hx2 - 3, G + 1, hz2 - 1, st.bed("cyan", "east", "foot"))
    s.add_sign(hx1 + 1, G + 3, hz2 - 1, "minecraft:warped_wall_sign[facing=north]",
               ["STATION RELAIS 4", "liaison perdue", "jour 31", "batterie 12%"])
    s.add_sign(hx1 - 1, G + 3, 35, "minecraft:warped_wall_sign[facing=west]", ["CONTROLE", "acces", "personnel", "seul"])

    # --- cable trays: hut -> pedestal, generator -> hut (chains at ground level on deepslate sleepers)
    def tray(p1, p2):
        chain_run(s, (p1[0], G + 1, p1[1]), (p2[0], G + 1, p2[1]))
        n_ = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), 1)
        for i in range(0, n_ + 1, 3):
            x = round(p1[0] + (p2[0] - p1[0]) * i / n_); z = round(p1[1] + (p2[1] - p1[1]) * i / n_)
            s.set(x, G, z, DARK)
    tray((29, 33), (26, 33)); tray((26, 33), (26, 28)); tray((26, 28), (26, 25))
    tray((10, 33), (14, 33)); tray((14, 33), (14, 29)); tray((14, 29), (17, 29)); tray((17, 29), (17, 25))

    # --- generator unit + fuel tank (west side)
    gx, gz = 6, 32
    sh.box(s, gx - 1, G, gz - 1, gx + 3, G, gz + 4, DARK_ALT)          # pad
    sh.box(s, gx, G + 1, gz, gx + 2, G + 2, gz + 1, IRON)              # body
    s.set(gx, G + 1, gz - 1, st.facing_block("minecraft:blast_furnace", "north"))
    s.set(gx + 1, G + 1, gz - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(gx + 2, G + 1, gz - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(gx + 3, G + 1, gz, st.trapdoor("iron", "east", "bottom", open=True))
    s.set(gx + 3, G + 1, gz + 1, st.trapdoor("iron", "east", "bottom", open=True))
    s.set(gx - 1, G + 1, gz, st.facing_block("minecraft:observer", "west"))
    s.set(gx - 1, G + 1, gz + 1, st.facing_block("minecraft:observer", "west"))
    s.set(gx + 1, G + 3, gz + 1, DARK)
    s.set(gx + 1, G + 4, gz + 1, st.campfire(soul=False, facing="north"))
    s.set(gx + 2, G + 3, gz, st.button("stone", "floor", "north"))
    s.set(gx, G + 3, gz, LAMP)
    # fuel tank (horizontal cylinder) on saddles
    sh.box(s, gx - 1, G + 1, gz + 3, gx + 3, G + 1, gz + 3, DARK)
    sh.cylinder(s, gx - 1, G + 3, gz + 3, 1.4, 4, LGRAY, axis="x")
    s.set(gx - 2, G + 3, gz + 3, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(gx + 4, G + 3, gz + 3, st.trapdoor("iron", "east", "bottom", open=True))
    s.set(gx + 1, G + 5, gz + 3, st.lightning_rod("up"))
    chain_run(s, (gx + 3, G + 2, gz + 3), (gx + 3, G + 2, gz + 1))

    # --- two solar racks (daylight detectors on dark stands) south-west
    for rz in (37, 39):
        for x in range(4, 12):
            s.set(x, G + 1, rz, DARK if x % 3 == 0 else st.slab("polished_deepslate", "top"))
            s.set(x, G + 2, rz, LAB["console"])
    s.set(12, G + 1, 38, st.chain("x")); s.set(13, G + 1, 38, st.chain("x"))
    chain_run(s, (13, G + 1, 37), (13, G + 1, 35))

    # --- weather mast in the NE + a supply crate stack
    s.set(35, G, 30, DARK_ALT); s.set(35, G + 1, 30, DARK); sh.box(s, 35, G + 2, 30, 35, G + 7, 30, BARS)
    s.set(35, G + 8, 30, st.lightning_rod("up"))
    s.set(35, G + 6, 30, LAB["console"])
    sh.box(s, 8, G + 1, 12, 9, G + 1, 13, SHIP["crate"]); s.set(8, G + 2, 12, SHIP["crate"])
    s.add_chest(9, G + 2, 13, "south", "minecraft:chests/village/village_snowy_house")

    # --- story: crystal spike breaking through the NE fence, snow drift leeward (east) of the hut, a flag
    sx, sz = 38, 5
    sh.cylinder(s, sx, G - 1, sz, 2.2, 7, GROUND["ice_light"], axis="y", r2=0.3)
    sh.cylinder(s, sx + 1, G - 1, sz + 2, 1.3, 4, GROUND["ice_glass"], axis="y", r2=0.2)
    sh.cylinder(s, sx - 2, G - 1, sz + 1, 0.9, 3, GROUND["ice_glass"], axis="y", r2=0.2)
    s.set(sx, G + 7, sz, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(sx + 1, G + 4, sz + 2, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(sx - 2, G + 3, sz + 1, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(sx + 2, G + 1, sz - 1, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(sx - 1, G + 1, sz + 3, st.facing_block("minecraft:medium_amethyst_bud", "up"))
    for (x, z) in ((sx - 1, sz - 1), (sx + 1, sz), (sx, sz + 1), (sx + 2, sz + 1)):
        s.set(x, G, z, "minecraft:amethyst_block")
    for (x, y, z) in ((36, G + 1, 2), (37, G + 1, 2), (39, G + 1, 2), (40, G + 1, 2), (40, G + 1, 3), (40, G + 1, 4), (40, G + 1, 5), (40, G + 1, 6)):
        s.set(x, y, z, "air")                                            # fence torn by the crystal
    s.set(37, G + 1, 2, st.trapdoor("iron", "south", "top", open=True)) # bent panel
    for dz in range(hz1 - 1, hz2 + 2):                                   # drift piling against the hut east wall
        for i, x in enumerate(range(hx2 + 1, hx2 + 4)):
            lay = 8 - 3 * i - (1 if dz in (hz1 - 1, hz2 + 1) else 0)
            if not (s.is_air(x, G + 1, dz) or s.get(x, G + 1, dz) == BARS):
                continue                                             # never bury a fence post / pole
            if lay >= 8:
                s.set(x, G + 1, dz, GROUND["snow"]); s.set(x, G + 2, dz, st.snow_layer(2))
            elif lay > 0:
                s.set(x, G + 1, dz, st.snow_layer(lay))
    for x in (x1 + 1, x1 + 2):                                           # drift along the inside of the west fence
        for z in range(8, 26):
            s.set_if_air(x, G + 1, z, st.snow_layer(3 if x == x1 + 1 else 1))
    sh.box(s, 16, G, 38, 16, G + 5, 38, DARK)                            # flag pole by the gate
    s.set(16, G + 6, 38, st.banner("cyan", 4))
    s.set(16, G + 3, 38, st.wall_banner("light_blue", "south"))

    # --- textures + weathering on everything but the dishes (built afterwards, kept clean)
    sh.texturize(s, WHITE, MIX_WHITE, seed=21)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=22)
    sh.texturize(s, DARK, MIX_DARK, seed=23)
    sh.snow_cover(s, y_min=G + 1, prob=0.45, seed=5, skip=["quartz", "calcite", "white_concrete", "lamp", "iron", "glass",
                                                          "lantern", "observer", "purpur", "froglight", "wool"])

    # --- the big dish: white paraboloid face, light-gray back, dark rim, 6 iron struts proud of the back, hub
    u, v, n, k = paraboloid_dish(s, C, R, depth, tilt, az, rim=DARK, rim_w=1.0, thick=2.4, front_w=1.4,
                                 struts=6, strut_block=IRON, strut_off=-2.6, hub=DARK, hub_r=1.5, lamps=6,
                                 snow=True)
    line6(s, P, C + n * (-2.9), IRON)                                  # re-assert the pivot through the hub
    # feed horn on 3 struts at the focal point: 2x2x2 light-gray horn, lanterns + end rods aimed at the bowl
    f = R * R / (4 * depth)
    F = C + n * f
    Fi = rp(F)
    for ph in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3):
        a, b = (R - 0.6) * math.cos(ph), (R - 0.6) * math.sin(ph)
        pr = C + u * a + v * b + n * (k * (a * a + b * b) + 0.8)
        line6(s, pr, F, DARK, ends=IRON, end_len=1.6)
    sh.box(s, Fi[0] - 1, Fi[1] - 1, Fi[2], Fi[0], Fi[1], Fi[2] + 1, LGRAY)
    for dx in (-1, 0):
        s.set(Fi[0] + dx, Fi[1] - 1, Fi[2] + 1, SEA)                   # lower-south cells face the bowl
        s.set(Fi[0] + dx, Fi[1] - 2, Fi[2] + 1, st.end_rod("down"))
        s.set(Fi[0] + dx, Fi[1] + 1, Fi[2], LAMP if dx == 0 else st.end_rod("up"))
    s.set(Fi[0] - 2, Fi[1], Fi[2], st.trapdoor("iron", "west", "top", open=True))
    s.set(Fi[0] + 1, Fi[1], Fi[2], st.trapdoor("iron", "east", "top", open=True))

    # --- two small dishes on posts (north corners)
    for (px, pz, az_, tl) in ((7, 8, -25, 45), (35, 8, 20, 50)):
        sh.cylinder(s, px, G, pz, 2.2, 0, DARK_ALT, axis="y")
        sh.box(s, px, G - 1, pz, px, G + 6, pz, DARK)
        sh.ring_stairs(s, px, G + 1, pz, 1.4, "deepslate_tile", half="bottom")
        small_dish(s, px, G + 7, pz, az_, tl)
        chain_run(s, (px, G + 1, pz + 1), (px, G + 1, pz + 6))
    finish_dishes(s)
    return s.cropped(pad=1)


# ----------------------------------------------------------------------------- beacon tower
def build_beacon_tower():
    W, H, L, G = 25, 50, 25, 2
    s = Schematic(W, H, L, ground=G)
    cx, cz = 12, 12
    TOP = G + 40                                   # lantern base level
    SECTIONS = ((G + 1, G + 12, 3), (G + 13, G + 24, 2), (G + 25, G + 36, 1))   # (y_from, y_to, half-width)

    def hw_at(y):
        for (y1, y2, hw) in SECTIONS:
            if y1 <= y <= y2:
                return hw
        return 0

    # --- footings: 2x2 pads sunk under each leg, tile plate at the surface
    for sx in (-3, 3):
        for sz in (-3, 3):
            sh.box(s, cx + sx - 1, G, cz + sz - 1, cx + sx + 1, G, cz + sz + 1, DARK_ALT)
            sh.box(s, cx + sx, G - 2, cz + sz, cx + sx, G, cz + sz, DARK)
    sh.box(s, cx - 3, G, cz - 3, cx + 3, G, cz + 3, DARK)
    sh.box(s, cx - 2, G, cz - 2, cx + 2, G, cz + 2, LGRAY)

    # --- open lattice: iron corner legs, dark ring every 6, iron-bar "+" panel bracing, hollow core
    for (y1, y2, hw) in SECTIONS:
        for y in range(y1, y2 + 1):
            for sx in (-hw, hw):
                for sz in (-hw, hw):
                    s.set(cx + sx, y, cz + sz, IRON)
            yl = (y - G) % 6
            for i in range(-hw + 1, hw):
                cells = ((cx + i, cz - hw), (cx + i, cz + hw), (cx - hw, cz + i), (cx + hw, cz + i))
                for (x, z) in cells:
                    if yl == 0:
                        s.set(x, y, z, DARK)
                    elif i == 0 or yl == 3:
                        s.set(x, y, z, BARS)
    # ladders: on the inside of the NW leg of each section
    for (y1, y2, hw) in SECTIONS:
        for y in range(y1, y2 + 1):
            s.set(cx - hw, y, cz - hw + 1, st.facing_block("minecraft:ladder", "south"))

    # --- platforms at every step-in: light-gray deck, quartz stair lip, iron-bar railings, corner lights
    def platform(y, hw):
        sh.box(s, cx - hw, y, cz - hw, cx + hw, y, cz + hw, LGRAY)
        sh.box_edge_stairs(s, cx - hw + 1, y, cz - hw + 1, cx + hw - 1, cz + hw - 1, "quartz", half="top")
        for x in range(cx - hw, cx + hw + 1):
            for z in (cz - hw, cz + hw):
                s.set(x, y + 1, z, BARS)
        for z in range(cz - hw, cz + hw + 1):
            for x in (cx - hw, cx + hw):
                s.set(x, y + 1, z, BARS)
        for (x, z) in ((cx - hw, cz - hw), (cx + hw, cz - hw), (cx - hw, cz + hw), (cx + hw, cz + hw)):
            s.set(x, y, z, DARK)
            s.set(x, y - 1, z, st.stairs("deepslate_tile", "east" if x < cx else "west", "top"))   # corbel
            s.set(x, y + 1, z, IRON)
            s.set(x, y + 2, z, st.end_rod("up"))
        lh = hw_at(y)
        for sx in (-lh, lh):                                            # legs through the deck
            for sz in (-lh, lh):
                s.set(cx + sx, y, cz + sz, IRON)
        s.set(cx, y, cz, SEA)

    platform(G + 12, 4)
    platform(G + 24, 3)
    platform(G + 36, 2)
    s.set(cx - 3, G + 12, cz - 2, st.facing_block("minecraft:ladder", "south"))     # ladder holes
    s.set(cx - 2, G + 24, cz - 1, st.facing_block("minecraft:ladder", "south"))
    s.set(cx - 1, G + 36, cz, st.facing_block("minecraft:ladder", "south"))

    # --- platform 2 (G+24): antenna arms north and south at deck level, lightning rods
    for dz in (-1, 1):
        for i in range(4, 7):
            s.set(cx, G + 24, cz + dz * i, IRON)
        s.set(cx, G + 24, cz + dz * 7, DARK)
        s.set(cx, G + 25, cz + dz * 7, st.end_rod("up"))
        s.set(cx, G + 24, cz + dz * 8, st.end_rod("south" if dz > 0 else "north"))
    for dx in (-1, 1):
        s.set(cx + dx * 3, G + 26, cz, st.lightning_rod("up"))
    # --- platform 1 (G+12): east arm carrying the small dish (built last, clean), west weather sensors
    sh.box(s, cx + 5, G + 12, cz, cx + 6, G + 12, cz, IRON)
    s.set(cx - 5, G + 12, cz, IRON); s.set(cx - 6, G + 12, cz, DARK)
    s.set(cx - 6, G + 13, cz, LAB["console"]); s.set(cx - 6, G + 11, cz, st.lightning_rod("down"))

    # --- mast pole above platform 3, yagi arms, red aviation lamps on the outside of the legs
    sh.box(s, cx, G + 37, cz, cx, TOP - 1, cz, DARK)
    for dx in (-1, 1):
        s.set(cx + dx, G + 38, cz, st.end_rod("east" if dx > 0 else "west"))
        s.set(cx + dx, G + 39, cz, LAMP)
    for (y, hw) in ((G + 6, 3), (G + 18, 2), (G + 30, 1)):
        for sx in (-1, 1):
            for sz in (-1, 1):
                s.set(cx + sx * (hw + 1), y, cz + sz * hw, LAMP)

    # --- top lantern: dark base with quartz bevel, 3x3 glass column around a froglight core, slab cap, rods
    sh.box(s, cx - 1, TOP, cz - 1, cx + 1, TOP, cz + 1, DARK)
    sh.box_edge_stairs(s, cx - 1, TOP, cz - 1, cx + 1, cz + 1, "quartz", half="top")
    for y in range(TOP + 1, TOP + 4):
        sh.hollow_box(s, cx - 1, y, cz - 1, cx + 1, y, cz + 1, GLASS, floor=False, ceiling=False)
        for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):        # thin corner posts: the core shows diagonally
            s.set(cx + dx, y, cz + dz, BARS)
    s.set(cx, TOP + 1, cz, SEA); s.set(cx, TOP + 2, cz, FROG); s.set(cx, TOP + 3, cz, FROG)
    for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        s.set(cx + dx, TOP + 4, cz + dz, IRON)
        s.set(cx + dx, TOP + 5, cz + dz, st.end_rod("up"))
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set(cx + dx, TOP + 4, cz + dz, st.slab("smooth_quartz"))
    s.set(cx, TOP + 4, cz, DARK)
    s.set(cx, TOP + 5, cz, st.lightning_rod("up")); s.set(cx, TOP + 6, cz, st.lightning_rod("up"))

    # --- equipment hut (x 17..21, z 9..15) east of the mast, iron door on the south face
    hx1, hz1, hx2, hz2 = 17, 9, 21, 15
    hut_shell(s, hx1, hz1, hx2, hz2, G)
    for z in (11, 12, 13):
        s.set(hx2, G + 3, z, PANE)
        s.set(hx1, G + 3, z, PANE)
    for x in (18, 19, 20):
        s.set(x, G + 3, hz1, PANE)
    s.set(20, G + 3, hz2, PANE)
    s.set(19, G + 2, hz1 - 1, st.trapdoor("iron", "north", "top", open=True))   # panels on the walls
    s.set(hx2 + 1, G + 2, 10, st.trapdoor("iron", "east", "top", open=True))
    s.set(hx2 + 1, G + 2, 14, st.button("stone", "wall", "east"))
    s.set(19, G + 1, hz2, st.door("iron", "north", "lower")); s.set(19, G + 2, hz2, st.door("iron", "north", "upper"))
    s.set(20, G + 2, hz2 + 1, st.button("stone", "wall", "south"))
    s.set(18, G + 2, hz2 + 1, st.button("stone", "wall", "south"))          # inside call button on the wall
    s.set(18, G + 3, hz2 + 1, st.wall_torch("south", soul=True))
    s.set(19, G, hz2 + 1, st.slab("smooth_stone")); s.set(19, G, hz2 + 2, st.slab("smooth_stone"))   # step
    s.set(19, G + 5, hz1 + 2, SEA); s.set(19, G + 5, hz2 - 2, SEA)
    console(s, 18, G + 1, hz1 + 1, "north"); console(s, 20, G + 1, hz1 + 1, "north")
    s.set(19, G + 1, hz1 + 1, DARK); s.set(19, G + 2, hz1 + 1, st.slab("polished_deepslate"))
    s.set(20, G + 1, 13, st.bed("cyan", "north", "head")); s.set(20, G + 1, 14, st.bed("cyan", "north", "foot"))
    s.add_chest(18, G + 1, 14, "east", "minecraft:chests/igloo_chest")
    s.set(18, G + 1, 12, st.facing_block("minecraft:barrel", "up"))
    s.set(18, G + 1, 13, LAB["machine_dark"])
    s.set(18, G + 2, 13, st.facing_block("minecraft:observer", "east"))
    s.add_sign(18, G + 3, 11, "minecraft:warped_wall_sign[facing=east]", ["BALISE NORD", "portee 40 km", "batterie 12%", "relance manuelle"])
    s.add_sign(20, G + 3, hz2 + 1, "minecraft:warped_wall_sign[facing=south]", ["RELAIS R-7", "danger", "haute tension", ""])
    # cable from platform 1 down onto the hut roof, vent stack, rooftop solar panel
    s.set(hx1, G + 12, 12, st.chain("x"))
    for y in range(G + 7, G + 12):
        s.set(hx1, y, 12, st.chain("y"))
    s.set(hx1, G + 6, 12, DARK)                                             # junction box on the roof lip
    sh.box(s, 21, G + 7, 14, 21, G + 8, 14, DARK)
    s.set(21, G + 9, 14, st.trapdoor("iron", "north", "bottom", open=False))
    for x in range(18, 21):
        s.set(x, G + 7, 10, LAB["console"])
    s.set(18, G + 8, 10, st.end_rod("up"))

    # --- guy-lines: from platform-2 corner posts down to 2x2 anchors sunk in the snow (face-connected chains)
    for sx in (-1, 1):
        for sz in (-1, 1):
            guy_line(s, (cx + 4 * sx, G + 25, cz + 3 * sz), (cx + 11 * sx, cz + 11 * sz))

    # --- textures + weathering, then the (clean) dish on platform 1's east arm
    sh.texturize(s, WHITE, MIX_WHITE, seed=31)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=32)
    sh.texturize(s, DARK, MIX_DARK, seed=33)
    sh.snow_cover(s, y_min=G + 1, prob=0.35, seed=6, skip=["quartz", "calcite", "white_concrete", "lamp", "iron", "glass",
                                                          "lantern", "observer", "froglight", "daylight", "wool"])
    small_dish(s, cx + 6, G + 13, cz, 90, 35, R=3, depth=0.9)
    finish_dishes(s)
    return s.cropped(pad=1)


def build():
    return {"comms_array": build_comms_array(), "beacon_tower": build_beacon_tower()}

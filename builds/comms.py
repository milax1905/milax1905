"""Communications structures: a deep-space dish station (comms_array) and a slender relay/beacon tower
(beacon_tower). Clean white/quartz surfaces on dark deepslate structure, lavender accents, red aviation lamps,
pearlescent lantern at the top of the mast. Both are pasted onto snow (ground=2): nothing is placed below the
surface except footings, sleepers and the crystal spike root, so `//paste -a` sits them in the terrain."""
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
GLASS = "minecraft:glass"
PANE = "minecraft:glass_pane"
TRODDEN = CAMP["trodden_snow"]
# placeholders for the dish shells: converted at the very end so the global texturize / snow_cover never touch them
DISH_FACE = "minecraft:white_wool"
DISH_BACK = "minecraft:light_gray_wool"
DISH_FACE_MIX = [(WHITE, 8), ("minecraft:quartz_block", 2)]
DISH_BACK_MIX = [("minecraft:light_gray_concrete_powder", 7), (LGRAY, 3)]


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


def tilted_dish(s, C, R, depth, tilt, az, front=DISH_FACE, back=DISH_BACK, rim=DARK, rim_w=1.5, ribs=0,
                rib_block=DARK, lamps=0, snow=False, hub=None, step=0.33, rib_off=-2.2, hub_r=1.3,
                back_ring=False, mid_ring=None, seams=None, back_rim=False):
    """Parabolic bowl of radius R and depth `depth` (at the rim) centred at C, axis tilted. Two layers:
    `front` (reflecting face) and `back` (1 block behind), both edged by a `rim` band `rim_w` wide so the
    dish always has a dark outline. Ribs sit `rib_off` behind the face (proud of the back shell), optional
    stiffening ring on the back, a structure ring / radial seams drawn on the face, rim lamps, snow build-up
    on the low side. Returns (u, v, n, k) for callers that add struts / feed horns."""
    C = np.array(C, dtype=float)
    u, v, n = dish_basis(tilt, az)
    k = depth / (R * R)
    layers = ([(-1.0, back)] if back else []) + [(0.0, front)]
    lows = []
    for off, blk in layers:
        for a in np.arange(-R, R + step, step):
            for b in np.arange(-R, R + step, step):
                r2 = a * a + b * b
                if r2 > R * R:
                    continue
                r = math.sqrt(r2)
                p = C + u * a + v * b + n * (k * r2 + off)
                x, y, z = rp(p)
                b_ = blk
                if rim and r >= R - rim_w and (off == 0.0 or back_rim):
                    b_ = rim
                elif off == 0.0 and mid_ring and abs(r - R * 0.55) < 0.38:
                    b_ = mid_ring
                elif off == 0.0 and seams and r > 1.5:
                    ph = math.atan2(b, a)
                    sector = ph * seams[1] / (2 * math.pi)
                    if abs(sector - round(sector)) * (2 * math.pi * r / seams[1]) < 0.4:
                        b_ = seams[0]
                s.set(x, y, z, b_)
                if off == 0.0 and snow and (p[1] - C[1]) < -0.45 * R * math.sin(math.radians(tilt)):
                    lows.append((x, y, z, p[1] - C[1]))
    # ribs on the back: a row proud of the back shell, plus a deeper row toward the hub (truss)
    for i in range(ribs):
        ph = 2 * math.pi * i / ribs
        for r in np.arange(0, R - 0.4, 0.25):
            a, b = r * math.cos(ph), r * math.sin(ph)
            offs = (rib_off,) if R <= 6 else ((rib_off, rib_off - 0.9) if r < R * 0.3 else (rib_off,))
            for off in offs:
                p = C + u * a + v * b + n * (k * r * r + off)
                s.set(*rp(p), rib_block)
    if hub:
        p = C + n * (rib_off - 0.7)
        sh.sphere(s, *rp(p), hub_r, hub)
    if back_ring:                                   # stiffening ring on the back at half radius, on the rib line
        r = R * 0.55
        for ph in np.arange(0, 2 * math.pi, 0.03):
            a, b = r * math.cos(ph), r * math.sin(ph)
            s.set(*rp(C + u * a + v * b + n * (k * r * r + rib_off)), rib_block)
    # lamps set into the rim, flush with the front face
    for i in range(lamps):
        ph = 2 * math.pi * (i + 0.5) / lamps
        a, b = (R - 0.6) * math.cos(ph), (R - 0.6) * math.sin(ph)
        p = C + u * a + v * b + n * (k * (a * a + b * b) + 0.35)
        s.set(*rp(p), LAMP)
    # snow build-up in the low part of the bowl
    if snow:
        low_min = min(l[3] for l in lows) if lows else 0
        for (x, y, z, dy) in lows:
            if s.is_air(x, y + 1, z):
                depth01 = (dy - low_min) / max(1e-6, (-0.45 * R * math.sin(math.radians(tilt)) - low_min))
                nlay = int(round(6 - 5 * depth01))
                if nlay >= 8:
                    s.set(x, y + 1, z, GROUND["snow"])
                else:
                    s.set(x, y + 1, z, st.snow_layer(max(1, nlay)))
    return u, v, n, k


def finish_dishes(s):
    """Convert the dish placeholders into their clean (close-shade) concrete mixes."""
    sh.texturize(s, DISH_FACE, DISH_FACE_MIX, seed=41)
    sh.texturize(s, DISH_BACK, DISH_BACK_MIX, seed=42)


def strut(s, p1, p2, end_len=1.5):
    """Feed-horn strut: a solid stepped line of dark deepslate (reads as a structure line over the white face)
    with iron feet at both ends."""
    p1, p2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    length = float(np.linalg.norm(p2 - p1))
    n = max(1, int(math.ceil(length)))
    for i in range(n + 1):
        t = i / n
        d = t * length
        blk = IRON if (d < end_len or length - d < end_len) else DARK
        s.set(*rp(p1 + (p2 - p1) * t), blk)


def chain_col(s, x, y1, y2, z):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        s.set(x, y, z, st.chain("y"))


def chain_run(s, p1, p2):
    """Straight horizontal / vertical chain run, axis following the run."""
    dx, dy, dz = abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), abs(p2[2] - p1[2])
    axis = "y" if dy >= max(dx, dz) else ("x" if dx >= dz else "z")
    sh.line(s, p1, p2, st.chain(axis))


def guy_line(s, top, anchor):
    """Stepped guy-line: vertical chain columns that overlap one block at every lateral step (never a gap),
    lateral moves alternating x / z so successive columns touch face to face. `top` is the first chain block
    (must be face-adjacent to a structure block), `anchor` is (x, z): the line ends on an iron anchor block
    at G+1 with a deepslate footing at G."""
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
        chain_col(s, x, cur_y, yj + 1, z)             # vertical run down to just above the step
        s.set(x, yj, z, st.chain(axis))               # horizontal link toward the next column
        if axis == "x":
            x += sgn
        else:
            z += sgn
        cur_y = yj                                    # next column starts beside the link (face contact)
    chain_col(s, x, cur_y, y_bot, z)
    s.set(x, g + 1, z, IRON)                          # anchor block
    s.set(x, g, z, DARK)
    s.set(x, g - 1, z, DARK)


def console(s, x, y, z, facing_wall: str):
    """Desk console: dark base, daylight-detector top, lit screen on the wall behind (facing_wall = wall side)."""
    s.set(x, y, z, DARK)
    s.set(x, y + 1, z, LAB["console"])
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing_wall]
    s.set(x + dx, y + 2, z + dz, LAMP)


def small_dish(s, px, py, pz, az, tilt, R=4, depth=1.1, post_from=None):
    """Small dish on a yoke: a light-gray yoke block on the post shows the tilt; dark 1-block rim, 4 ribs,
    hub, feed rod on a bar strut."""
    s.set(px, py, pz, LGRAY)                                       # yoke
    _, _, n0 = dish_basis(tilt, az)
    Cs = np.array([px, py, pz], dtype=float) + n0 * 2.4
    sh.line(s, (px, py, pz), rp(Cs), IRON)
    us, vs, ns, ks = tilted_dish(s, Cs, R, depth, tilt, az, rim=DARK, rim_w=0.6, ribs=0, hub=IRON, step=0.3,
                                 hub_r=0.8, rib_off=-1.2, back=None)
    Fs = Cs + ns * (R * R / (4 * depth))
    sh.line(s, rp(Cs), rp(Fs), IRON)
    s.set(*rp(Fs), DARK)
    fx, fy, fz = rp(Fs)
    s.set(fx, fy + 1, fz, st.end_rod("up"))                       # feed tip, face-adjacent to the focus block


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

    # --- concrete apron around the pedestal (surface level), ground lights, then plinth
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

    sh.cylinder(s, cx, G + 1, cz, 4.0, 0, DARK, axis="y")
    sh.ring_stairs(s, cx, G + 1, cz, 4.9, "deepslate_tile", half="bottom")
    sh.cylinder(s, cx, G + 2, cz, 2.6, 6, DARK, axis="y")            # column G+2..G+8
    sh.ring(s, cx, G + 5, cz, 3.2, PURPUR, thickness=1.0)              # lavender band
    for i in range(4):
        ph = math.pi / 4 + i * math.pi / 2
        x, z = round(cx + 2.9 * math.cos(ph)), round(cz + 2.9 * math.sin(ph))
        sh.box(s, x, G + 2, z, x, G + 8, z, IRON)
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
    C = P + dish_basis(tilt, az)[2] * 3.4
    sh.line(s, rp(P), rp(C), IRON)                                     # pivot into the hub
    # actuator strut from the yoke to the low back of the dish
    u0, v0, n0 = dish_basis(tilt, az)
    low_back = C + v0 * 5.0 * (1 if v0[1] < 0 else -1) + n0 * (-2.6)
    sh.line(s, (cx, G + 10, cz + 3), rp(low_back), IRON)

    # --- control hut (x 30..38, z 31..37), door on the west side facing the pedestal
    hx1, hz1, hx2, hz2 = 30, 31, 38, 37
    sh.box(s, hx1, G, hz1, hx2, G, hz2, LGRAY)                        # floor at surface level
    sh.hollow_box(s, hx1, G + 1, hz1, hx2, G + 5, hz2, WHITE, floor=False, ceiling=True)
    for (x, z) in ((hx1, hz1), (hx2, hz1), (hx1, hz2), (hx2, hz2)):    # corner pillars
        sh.box(s, x, G + 1, z, x, G + 5, z, DARK)
    for x in range(hx1 + 1, hx2):                                       # base course + light-gray mid band
        for z in (hz1, hz2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    for z in range(hz1 + 1, hz2):
        for x in (hx1, hx2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    for x in (32, 33, 35, 36):                                          # window strips north + south
        s.set(x, G + 3, hz1, PANE); s.set(x, G + 3, hz2, PANE)
    for z in (33, 34, 35):                                              # east window strip
        s.set(hx2, G + 3, z, PANE)
    s.set(hx1, G + 3, 36, PANE)                                         # west: small window south of the door
    for x in (32, 36):                                                  # lamps in the top course
        s.set(x, G + 5, hz1, LAMP); s.set(x, G + 5, hz2, LAMP)
    s.set(hx2, G + 5, 34, LAMP)
    sh.box_edge_stairs(s, hx1, G + 5, hz1, hx2, hz2, "deepslate_tile", half="top")   # eaves
    for (x, z) in ((31, hz1 - 1), (37, hz1 - 1), (31, hz2 + 1), (37, hz2 + 1), (hx2 + 1, 34)):
        s.set(x, G + 4, z, st.end_rod("down"))                          # lights hanging under the eave
    # roof: dark slab ring on the wall line, light slab cap inset, vent stack, AC unit, antenna
    sh.box(s, hx1 + 1, G + 6, hz1 + 1, hx2 - 1, G + 6, hz2 - 1, st.slab("smooth_stone"))
    sh.box(s, 37, G + 6, 36, 37, G + 8, 36, DARK)                       # vent stack
    s.set(37, G + 9, 36, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(37, G + 7, 35, st.trapdoor("iron", "north", "bottom", open=True))
    sh.box(s, 32, G + 6, 32, 33, G + 6, 33, LAB["machine"])             # roof AC unit
    s.set(32, G + 7, 32, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(33, G + 7, 33, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(36, G + 7, 32, st.lightning_rod("up"))
    s.set(31, G + 7, 36, st.end_rod("up"))
    # door (west wall) + buttons + porch light
    s.set(hx1, G + 1, 34, st.door("dark_oak", "east", "lower"))
    s.set(hx1, G + 2, 34, st.door("dark_oak", "east", "upper"))
    s.set(hx1 - 1, G + 2, 33, st.button("stone", "wall", "west"))
    s.set(hx1 + 1, G + 2, 33, st.button("stone", "wall", "east"))
    s.set(hx1 - 1, G + 3, 34, st.wall_torch("west", soul=True))
    s.set(hx1 - 1, G, 34, LGRAY); s.set(hx1 - 2, G, 34, LGRAY)          # door step
    # interior (air G+1..G+4, ceiling G+5)
    sh.box(s, hx1 + 1, G + 1, hz1 + 1, hx2 - 1, G + 4, hz2 - 1, "air")
    sh.box(s, hx1 + 1, G + 5, hz1 + 1, hx2 - 1, G + 5, hz2 - 1, WHITE)
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
    sh.box(s, 16, G, 38, 16, G + 5, 38, DARK)                            # flag pole by the gate
    s.set(16, G + 6, 38, st.banner("cyan", 4))
    s.set(16, G + 3, 38, st.wall_banner("light_blue", "south"))

    # --- textures + weathering on everything but the dishes (built afterwards, kept clean)
    sh.texturize(s, WHITE, MIX_WHITE, seed=21)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=22)
    sh.texturize(s, DARK, MIX_DARK, seed=23)
    sh.snow_cover(s, y_min=G + 1, prob=0.25, seed=5, skip=["quartz", "calcite", "white_concrete", "lamp", "iron", "glass",
                                                          "lantern", "observer", "purpur", "froglight", "wool"])

    # --- the big dish (clean: dark rim, light-gray back, ribs proud of the back, structure ring + seams on the face)
    u, v, n, k = tilted_dish(s, C, R, depth, tilt, az, front=DISH_FACE, back=DISH_BACK, rim=DARK, rim_w=0.9,
                             ribs=8, rib_block=IRON, lamps=8, snow=True, hub=DARK, rib_off=-2.2, hub_r=1.4,
                             back_ring=True, mid_ring=DARK)
    sh.line(s, rp(P), rp(C), IRON)                                     # re-assert the pivot through the hub
    # feed horn on 3 struts at the focal point
    f = R * R / (4 * depth)
    F = C + n * f
    Fi = rp(F)
    for ph in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3):
        a, b = (R - 0.8) * math.cos(ph), (R - 0.8) * math.sin(ph)
        pr = C + u * a + v * b + n * (k * (a * a + b * b) + 0.6)
        strut(s, pr, F, end_len=1.5)
    s.set(*Fi, IRON)
    s.set(Fi[0], Fi[1] + 1, Fi[2], LAMP)
    s.set(Fi[0], Fi[1] - 1, Fi[2], SEA)
    s.set(Fi[0], Fi[1] - 2, Fi[2], st.end_rod("down"))
    for dx in (-1, 1):
        s.set(Fi[0] + dx, Fi[1], Fi[2], DARK)
        s.set(Fi[0] + dx, Fi[1] - 1, Fi[2], st.trapdoor("iron", "east" if dx > 0 else "west", "top", open=True))
    s.set(Fi[0], Fi[1], Fi[2] - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(Fi[0], Fi[1], Fi[2] + 1, st.trapdoor("iron", "south", "bottom", open=True))

    # --- two small dishes on posts (north corners)
    for (px, pz, az_, tl) in ((7, 8, -25, 45), (35, 8, 20, 50)):
        sh.cylinder(s, px, G, pz, 2.2, 0, DARK_ALT, axis="y")
        sh.box(s, px, G, pz, px, G + 6, pz, DARK)
        sh.ring_stairs(s, px, G + 1, pz, 1.4, "deepslate_tile", half="bottom")
        small_dish(s, px, G + 7, pz, az_, tl)
        chain_run(s, (px, G + 1, pz + 1), (px, G + 1, pz + 6))
    finish_dishes(s)
    return s.cropped(pad=1)


# ----------------------------------------------------------------------------- beacon tower
def build_beacon_tower():
    W, H, L, G = 19, 53, 19, 2
    s = Schematic(W, H, L, ground=G)
    cx, cz = 9, 9
    TOP = G + 40                                   # lantern base level

    def hw_at(y):
        return 2 if y <= G + 24 else 1

    # --- footings: sunk 2 blocks into the snow, tile plate at the surface
    for sx in (-2, 2):
        for sz in (-2, 2):
            sh.box(s, cx + sx - 1, G, cz + sz - 1, cx + sx + 1, G, cz + sz + 1, DARK_ALT)
            sh.box(s, cx + sx, G - 1, cz + sz, cx + sx, G, cz + sz, DARK)
    sh.box(s, cx - 2, G, cz - 2, cx + 2, G, cz + 2, DARK)
    # --- legs, rings and lattice bracing
    for y in range(G + 1, TOP + 1):
        hw = hw_at(y)
        for sx in (-hw, hw):
            for sz in (-hw, hw):
                s.set(cx + sx, y, cz + sz, IRON)
        yl = (y - G) % 6
        ring = yl == 0
        for i in range(-hw + 1, hw):
            cells = ((cx + i, cz - hw, "x"), (cx + i, cz + hw, "x"), (cx - hw, cz + i, "z"), (cx + hw, cz + i, "z"))
            for (x, z, along) in cells:
                if ring:
                    s.set(x, y, z, DARK)
                elif hw == 2:
                    if yl in (1, 5) and i != 0:                       # knee gussets at the leg / ring joints
                        if along == "x":
                            fac = "west" if i < 0 else "east"
                        else:
                            fac = "north" if i < 0 else "south"
                        s.set(x, y, z, st.stairs("polished_andesite", fac, "bottom" if yl == 1 else "top"))
                    elif yl == 3 or (yl in (2, 4) and i != 0):   # X bracing (with crossbar) between the gussets
                        s.set(x, y, z, BARS)
                else:
                    s.set(x, y, z, BARS)
    # taper transition: diagonals from hw2 to hw1
    for sx in (-1, 1):
        for sz in (-1, 1):
            sh.line(s, (cx + 2 * sx, G + 24, cz + 2 * sz), (cx + sx, G + 27, cz + sz), IRON)
    # centre core in the upper section (ladder support) and ladders
    sh.box(s, cx, G + 24, cz, cx, TOP, cz, DARK)
    for y in range(G + 1, G + 25):
        s.set(cx - 2, y, cz - 1, st.facing_block("minecraft:ladder", "south"))
    for y in range(G + 25, TOP + 1):
        s.set(cx - 1, y, cz, st.facing_block("minecraft:ladder", "west"))

    # --- platforms every 12 blocks
    def platform(y, hw):
        sh.box(s, cx - hw, y, cz - hw, cx + hw, y, cz + hw, LGRAY)
        sh.box_edge_stairs(s, cx - hw + 1, y, cz - hw + 1, cx + hw - 1, cz + hw - 1, "deepslate_tile", half="top")
        for x in range(cx - hw, cx + hw + 1):
            for z in (cz - hw, cz + hw):
                s.set(x, y + 1, z, BARS)
        for z in range(cz - hw, cz + hw + 1):
            for x in (cx - hw, cx + hw):
                s.set(x, y + 1, z, BARS)
        for (x, z) in ((cx - hw, cz - hw), (cx + hw, cz - hw), (cx - hw, cz + hw), (cx + hw, cz + hw)):
            s.set(x, y + 1, z, DARK)
            s.set(x, y + 2, z, st.end_rod("up"))
        lh = hw_at(y)
        for sx in (-lh, lh):
            for sz in (-lh, lh):
                s.set(cx + sx, y, cz + sz, IRON)
                s.set(cx + sx, y + 1, cz + sz, IRON)
        for sx in (-1, 1):                                              # under-platform braces from the legs
            for sz in (-1, 1):
                sh.line(s, (cx + lh * sx, y - 4, cz + lh * sz), (cx + hw * sx, y - 1, cz + hw * sz), BARS)
        s.set(cx, y, cz, SEA)

    platform(G + 12, 3)
    platform(G + 24, 3)
    platform(G + 36, 2)
    for y in (G + 12, G + 24):                                           # ladder holes
        s.set(cx - 2, y, cz - 1, st.facing_block("minecraft:ladder", "south"))
    s.set(cx - 1, G + 36, cz, st.facing_block("minecraft:ladder", "west"))
    s.set(cx, G + 24, cz, DARK)

    # --- platform 2: antenna arms (end rods) north and south, lightning rods
    for dz in (-1, 1):
        z0 = cz + 3 * dz
        for i in range(0, 3):
            s.set(cx, G + 25, z0 + dz * i, IRON)
        s.set(cx, G + 25, z0 + dz * 3, DARK)
        s.set(cx, G + 26, z0 + dz * 3, st.end_rod("up"))
        s.set(cx, G + 25, z0 + dz * 4, st.end_rod("south" if dz > 0 else "north"))
    for dx in (-1, 1):
        s.set(cx + dx * 3, G + 26, cz, st.lightning_rod("up"))
    # --- platform 3: small yagi arms
    for dx in (-1, 1):
        s.set(cx + dx * 3, G + 37, cz, st.end_rod("east" if dx > 0 else "west"))
        s.set(cx + dx * 2, G + 38, cz, st.lightning_rod("up"))

    # --- red aviation lamps on the outside of the legs
    for (y, hw) in ((G + 6, 2), (G + 18, 2), (G + 30, 1), (G + 39, 1)):
        for sx in (-1, 1):
            for sz in (-1, 1):
                if y in (G + 6, G + 39) and sx != sz:
                    continue
                s.set(cx + sx * (hw + 1), y, cz + sz * hw, LAMP)

    # --- top lantern: base, glass housing, pearlescent core, cap, spike
    sh.box(s, cx - 2, TOP, cz - 2, cx + 2, TOP, cz + 2, DARK)
    sh.box_edge_stairs(s, cx - 2, TOP, cz - 2, cx + 2, cz + 2, "deepslate_tile", half="top")
    for y in range(TOP + 1, TOP + 4):
        sh.hollow_box(s, cx - 2, y, cz - 2, cx + 2, y, cz + 2, GLASS, floor=False, ceiling=False)
        for (x, z) in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
            s.set(x, y, z, IRON)
    s.set(cx, TOP + 1, cz, SEA); s.set(cx, TOP + 2, cz, FROG); s.set(cx, TOP + 3, cz, SEA)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set(cx + dx, TOP + 2, cz + dz, FROG)
        s.set(cx + dx, TOP + 1, cz + dz, st.slab("polished_deepslate"))
    sh.box(s, cx - 2, TOP + 4, cz - 2, cx + 2, TOP + 4, cz + 2, WHITE)
    sh.box_edge_stairs(s, cx - 2, TOP + 4, cz - 2, cx + 2, cz + 2, "quartz", half="top")
    sh.box(s, cx - 1, TOP + 5, cz - 1, cx + 1, TOP + 5, cz + 1, st.slab("smooth_quartz"))
    s.set(cx, TOP + 5, cz, DARK)
    s.set(cx, TOP + 6, cz, st.lightning_rod("up")); s.set(cx, TOP + 7, cz, st.lightning_rod("up"))
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        s.set(cx + dx, TOP + 5, cz + dz, st.end_rod("up"))
    s.set(cx + 2, TOP + 5, cz, LAMP); s.set(cx - 2, TOP + 5, cz, LAMP)

    # --- equipment hut (x 12..16, z 6..12), door facing the mast
    hx1, hz1, hx2, hz2 = 12, 6, 16, 12
    sh.box(s, hx1, G, hz1, hx2, G, hz2, LGRAY)
    sh.hollow_box(s, hx1, G + 1, hz1, hx2, G + 5, hz2, WHITE, floor=False, ceiling=True)
    for (x, z) in ((hx1, hz1), (hx2, hz1), (hx1, hz2), (hx2, hz2)):
        sh.box(s, x, G + 1, z, x, G + 5, z, DARK)
    for x in range(hx1 + 1, hx2):
        for z in (hz1, hz2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    for z in range(hz1 + 1, hz2):
        for x in (hx1, hx2):
            s.set(x, G + 1, z, DARK); s.set(x, G + 4, z, LGRAY)
    for z in (8, 9, 10):
        s.set(hx2, G + 3, z, PANE)
    for x in (13, 14, 15):
        s.set(x, G + 3, hz1, PANE); s.set(x, G + 3, hz2, PANE)
    s.set(14, G + 2, hz1 - 1, st.trapdoor("iron", "north", "top", open=True))   # panels on the walls
    s.set(13, G + 2, hz2 + 1, st.trapdoor("iron", "south", "top", open=True))
    s.set(hx2 + 1, G + 2, 8, st.trapdoor("iron", "east", "top", open=True))
    s.set(14, G + 2, hz2 + 1, st.button("stone", "wall", "south"))
    s.set(hx2 + 1, G + 2, 9, st.button("stone", "wall", "east"))
    sh.box(s, hx1 + 1, G + 1, hz1 + 1, hx2 - 1, G + 4, hz2 - 1, "air")     # interior 4 high
    sh.box(s, hx1 + 1, G + 5, hz1 + 1, hx2 - 1, G + 5, hz2 - 1, WHITE)
    sh.box_edge_stairs(s, hx1, G + 5, hz1, hx2, hz2, "deepslate_tile", half="top")
    sh.box(s, hx1 + 1, G + 6, hz1 + 1, hx2 - 1, G + 6, hz2 - 1, st.slab("smooth_stone"))
    s.set(hx1, G + 1, 9, st.door("dark_oak", "east", "lower")); s.set(hx1, G + 2, 9, st.door("dark_oak", "east", "upper"))
    s.set(hx1 - 1, G + 2, 8, st.button("stone", "wall", "west"))
    s.set(hx1 - 1, G + 3, 10, st.wall_torch("west", soul=True))
    s.set(14, G + 5, 9, SEA)
    console(s, 15, G + 1, 7, "north"); console(s, 13, G + 1, 7, "north")
    s.set(14, G + 1, 7, DARK); s.set(14, G + 2, 7, st.slab("polished_deepslate"))
    s.add_chest(15, G + 1, 11, "west", "minecraft:chests/igloo_chest")
    s.set(13, G + 1, 11, st.facing_block("minecraft:barrel", "up"))
    s.set(14, G + 1, 11, LAB["machine_dark"])
    s.set(14, G + 2, 11, st.facing_block("minecraft:observer", "north"))
    s.add_sign(13, G + 3, 11, "minecraft:warped_wall_sign[facing=north]", ["BALISE NORD", "portee 40 km", "batterie 12%", "relance manuelle"])
    s.add_sign(hx1 - 1, G + 3, 8, "minecraft:warped_wall_sign[facing=west]", ["RELAIS R-7", "danger", "haute tension", ""])
    # cable from platform 1 down onto the hut roof, vent stack, rooftop solar panel
    for y in range(G + 7, G + 12):
        s.set(12, y, 9, st.chain("y"))
    s.set(12, G + 6, 9, DARK)
    s.set(11, G + 1, 9, st.chain("x"))
    sh.box(s, 16, G + 6, 11, 16, G + 7, 11, DARK)
    s.set(16, G + 8, 11, st.trapdoor("iron", "north", "bottom", open=False))
    for x in range(13, 16):
        s.set(x, G + 7, 7, LAB["console"])
    s.set(13, G + 6, 7, DARK); s.set(15, G + 6, 7, DARK)

    # --- guy-lines: from the platform-3 corner posts down to anchors in the snow, stepped without gaps
    for sx in (-1, 1):
        for sz in (-1, 1):
            guy_line(s, (cx + 3 * sx, G + 37, cz + 2 * sz), (cx + 8 * sx, cz + 8 * sz))

    # --- textures + weathering, then the (clean) dish on platform 1's east arm
    sh.texturize(s, WHITE, MIX_WHITE, seed=31)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=32)
    sh.texturize(s, DARK, MIX_DARK, seed=33)
    sh.snow_cover(s, y_min=G + 1, prob=0.3, seed=6, skip=["quartz", "calcite", "white_concrete", "lamp", "iron", "glass",
                                                         "lantern", "observer", "froglight", "daylight", "wool"])
    sh.box(s, cx + 3, G + 13, cz, cx + 5, G + 13, cz, IRON)
    small_dish(s, cx + 5, G + 14, cz, 90, 35, R=3, depth=0.9)
    finish_dishes(s)
    return s.cropped(pad=1)


def build():
    return {"comms_array": build_comms_array(), "beacon_tower": build_beacon_tower()}

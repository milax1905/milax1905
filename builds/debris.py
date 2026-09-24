"""Debris sites: a spilled cargo drop (shipping containers under a parachute) and a field of fallen orbital debris
(satellite, heat shield, cracked fuel tank, hull panels). Both sit on a thin snow slab (ground=2)."""
import math
import random

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_SCORCH, MIX_WHITE

FRAME = "minecraft:polished_deepslate"          # container corner posts / bottom rails
FRAME_STAIR = "deepslate_tile"
FLOOR = "minecraft:spruce_planks"
LGP = "minecraft:light_gray_concrete_powder"
LGC = "minecraft:light_gray_concrete"
SNOW = GROUND["snow"]
COL = {
    "cyan": ("minecraft:cyan_concrete", "minecraft:cyan_concrete_powder"),
    "light_gray": ("minecraft:light_gray_concrete", "minecraft:light_gray_concrete_powder"),
    "white": ("minecraft:white_concrete", "minecraft:white_concrete_powder"),
    "purple": ("minecraft:purple_concrete", "minecraft:purple_concrete_powder"),
}
_DIRN = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
_OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
_DV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
BARREL_UP = "minecraft:barrel[facing=up,open=false]"


def _barrel(facing="up"):
    return f"minecraft:barrel[facing={facing},open=false]"


def _vec(axis):
    """(+a vector, +c vector) in (dx, dz) for a container along `axis`."""
    return ((1, 0), (0, 1)) if axis == "x" else ((0, 1), (1, 0))


def container(s, x0, y0, z0, length, width, height, axis, color, door_end=1, doors="closed", tipped=False):
    """Corrugated shipping container. Local coords: a along `axis`, c across, y up. Returns P(a, c, y) -> (x, y, z).
    doors: 'closed' | 'open' (both leaves swung out) | 'half' (one leaf) | 'none'."""
    conc, powd = COL[color]
    av, cv = _vec(axis)

    def P(a, c, y):
        return (x0 + av[0] * a + cv[0] * c, y0 + y, z0 + av[1] * a + cv[1] * c)

    def put(a, c, y, b):
        x, yy, z = P(a, c, y)
        s.set(x, yy, z, b)

    top = height - 1
    for a in range(length):
        for c in range(width):
            for y in range(height):
                edge_a, edge_c = a in (0, length - 1), c in (0, width - 1)
                if edge_a and edge_c:                         # corner posts
                    put(a, c, y, FRAME); continue
                if y == 0:
                    put(a, c, y, FRAME if (edge_a or edge_c) else FLOOR); continue
                rib = (y % 2 == 0) if tipped else (a % 2 == 0)
                skin = conc if rib else powd
                if y == top:
                    put(a, c, y, skin); continue
                if edge_c or edge_a:
                    put(a, c, y, skin); continue
                put(a, c, y, "air")                        # interior
    # doors (iron trapdoors) on one end
    if doors != "none":
        a_door = length - 1 if door_end > 0 else 0
        out_vec = av if door_end > 0 else (-av[0], -av[1])
        closed_facing = _DIRN[(-out_vec[0], -out_vec[1])]  # sits flush on the outer face
        a_out = a_door + door_end
        leaves = list(range(1, width - 1))
        for y in range(1, top):
            for i, c in enumerate(leaves):
                swung = doors == "open" or (doors == "half" and i == 0)
                if not swung:
                    put(a_door, c, y, st.trapdoor("iron", closed_facing, "top" if y % 2 else "bottom", open=True))
                else:
                    put(a_door, c, y, "air")
                    hinge_side = cv if c == leaves[0] else (-cv[0], -cv[1])    # leaf lies against its hinge post
                    put(a_out, c, y, st.trapdoor("iron", _DIRN[hinge_side], "top" if y % 2 else "bottom", open=True))
    return P


def roof_detail(s, P, length, width, height, seed=0, hatch=True, rib=True, rust=1, snow_prob=0.45):
    """Roof furniture: a polished-deepslate rib across the middle, iron-trapdoor hatches, rust patches and
    wind-blown snow (taller layers on the windward = west half)."""
    rng = random.Random(seed)
    top = height - 1
    if rib:
        a_mid = length // 2
        for c in range(width):
            x, y, z = P(a_mid, c, top)
            s.set(x, y, z, FRAME)
    if hatch:
        for a in (1, length - 2):
            if a == length // 2:
                continue
            x, y, z = P(a, 1 if width > 2 else 0, top)
            s.set(x, y + 1, z, st.trapdoor("iron", "north", "bottom", open=False))
    for _ in range(rust):
        a = rng.choice([i for i in range(1, length - 1) if i != length // 2])
        c = rng.randint(0, width - 1)
        x, y, z = P(a, c, top)
        s.set(x, y, z, LGP)
    xs = [P(a, 0, top)[0] for a in range(length)] + [P(0, c, top)[0] for c in range(width)]
    x_mid = (min(xs) + max(xs)) / 2.0
    for a in range(length):
        for c in range(width):
            x, y, z = P(a, c, top)
            if not s.is_air(x, y + 1, z) or "trapdoor" in s.get(x, y, z):
                continue
            if rng.random() < snow_prob:
                n = rng.randint(3, 6) if x < x_mid else rng.randint(1, 2)
                s.set(x, y + 1, z, st.snow_layer(n))


def _drift(s, x, y, z, dx, dz, length, seed=0):
    """Snow drift tapering away from (x, z) in direction (dx, dz): 2 high near the object, then layers."""
    rng = random.Random(seed)
    for i in range(length):
        for w in (-1, 0, 1):
            px, pz = x + dx * i + (dz * w), z + dz * i + (dx * w)
            if not s.is_air(px, y, pz):
                continue
            h = length - i - abs(w) - rng.randint(0, 1)
            if h >= 2:
                s.set(px, y, pz, SNOW); s.set(px, y + 1, pz, st.snow_layer(rng.randint(2, 5)))
            elif h == 1:
                s.set(px, y, pz, SNOW)
            elif h == 0:
                s.set(px, y, pz, st.snow_layer(rng.randint(2, 6)))


def _straps(s, x, y_top, z1, z2, y_bottom):
    """Cargo strap: a chain over a roof (x fixed, along z) and down both sides to the ground."""
    for z in range(z1, z2 + 1):
        s.set(x, y_top + 1, z, st.chain("z"))
    for z in (z1 - 1, z2 + 1):
        for y in range(y_bottom, y_top + 2):
            s.set(x, y, z, st.chain("y"))
        s.set(x, y_bottom - 1, z, "minecraft:polished_deepslate_wall")


def _chain_line(s, p1, p2):
    """Straight chain run between two points; chain axis follows the dominant direction. Only fills air."""
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    n = max(abs(dx), abs(dy), abs(dz), 1)
    axis = "x" if abs(dx) >= max(abs(dy), abs(dz)) else ("z" if abs(dz) >= abs(dy) else "y")
    for i in range(n + 1):
        t = i / n
        x, y, z = round(x1 + dx * t), round(y1 + dy * t), round(z1 + dz * t)
        if s.is_air(x, y, z):
            s.set(x, y, z, st.chain(axis))


def _canopy(s, cx, cz, rx, ry, rz, y_surface, gores=6, seed=1):
    """Deflated parachute canopy: a half-buried wool mound (ellipsoid) with 6 wide gores (cyan / light gray),
    a carpet fringe of the gore colour and a couple of light-gray-concrete seam lines. Returns rim points."""
    rng = random.Random(seed)
    Y = y_surface + 1

    def gore(dx, dz):
        return int((math.atan2(dz, dx) + math.pi) / (2 * math.pi / gores)) % gores

    def fabric(g):
        return "cyan" if g % 2 == 0 else "light_gray"

    for x in range(s.w):
        for z in range(s.l):
            dx, dz = x - cx, z - cz
            r2 = (dx / rx) ** 2 + (dz / rz) ** 2
            if r2 > 1.0:
                continue
            h = ry * math.sqrt(max(0.0, 1.0 - r2)) * (0.9 + 0.2 * sh.value_noise2(x, z, seed, 4.0))
            fab = fabric(gore(dx, dz))
            n = int(round(h))
            for k in range(n):
                s.set(x, Y + k, z, f"minecraft:{fab}_wool")
            if n == 0:
                s.set(x, Y, z, f"minecraft:{fab}_carpet")
            elif h - n > 0.45:
                s.set(x, Y + n, z, f"minecraft:{fab}_carpet")
    # fringe ring (carpet of the gore colour) just outside the rim
    for x in range(s.w):
        for z in range(s.l):
            dx, dz = x - cx, z - cz
            r2 = (dx / (rx + 1.2)) ** 2 + (dz / (rz + 1.2)) ** 2
            if r2 <= 1.0 and s.is_air(x, Y, z) and rng.random() < 0.75:
                s.set(x, Y, z, f"minecraft:{fabric(gore(dx, dz))}_carpet")
    # seam / crease lines: light-gray-concrete lines along two gore boundaries on the mound top
    for g in (1, 4):
        a = -math.pi + g * 2 * math.pi / gores
        for t in range(1, int(max(rx, rz))):
            x, z = round(cx + t * rx / max(rx, rz) * math.cos(a)), round(cz + t * rz / max(rx, rz) * math.sin(a))
            ty = s.top_y(x, z)
            if ty >= Y and "wool" in s.get(x, ty, z):
                s.set(x, ty, z, LGC)
            elif ty >= Y and "carpet" in s.get(x, ty, z) and "wool" in s.get(x, ty - 1, z):
                s.set(x, ty, z, "air"); s.set(x, ty - 1, z, LGC)


def build_cargo():
    W, H, L, G = 32, 15, 32, 2
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=3)
    Y = G + 1
    rng = random.Random(3)

    # ---- impact crater (the drop point): packed snow / light gray floor, the stack sits IN it
    cx, cz = 13.5, 13.5
    sh.crater(s, cx, cz, 6.0, G, LGP, SNOW, SNOW, depth=1, rim_height=1, seed=8)
    sh.box(s, 9, G, 11, 18, G, 16, "air"); sh.box(s, 9, G - 1, 11, 18, G - 1, 16, LGP)
    sh.texturize(s, LGP, [(LGP, 5), ("minecraft:packed_ice", 2), ("minecraft:white_concrete_powder", 2)], seed=9)

    # ---- the stack: cyan big (sunk one block) + light_gray big on top (slid 1 block east), straps + beacon
    P1 = container(s, 10, G, 12, 8, 4, 4, "x", "cyan", doors="half")
    s.set(*P1(2, 1, 1), BARREL_UP); s.set(*P1(3, 1, 1), BARREL_UP); s.set(*P1(3, 1, 2), BARREL_UP)
    s.set(*P1(1, 2, 1), SHIP["container"]); s.set(*P1(5, 2, 1), "minecraft:white_shulker_box")
    s.set(*P1(4, 1, 2), st.lantern(hanging=True))
    P2 = container(s, 11, G + 4, 12, 8, 4, 4, "x", "light_gray", doors="closed")
    s.set(*P2(3, 1, 2), st.lantern(hanging=True))
    s.set(*P2(2, 1, 1), SHIP["container"]); s.set(*P2(2, 2, 1), SHIP["container"])
    roof_detail(s, P2, 8, 4, 4, seed=1, rust=2)
    # beacon strobe on the top container
    bx, by, bz = P2(4, 2, 4)
    s.set(bx, by, bz, "minecraft:iron_bars"); s.set(bx, by + 1, bz, SHIP["light"]); s.set(bx, by + 2, bz, st.end_rod("up"))
    s.set(bx - 1, by, bz, "minecraft:polished_deepslate_wall"); s.set(bx + 1, by, bz, "minecraft:polished_deepslate_wall")
    for x in (12, 16):                                                     # tie-down straps over the stack
        _straps(s, x, G + 7, 12, 15, G + 1)
    # snow blown against the west face of the stack (windward drift)
    for z in range(11, 17):
        s.set(9, Y, z, SNOW); s.set(9, Y + 1, z, st.snow_layer(rng.randint(2, 5)))
        s.set(8, Y, z, st.snow_layer(rng.randint(3, 7)))

    # ---- parachute: snagged on the top corner of the stack, draped down the east face, mound to the south-east
    top_y = G + 7
    for z in (14, 15):                                                     # fabric over the roof corner
        s.set(18, top_y + 1, z, "minecraft:cyan_carpet")
    knot = (19, top_y + 1, 15)
    s.set(*knot, "minecraft:light_gray_wool")                              # riser knot
    curtain = [(19, top_y - 2, top_y), (20, top_y - 4, top_y - 2), (21, top_y - 5, top_y - 4), (22, top_y - 6, top_y - 5)]
    for x, y1, y2 in curtain:
        for z in range(12, 17):
            fab = "cyan" if z in (12, 13) else "light_gray"
            for y in range(y1, y2 + 1):
                s.set(x, y, z, f"minecraft:{fab}_wool")
    s.set(22, top_y - 6, 17, "minecraft:light_gray_carpet"); s.set(22, top_y - 6, 11, "minecraft:cyan_carpet")
    _canopy(s, 25, 19, 6, 3.2, 5.5, G, gores=6, seed=4)
    # shroud lines: from the knot on the stack down to the far rim of the canopy (deepslate attachment loops)
    for (rx_, rz_) in ((30, 20), (28, 24), (23, 25)):
        s.set(rx_, Y, rz_, st.slab("polished_deepslate"))
        _chain_line(s, (knot[0], knot[1] - 1, knot[2]), (rx_, Y + 1, rz_))
    # drop-zone marker poles with cyan banners + one ground beacon
    for (x, z) in ((6, 7), (21, 27)):
        for y in range(Y, Y + 3):
            s.set(x, y, z, st.log("minecraft:stripped_spruce_log", "y"))
        s.set(x, Y + 3, z, st.banner("cyan", 4))
    s.set(20, G, 3, SHIP["light"]); s.set(20, Y, 3, st.end_rod("up"))

    # ---- shelter container (west): white, doors open to the south, someone lived here
    P3 = container(s, 2, Y, 13, 8, 4, 4, "z", "white", doors="open")
    s.set(*P3(1, 1, 1), st.bed("cyan", "north", "head")); s.set(*P3(2, 1, 1), st.bed("cyan", "north", "foot"))
    s.add_chest(*P3(1, 2, 1), "south", "minecraft:chests/igloo_chest")
    s.set(*P3(2, 2, 1), BARREL_UP); s.set(*P3(3, 2, 1), BARREL_UP)
    s.set(*P3(3, 1, 2), st.lantern(hanging=True)); s.set(*P3(5, 2, 2), st.lantern(hanging=True))
    s.set(*P3(4, 1, 1), "minecraft:cartography_table")
    s.set(*P3(5, 2, 1), "minecraft:white_carpet")
    s.add_sign(*P3(4, 1, 2), "minecraft:warped_wall_sign[facing=east]", ["JOURNAL 12", "tempete 3 jours", "plus de radio", "on part vers N"])
    s.add_sign(*P3(6, 4, 2), "minecraft:warped_wall_sign[facing=east]", ["ABRI", "largage 03", "vivres OK", "porte ouverte"])
    roof_detail(s, P3, 8, 4, 4, seed=2)
    # campfire + trodden snow + seat in front of the open doors
    s.set(3, Y, 23, st.campfire())
    for (x, z) in ((3, 22), (4, 22), (2, 23), (4, 23), (3, 24), (2, 24), (4, 25), (5, 22)):
        s.set(x, G, z, "minecraft:white_concrete_powder")
    s.set(5, Y, 23, st.stairs("spruce", "west"))                        # a seat by the fire
    s.set(2, Y, 25, _barrel("east"))

    # ---- purple container (north-east), burst open on its west side toward the stack, cargo spilled in a heap
    P4 = container(s, 22, Y, 4, 8, 4, 4, "z", "purple", door_end=1, doors="closed")
    for a in range(2, 6):
        for y in (1, 2):
            s.set(*P4(a, 0, y), "air")
    s.set(*P4(2, 0, 2), st.trapdoor("iron", "east", "top", open=True))        # bent sheets still hanging from the roof
    s.set(*P4(5, 0, 2), st.trapdoor("iron", "east", "top", open=True))
    s.set(*P4(3, 0, 3), st.stairs(FRAME_STAIR, "east", "top"))                 # buckled roof edge
    s.set(*P4(4, 0, 3), st.stairs(FRAME_STAIR, "east", "top"))
    s.set(*P4(1, 1, 1), st.lantern(hanging=False))
    s.set(*P4(6, 1, 1), BARREL_UP); s.set(*P4(6, 2, 1), SHIP["container"])
    s.set(*P4(3, 1, 1), _barrel("west")); s.set(*P4(4, 1, 1), BARREL_UP)
    s.add_sign(*P4(7, 4, 2), "minecraft:warped_wall_sign[facing=south]", ["CX-04", "FRAGILE", "labo Nord", ""])
    roof_detail(s, P4, 8, 4, 4, seed=3, rust=2)
    # the heap: 2 high against the torn wall (x=21), pallet boards around it, two barrels rolled away
    heap = [(21, 6, _barrel("west")), (21, 7, BARREL_UP), (21, 8, BARREL_UP), (21, 9, _barrel("north")),
            (20, 7, BARREL_UP), (20, 8, "minecraft:white_shulker_box"), (20, 6, st.slab("spruce")),
            (20, 9, st.trapdoor("spruce", "north", "bottom", open=False)), (19, 7, _barrel("east")),
            (19, 8, st.slab("spruce")), (19, 6, "minecraft:purple_concrete_powder"), (18, 7, _barrel("east")),
            (18, 9, st.trapdoor("iron", "north", "bottom", open=False)), (19, 10, st.slab("dark_oak"))]
    for x, z, b in heap:
        s.set(x, Y, z, b)
    s.set(21, Y + 1, 7, BARREL_UP); s.set(21, Y + 1, 8, SHIP["container"]); s.set(20, Y + 1, 7, "minecraft:light_gray_shulker_box")
    s.set(21, Y + 2, 7, st.snow_layer(2)); s.set(21, Y + 1, 9, st.snow_layer(1)); s.set(20, Y + 1, 8, st.snow_layer(2))
    s.set(19, Y + 1, 7, st.snow_layer(1))

    # ---- crushed white big container (south of the stack), roof stamped down one block at the east end
    P6 = container(s, 9, Y, 19, 8, 4, 4, "x", "white", door_end=-1, doors="closed")
    wc, wp = COL["white"]
    for a in range(4, 8):
        for c in range(4):
            s.set(*P6(a, c, 3), "air")
            if a == 7:
                continue
            s.set(*P6(a, c, 2), wc if a % 2 == 0 else wp)
    for c in (1, 2):
        s.set(*P6(7, c, 2), st.stairs(FRAME_STAIR, "east", "top"))
        s.set(*P6(4, c, 3), st.stairs(FRAME_STAIR, "west", "bottom"))
    for c in (0, 3):
        s.set(*P6(4, c, 3), st.slab("polished_deepslate"))
        s.set(*P6(7, c, 2), st.slab("polished_deepslate"))
    s.set(*P6(5, 1, 2), st.trapdoor("iron", "east", "bottom", open=False)); s.set(*P6(5, 2, 2), st.trapdoor("iron", "west", "bottom", open=False))
    s.set(*P6(2, 1, 1), st.lantern(hanging=True)); s.set(*P6(1, 1, 1), BARREL_UP); s.set(*P6(1, 2, 1), SHIP["container"])
    s.set(*P6(1, 3, 3), FRAME); s.set(*P6(2, 0, 3), LGP)                   # rib stub + rust on the intact roof
    s.set(*P6(1, 1, 4), st.trapdoor("iron", "north", "bottom", open=False))
    # ---- tipped light_gray small container (north), plowed into the snow, door hanging up
    P5 = container(s, 11, G, 5, 5, 3, 3, "x", "light_gray", door_end=-1, doors="none", tipped=True)
    s.set(*P5(-1, 1, 2), st.trapdoor("iron", "east", "top", open=False))
    s.set(*P5(-1, 1, 1), "air")
    s.set(*P5(2, 1, 2), st.trapdoor("iron", "north", "bottom", open=False))
    for (dx, dz) in ((-2, 0), (-2, 1), (-2, 2), (-3, 1), (-1, -1), (-1, 3), (5, 0), (5, 1)):   # snow plowed up around it
        s.set(11 + dx, Y, 5 + dz, SNOW)
    # ---- small cyan + small white stacked and skewed 90 degrees (south)
    P7 = container(s, 8, Y, 26, 5, 3, 3, "x", "cyan", doors="closed")
    P8 = container(s, 9, Y + 3, 25, 5, 3, 3, "z", "white", doors="closed")
    s.set(*P8(2, 1, 1), BARREL_UP)
    roof_detail(s, P8, 5, 3, 3, seed=5, rib=True, hatch=False)
    s.set(*P7(1, 0, 2), LGP)

    # ---- debris and weathering
    pallets = [(17, 9, st.slab("spruce")), (7, 20, st.trapdoor("iron", "north", "bottom", open=False)),
               (17, 21, st.slab("spruce")), (13, 24, st.slab("polished_deepslate")), (25, 12, st.slab("spruce"))]
    for x, z, b in pallets:
        if s.is_air(x, Y, z):
            s.set(x, Y, z, b)
    _drift(s, 26, Y, 6, 1, 0, 3, seed=3); _drift(s, 16, Y, 6, 1, 0, 3, seed=2)      # leeward drifts (east side)
    _drift(s, 17, Y, 21, 1, 0, 3, seed=4); _drift(s, 13, Y, 27, 1, 0, 2, seed=5)
    _drift(s, 6, Y, 17, 1, 0, 2, seed=6)
    sh.snow_cover(s, y_min=Y, prob=0.22, seed=5, layers=(1, 2),
                  skip=["wool", "carpet", "glass", "iron", "purple", "lantern", "barrel", "shulker", "planks", "table",
                        "bed", "log", "white_concrete", "sea_lantern", "powder", "concrete"])
    sh.snow_cover(s, y_min=G, prob=0.12, seed=15, layers=(1, 2), skip=["wool", "carpet", "glass", "iron", "purple",
                  "lantern", "barrel", "shulker", "planks", "table", "bed", "log", "sea_lantern", "concrete", "packed_ice"])
    return s.cropped(pad=1)


# ------------------------------------------------------------------------------------------ orbital debris
def _panel(s, x, y, z, dir, mat="smooth_quartz", core="minecraft:white_concrete"):
    """A small hull panel resting at an angle: slab -> stairs -> raised block -> top stair. dir = long axis."""
    dx, dz = _DV[dir]
    back = _OPP[dir]
    s.set(x, y, z, st.slab(mat))
    s.set(x + dx, y, z + dz, st.stairs(mat, dir))
    s.set(x + 2 * dx, y, z + 2 * dz, core)
    s.set(x + 2 * dx, y + 1, z + 2 * dz, st.stairs(mat, back, "top"))
    s.set(x + 3 * dx, y + 1, z + 3 * dz, st.slab(mat))
    s.set(x + 3 * dx, y, z + 3 * dz, FRAME)


def _sheet(s, x0, y, z0, dir, seed=0):
    """A big torn hull sheet, 5 long x 4 wide: a plate of quartz slabs lying on the snow that lifts gently at
    one end (bottom slab -> top slab -> one block up), propped on polished-deepslate chunks, with one dark
    polished-deepslate rib edge and a torn-off corner. Reads as a pale panel, not a staircase."""
    dx, dz = _DV[dir]
    wx, wz = (-dz, dx)                                        # width direction
    prof = [(0, "bottom"), (0, "bottom"), (0, "top"), (1, "bottom"), (1, "bottom")]
    for w in range(4):
        dark = (w == 3)
        mat = "polished_deepslate" if dark else ("quartz" if w % 2 == 0 else "smooth_quartz")
        for i, (dy, typ) in enumerate(prof):
            if i == 0 and w == 0:
                continue                                      # torn corner
            s.set(x0 + dx * i + wx * w, y + dy, z0 + dz * i + wz * w, st.slab(mat, typ))
    for w in (0, 3):                                          # props under the lifted end
        s.set(x0 + dx * 4 + wx * w, y, z0 + dz * 4 + wz * w, FRAME)
    s.set(x0 + dx * 3 + wx * 1, y, z0 + dz * 3 + wz * 1, "minecraft:cobbled_deepslate")
    s.set(x0 + dx * 1 + wx * 1, y + 1, z0 + dz * 1 + wz * 1, st.trapdoor("iron", _OPP[dir], "bottom", open=False))
    s.set(x0 + wx * 0, y, z0 + wz * 0, st.trapdoor("iron", dir, "bottom", open=True))       # torn flap


def _chunk(s, x, z, kind, seed=0):
    """2-4 block mini-cluster of wreckage on the snow (never a lone cube)."""
    y = s.top_y(x, z) + 1
    if "snow[" in s.get(x, y - 1, z):
        s.set(x, y - 1, z, "air"); y -= 1
    if kind == 0:
        s.set(x, y, z, st.slab("polished_deepslate")); s.set(x + 1, y, z, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(x, y, z + 1, "minecraft:cobbled_deepslate")
    elif kind == 1:
        s.set(x, y, z, st.stairs("quartz", "east")); s.set(x + 1, y, z, "minecraft:white_concrete")
        s.set(x + 1, y, z + 1, st.slab("polished_deepslate")); s.set(x + 1, y + 1, z, st.slab("quartz"))
    elif kind == 2:
        s.set(x, y, z, SHIP["frame"]); s.set(x - 1, y, z, st.slab("smooth_quartz"))
        s.set(x, y, z - 1, st.trapdoor("iron", "north", "bottom", open=False)); s.set(x, y + 1, z, st.snow_layer(2))
    else:
        s.set(x, y, z, "minecraft:cobbled_deepslate"); s.set(x + 1, y, z, st.stairs("polished_blackstone_brick", "west"))
        s.set(x, y, z - 1, st.slab("smooth_quartz")); s.set(x, y + 1, z, st.trapdoor("iron", "east", "bottom", open=True))


def _wing(s, x0, y, z0, length, dir, sag=True):
    """Solar panel wing: iron-bar rails, blue / light-blue glass cells, iron ribs. Along x (dir east/west)."""
    step = 1 if dir == "east" else -1
    for i in range(length):
        x = x0 + step * i
        yy = y - 1 if (sag and i >= length - 3) else y
        for dz in range(-2, 3):
            z = z0 + dz
            if abs(dz) == 2:
                s.set(x, yy, z, "minecraft:iron_bars" if i % 4 != 3 else "minecraft:iron_block")
            elif i % 4 == 3:
                s.set(x, yy, z, "minecraft:iron_block")
            else:
                s.set(x, yy, z, "minecraft:blue_stained_glass" if (i % 4) != 1 else "minecraft:light_blue_stained_glass")
            for k in (1, 2):                                   # nothing piled on the wing
                if s.get(x, yy + k, z) == SNOW:
                    s.set(x, yy + k, z, "air")


def _scorch_crater(s, cx, cz, r, G, depth, seed, lee=(1, 0)):
    """Impact crater that READS on white snow: scorch gradient floor (blackstone -> basalt -> light gray powder)
    that runs one block past the rim, dark tuff/basalt ejecta embedded in the surface, a taller snow rim with
    snow-layer steps on the leeward side."""
    rng = random.Random(seed)
    for x in range(s.w):
        for z in range(s.l):
            n = sh.value_noise2(x, z, seed, 6.0)
            dx, dz = x - cx, z - cz
            d = math.hypot(dx, dz) / (r * (0.85 + 0.3 * n))
            leeward = (dx * lee[0] + dz * lee[1]) > 0.3 * r
            if d <= 1.0:
                dep = int(round(depth * (1 - d * d)))
                for y in range(G - dep + 1, G + 1):
                    s.set(x, y, z, "air")
                fl = SHIP["scorch"] if d < 0.45 else ("minecraft:basalt" if d < 0.78 else LGP)
                s.set(x, G - dep, z, fl)
            elif d <= 1.18:
                s.set(x, G, z, LGP if n > 0.3 else "minecraft:tuff")
            elif d <= 1.5:
                rh = 2 if leeward else 1
                h = min(rh, int(round(rh * (1.5 - d) / 0.32 * (0.6 + 0.6 * n))))
                for y in range(G + 1, G + 1 + h):
                    s.set(x, y, z, SNOW)
                if s.is_air(x, G + 1 + h, z) and rng.random() < 0.7:
                    s.set(x, G + 1 + h, z, st.snow_layer(2 + int(n * 5)))
            elif d <= 1.9 and n > 0.62:
                s.set(x, G, z, rng.choice(["minecraft:tuff", "minecraft:basalt", "minecraft:polished_basalt[axis=y]", "minecraft:tuff"]))


def build_orbital():
    W, H, L, G = 38, 14, 38, 2
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=3)
    Y = G + 1
    scorch = SHIP["scorch"]

    # ---- craters (satellite, tank, heat shield, one small with a torn panel smoking in it)
    _scorch_crater(s, 17, 19, 5.5, G, 2, seed=11)
    _scorch_crater(s, 8, 8, 4.5, G, 2, seed=12)
    _scorch_crater(s, 30, 8, 3.5, G, 1, seed=13)
    _scorch_crater(s, 32, 32, 2.8, G, 1, seed=14)

    # ---- satellite body: pale white/quartz box, dark corner posts + top edge only, sunk one extra block
    bx1, by1, bz1, bx2, by2, bz2 = 14, G - 1, 17, 20, G + 3, 21
    sh.box(s, bx1, by1 - 1, bz1 + 1, bx2, by1 - 1, bz2 - 1, scorch)              # impact fill under the body
    sh.box(s, bx1, by1 - 1, bz1, bx2, by1 - 1, bz2, scorch)
    sh.hollow_box(s, bx1, by1, bz1, bx2, by2, bz2, SHIP["hull_light"], 1)
    for (x, z) in ((bx1, bz1), (bx1, bz2), (bx2, bz1), (bx2, bz2)):
        sh.box(s, x, by1, z, x, by2, z, FRAME)
    sh.box(s, bx1, by2, bz1, bx2, by2, bz1, FRAME); sh.box(s, bx1, by2, bz2, bx2, by2, bz2, FRAME)
    sh.box(s, bx1, by2, bz1, bx1, by2, bz2, FRAME); sh.box(s, bx2, by2, bz1, bx2, by2, bz2, FRAME)
    sh.box(s, bx1 + 1, by1, bz1, bx2 - 1, by1, bz1, LGC); sh.box(s, bx1 + 1, by1, bz2, bx2 - 1, by1, bz2, LGC)
    sh.box(s, bx1, by1, bz1 + 1, bx1, by1, bz2 - 1, LGC); sh.box(s, bx2, by1, bz1 + 1, bx2, by1, bz2 - 1, LGC)
    sh.box(s, bx1 + 1, by2, bz1 + 1, bx2 - 1, by2, bz2 - 1, LGC)                          # top plate
    for x in (bx1 + 2, bx2 - 2):                                                           # vents on the top plate
        s.set(x, by2 + 1, bz1 + 2, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(bx1 + 3, by2, bz1 + 3, SHIP["frame"]); s.set(bx1 + 1, by2, bz2 - 1, SHIP["frame"])
    # window strips on the east / west faces (mid height), wing root iron block replaces one cell
    for z in range(bz1 + 1, bz2):
        s.set(bx1, by1 + 2, z, SHIP["glass"]); s.set(bx2, by1 + 2, z, SHIP["glass"])
    s.set(bx1, by1 + 2, 19, SHIP["frame"]); s.set(bx2, by1 + 2, 19, SHIP["frame"])
    # thruster nozzle on the west end
    sh.cylinder(s, bx1 - 1, by1 + 3, 20, 0.8, -2, "minecraft:polished_blackstone", axis="x", r2=1.3)
    s.set(bx1 - 1, by1 + 3, 20, "minecraft:coal_block")
    # foil-wrapped north face (gold) with quartz clamps
    sh.box(s, bx1 + 1, by1 + 1, bz1, bx2 - 1, by2 - 1, bz1, "minecraft:gold_block")
    for x in range(bx1 + 1, bx2, 2):
        s.set(x, by1 + 2, bz1, "minecraft:quartz_block")
    s.set(17, by2, 19, "minecraft:observer[facing=up]")
    s.set(17, by2 + 1, 19, st.lightning_rod("up")); s.set(17, by2 + 2, 19, st.lightning_rod("up"))
    s.set(15, by2 + 1, 18, st.end_rod("up")); s.set(19, by2 + 1, 20, st.end_rod("up"))
    s.set(15, by2, 20, "minecraft:daylight_detector"); s.set(19, by2, 18, "minecraft:daylight_detector")
    s.set(16, by2, 18, SHIP["glass"]); s.set(18, by2, 20, "minecraft:tinted_glass")
    # breach: south face blown open (2 wide x 2 high) + scorch
    sh.box(s, 18, by1 + 1, bz2, 19, by1 + 2, bz2, "air")
    s.set(20, by1 + 1, bz2, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(18, by1 + 3, bz2, st.stairs(FRAME_STAIR, "north", "top")); s.set(19, by1 + 3, bz2, st.stairs(FRAME_STAIR, "north", "top"))
    s.set(18, by1, bz2 + 1, st.stairs("polished_blackstone_brick", "north")); s.set(19, by1, bz2 + 1, scorch)
    # interior: memory module bay, lit
    sh.box(s, bx1 + 1, by1 + 1, bz1 + 1, bx2 - 1, by2 - 1, bz2 - 1, "air")
    sh.box(s, bx1 + 1, by1, bz1 + 1, bx2 - 1, by1, bz2 - 1, SHIP["hull_dark"])
    s.set(15, by1 + 1, 18, "minecraft:observer[facing=south]"); s.set(15, by1 + 2, 18, "minecraft:observer[facing=south]")
    s.set(16, by1 + 1, 18, "minecraft:daylight_detector"); s.set(16, by1 + 2, 18, st.redstone_lamp(True))
    s.set(17, by2 - 1, 19, SHIP["light"])
    s.set(19, by1 + 1, 18, "minecraft:blast_furnace[facing=south,lit=false]")
    s.add_chest(18, by1 + 1, 18, "south", "minecraft:chests/end_city_treasure")
    s.set(15, by1 + 1, 20, SHIP["engine_glow"]); s.set(15, by1 + 2, 20, "minecraft:sea_lantern")
    s.add_sign(17, by1 + 2, 18, "minecraft:warped_wall_sign[facing=south]", ["SAT ORB-14", "module memoire", "rayonnement", "ne pas ouvrir"])
    s.set(16, by1 + 1, bz2 + 1, st.campfire(soul=True))                                     # smoke at the breach
    # wings: east intact (sagging to the snow), west snapped off
    wy = by1 + 3
    _wing(s, bx2 + 1, wy, 19, 10, "east", sag=True)
    s.set(bx2 + 1, wy, 19, "minecraft:iron_block")
    _wing(s, bx1 - 1, wy, 19, 3, "west", sag=False)
    s.set(bx1 - 4, wy, 19, st.chain("x")); s.set(bx1 - 5, wy, 19, st.chain("x")); s.set(bx1 - 5, wy - 1, 19, st.chain("y"))
    # the snapped wing fragment, tumbled, lying along z in the south-west
    for i in range(7):
        z = 25 + i
        for dx in range(-2, 3):
            x = 7 + dx
            if abs(dx) == 2:
                s.set(x, Y, z, "minecraft:iron_bars" if i % 4 != 2 else "minecraft:iron_block")
            elif i % 4 == 2:
                s.set(x, Y, z, "minecraft:iron_block")
            else:
                s.set(x, Y, z, "minecraft:blue_stained_glass" if i % 4 != 0 else "minecraft:light_blue_stained_glass")
    s.set(6, Y + 1, 27, "minecraft:blue_stained_glass"); s.set(8, Y + 1, 29, "minecraft:iron_bars")   # buckled cells
    for (x, z) in ((11, 23), (10, 25), (12, 24), (10, 24)):                                # shards along the tumble path
        s.set(x, Y, z, "minecraft:blue_stained_glass" if (x + z) % 2 else "minecraft:light_blue_stained_glass")
    s.set(11, Y, 24, "minecraft:iron_bars")

    # ---- fuel tank sphere, cracked open, blue smoke inside (only the buried underside is scorched)
    tcx, tcy, tcz = 8, G + 2, 8
    sh.sphere(s, tcx, tcy, tcz, 3.6, SHIP["frame"], hollow=True, thickness=1.2)
    sh.torus(s, tcx, tcy, tcz, 3.6, 0.6, FRAME, axis="y")                                  # equator band
    sh.torus(s, tcx, tcy + 2, tcz, 2.9, 0.4, "minecraft:polished_basalt[axis=y]", axis="y")
    sh.sphere(s, tcx + 2.5, tcy + 2, tcz + 2.5, 2.4, "air")                                 # the crack
    for y in range(0, G + 1):
        sh.replace_in_region(s, tcx - 5, y, tcz - 5, tcx + 5, y, tcz + 5, SHIP["frame"], "minecraft:polished_basalt[axis=y]")
    s.set(tcx + 1, tcy - 2, tcz + 1, st.campfire(soul=True))
    s.set(tcx, tcy - 2, tcz, SHIP["engine_glow"]); s.set(tcx - 1, tcy - 2, tcz - 1, SHIP["light"])
    s.set(tcx, tcy + 4, tcz, st.lightning_rod("up"))                                        # valve on top
    s.set(tcx - 4, tcy, tcz, st.trapdoor("iron", "east", "bottom", open=True))              # a torn hatch
    _chunk(s, 12, 13, 2)

    # ---- heat shield disc: black only in the centre, ablation gradient to the rim, propped up on the east
    hx, hz = 30, 8
    rng = random.Random(7)
    for x in range(hx - 6, hx + 7):
        for z in range(hz - 6, hz + 7):
            dd = math.hypot(x - hx, z - hz)
            if dd > 5.3:
                continue
            raised = x > hx
            s.set(x, Y, z, "minecraft:polished_blackstone" if dd > 4.4 else scorch)
            if dd <= 1.8:
                mat = rng.choice(["minecraft:coal_block", scorch, scorch])
            elif dd <= 3.3:
                mat = rng.choice(["minecraft:basalt", "minecraft:polished_basalt[axis=y]", "minecraft:blackstone"])
            elif dd <= 4.4:
                mat = rng.choice(["minecraft:polished_basalt[axis=y]", LGC, LGC, "minecraft:tuff"])
            else:
                mat = "minecraft:polished_blackstone"
            s.set(x, Y + 1 if raised else Y, z, mat)
    sh.ring_stairs(s, hx, Y + 1, hz, 5.4, "polished_blackstone_brick", half="bottom", outward=False)
    for z in range(hz - 3, hz + 4):
        s.set(hx, Y + 1, z, st.stairs("polished_blackstone_brick", "west", "bottom"))
    sh.replace_in_region(s, hx - 6, Y + 1, hz - 6, hx - 1, Y + 1, hz + 6, "minecraft:polished_blackstone_brick_stairs[facing=west,half=bottom,shape=straight]", "air")
    s.set(hx + 2, Y + 2, hz, st.campfire(soul=True))
    _chunk(s, hx - 4, hz + 2, 0)

    # ---- small crater with a torn panel smoking in it
    _panel(s, 30, G, 33, "east")
    s.set(32, G, 31, st.campfire(soul=True))

    # ---- bent antenna mast
    ax, az = 22, 32
    sh.box(s, ax - 1, Y, az - 1, ax + 1, Y, az + 1, SHIP["hull_dark"])
    s.set(ax, Y, az, SHIP["frame"])
    for y in range(Y + 1, Y + 4):
        s.set(ax, y, az, "minecraft:iron_bars")
    s.set(ax, Y + 4, az, st.chain("y"))
    s.set(ax, Y + 5, az, st.chain("x")); s.set(ax + 1, Y + 5, az, st.chain("x")); s.set(ax + 2, Y + 5, az, st.chain("x"))
    s.set(ax + 3, Y + 5, az, st.lightning_rod("east")); s.set(ax + 3, Y + 4, az, st.lightning_rod("down"))
    s.set(ax + 1, Y + 6, az, st.lightning_rod("up"))
    s.set(ax - 1, Y + 1, az + 1, "minecraft:observer[facing=up]")
    # snapped-off dish antenna lying on the snow (3x3 iron trapdoor plate + feed horn), south of the body
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            s.set(14 + dx, Y, 30 + dz, st.trapdoor("iron", "north", "bottom", open=False) if (dx or dz) else SHIP["frame"])
    s.set(14, Y + 1, 30, st.lightning_rod("up")); s.set(15, Y, 28, st.chain("y")); s.set(15, Y, 27, st.chain("z"))

    # ---- hull sheets (big pale pieces) + small panels + directional debris trail east / south-east of the body
    _sheet(s, 24, Y, 26, "east")
    _sheet(s, 3, Y, 15, "south")
    _panel(s, 12, Y, 3, "east")
    _panel(s, 33, Y, 22, "north")
    for (x, z, k) in ((23, 24, 0), (27, 22, 1), (31, 25, 3), (34, 27, 2), (29, 30, 0), (33, 15, 1),
                      (10, 21, 3), (5, 23, 0), (19, 27, 1), (21, 5, 3), (17, 9, 0), (4, 30, 2)):
        _chunk(s, x, z, k)
    sh.texturize(s, scorch, MIX_SCORCH, seed=4)
    sh.texturize(s, SHIP["hull_light"], MIX_WHITE, seed=5)
    sh.snow_cover(s, y_min=Y, prob=0.3, seed=6, layers=(1, 2),
                  skip=["glass", "iron", "gold", "quartz", "lamp", "observer", "detector", "blackstone", "basalt", "coal", "calcite"])
    return s.cropped(pad=1)


def build():
    return {"cargo_containers": build_cargo(), "orbital_debris": build_orbital()}

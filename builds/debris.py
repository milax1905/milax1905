"""Debris sites: a spilled cargo drop (shipping containers under a parachute) and a field of fallen orbital debris
(satellite bus with dish and solar wings, cracked fuel sphere, tilted heat shield, hull panels along one trail).
Both sit on a thin snow slab (ground=2)."""
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
IRON = "minecraft:iron_block"
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


def _on(s, x, z, block, dy=0):
    """Put a block on top of the terrain at (x, z) (snow layers are removed first). Returns the y used."""
    y = s.top_y(x, z) + 1
    if "snow[" in s.get(x, y - 1, z):
        s.set(x, y - 1, z, "air"); y -= 1
    s.set(x, y + dy, z, block)
    return y + dy


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


def roof_detail(s, P, length, width, height, seed=0, hatch=True, rib=True, rust=1, snow_prob=0.3):
    """Roof furniture: a polished-deepslate rib across the middle, iron-trapdoor hatches, rust patches and a few
    deliberate 2-3 layer snow patches on the leeward (east) half only - the windward half is wind-scoured so the
    roof colour and the rib stay readable."""
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
            if x <= x_mid or not s.is_air(x, y + 1, z) or "trapdoor" in s.get(x, y, z):
                continue
            if rng.random() < snow_prob:
                s.set(x, y + 1, z, st.snow_layer(rng.randint(2, 3)))


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
    """Deflated parachute canopy: a LOW white / light-gray wool mound (max 2 blocks of wool + a carpet), gores
    alternating, the outer two rings carpet only (soft edge), one cyan seam as the only accent, and a carpet
    fringe just outside the rim. Returns the apex (x, y, z)."""
    rng = random.Random(seed)
    Y = y_surface + 1
    soft = 1.0 - 2.0 / min(rx, rz)                              # outer two rings -> carpet only

    def gore(dx, dz):
        return int((math.atan2(dz, dx) + math.pi) / (2 * math.pi / gores)) % gores

    def fabric(g):
        return "white" if g % 2 == 0 else "light_gray"

    for x in range(s.w):
        for z in range(s.l):
            dx, dz = x - cx, z - cz
            r2 = (dx / rx) ** 2 + (dz / rz) ** 2
            if r2 > 1.0:
                continue
            fab = fabric(gore(dx, dz))
            h = ry * math.sqrt(max(0.0, 1.0 - r2)) * (0.9 + 0.2 * sh.value_noise2(x, z, seed, 4.0))
            n = 0 if r2 > soft * soft else min(2, int(h))
            for k in range(n):
                s.set(x, Y + k, z, f"minecraft:{fab}_wool")
            if n == 0 or (n < 2 and h - n > 0.45):
                s.set(x, Y + n, z, f"minecraft:{fab}_carpet")
    # fringe ring (carpet of the gore colour) just outside the rim
    for x in range(s.w):
        for z in range(s.l):
            dx, dz = x - cx, z - cz
            r2 = (dx / (rx + 1.2)) ** 2 + (dz / (rz + 1.2)) ** 2
            if r2 <= 1.0 and s.is_air(x, Y, z) and rng.random() < 0.7:
                s.set(x, Y, z, f"minecraft:{fabric(gore(dx, dz))}_carpet")
    # one cyan seam stripe along a gore boundary (the only accent)
    a = -math.pi + 2 * 2 * math.pi / gores
    for t in range(0, int(max(rx, rz)) + 1):
        x, z = round(cx + t * rx / max(rx, rz) * math.cos(a)), round(cz + t * rz / max(rx, rz) * math.sin(a))
        ty = s.top_y(x, z)
        b = s.get(x, ty, z)
        if ty >= Y and "wool" in b:
            s.set(x, ty, z, "minecraft:cyan_wool")
        elif ty >= Y and "carpet" in b:
            s.set(x, ty, z, "minecraft:cyan_carpet")
    return (round(cx), s.top_y(round(cx), round(cz)), round(cz))


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

    # ---- parachute: snagged on the top corner of the stack, a narrow drape down the east face, then the
    #      deflated canopy lying 1-2 blocks of snow further south-east, held by taut chain risers
    top_y = G + 7
    for z in (14, 15):                                                     # fabric over the roof corner
        s.set(18, top_y + 1, z, "minecraft:white_carpet")
    knot = (19, top_y + 1, 15)
    s.set(*knot, "minecraft:light_gray_wool")                              # riser knot
    curtain = [(19, top_y - 2, top_y), (20, top_y - 5, top_y - 2), (21, Y, Y + 1)]
    for x, y1, y2 in curtain:
        for z in range(12, 17):
            fab = "light_gray" if z == 14 else "white"
            for y in range(y1, y2 + 1):
                s.set(x, y, z, f"minecraft:{fab}_wool")
    s.set(21, Y + 2, 14, "minecraft:light_gray_carpet"); s.set(21, Y + 2, 12, "minecraft:white_carpet")
    for z in (12, 13, 15):
        s.set(22, Y, z, "minecraft:white_carpet")
    s.set(22, Y, 14, "minecraft:light_gray_carpet")
    apex = _canopy(s, 26.5, 21, 5.0, 2.6, 5.0, G, gores=6, seed=4)
    # risers: the shroud lines gather in a second knot at the foot of the drape and run almost flat to the
    # canopy edge (straight chain runs along x, one step at most) - taut, still attached
    knot2 = (21, Y + 2, 15)
    s.set(*knot2, "minecraft:light_gray_wool")
    for (rx_, rz_) in ((25, 16), (30, 17), (29, 18), (32, 15)):
        ty = s.top_y(rx_, rz_)
        _chain_line(s, (knot2[0] + 1, knot2[1], knot2[2]), (rx_, ty + 1, rz_))
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
    s.set(4, Y, 25, _barrel("east"))

    # ---- purple container (north-east), BURST open on its west side toward the stack, cargo spilled in a mound
    P4 = container(s, 22, Y, 4, 8, 4, 4, "z", "purple", door_end=1, doors="closed")
    for a in range(1, 5):                                                   # 4 wide x 2 high hole in the west wall
        for y in (1, 2):
            s.set(*P4(a, 0, y), "air")
    s.set(*P4(2, 0, 2), st.trapdoor("iron", "east", "top", open=True))        # one bent sheet still hanging
    s.set(*P4(2, 0, 3), st.slab("polished_deepslate", "top"))                   # roof edge sagging into the hole
    s.set(*P4(3, 0, 3), st.slab("polished_deepslate", "top"))
    s.set(*P4(1, -1, 3), st.stairs(FRAME_STAIR, "west", "top"))                # peeled sheet metal, bent outward
    s.set(*P4(4, -1, 3), st.stairs(FRAME_STAIR, "west", "top"))
    s.set(*P4(0, -1, 1), st.stairs(FRAME_STAIR, "west", "bottom"))
    s.set(*P4(1, 1, 1), st.lantern(hanging=False))
    s.set(*P4(6, 1, 1), BARREL_UP); s.set(*P4(6, 2, 1), SHIP["container"])
    s.set(*P4(3, 1, 1), _barrel("west")); s.set(*P4(4, 1, 1), BARREL_UP); s.set(*P4(5, 2, 1), BARREL_UP)
    s.add_sign(*P4(7, 4, 2), "minecraft:warped_wall_sign[facing=south]", ["CX-04", "FRAGILE", "labo Nord", ""])
    roof_detail(s, P4, 8, 4, 4, seed=3, rust=1)
    # the mound: 3 high against the hole (x=21), spreading west, pallet boards around it
    mound = {(21, Y, 5): BARREL_UP, (21, Y, 6): BARREL_UP, (21, Y, 7): _barrel("west"), (21, Y, 8): BARREL_UP,
             (21, Y, 9): st.slab("spruce"), (20, Y, 5): _barrel("north"), (20, Y, 6): BARREL_UP, (20, Y, 7): BARREL_UP,
             (20, Y, 8): SHIP["container"], (19, Y, 6): _barrel("east"), (19, Y, 7): st.slab("spruce"),
             (19, Y, 8): "minecraft:purple_concrete_powder", (20, Y, 9): st.trapdoor("spruce", "north", "bottom", open=False),
             (21, Y + 1, 6): BARREL_UP, (21, Y + 1, 7): SHIP["container"], (21, Y + 1, 8): st.slab("spruce"),
             (20, Y + 1, 6): "minecraft:light_gray_shulker_box", (20, Y + 1, 7): _barrel("west"),
             (21, Y + 2, 6): BARREL_UP, (21, Y + 2, 7): st.snow_layer(2), (20, Y + 2, 6): st.snow_layer(2),
             (19, Y + 1, 6): st.snow_layer(1), (21, Y + 1, 5): st.snow_layer(2), (18, Y, 7): st.slab("spruce")}
    for (x, y, z), b in mound.items():
        s.set(x, y, z, b)
    s.set(17, Y, 9, _barrel("east")); s.set(15, Y, 10, _barrel("west"))           # two barrels rolled away
    s.set(18, Y, 4, st.slab("spruce"))                                            # a broken crate: 3 sides left
    s.set(18, Y, 3, st.trapdoor("spruce", "north", "bottom", open=True))
    s.set(17, Y, 4, st.trapdoor("spruce", "west", "bottom", open=True))
    s.set(19, Y, 4, st.trapdoor("spruce", "east", "bottom", open=True))

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
    sh.snow_cover(s, 9, 19, 16, 22, y_min=Y + 2, prob=0.95, seed=7, layers=(2, 4))     # the only fully snowed roof
    # ---- tipped light_gray small container (north), plowed into the snow, door hanging up
    P5 = container(s, 11, G, 5, 5, 3, 3, "x", "light_gray", door_end=-1, doors="none", tipped=True)
    s.set(*P5(-1, 1, 2), st.trapdoor("iron", "east", "top", open=False))
    s.set(*P5(-1, 1, 1), "air")
    s.set(*P5(2, 1, 2), st.trapdoor("iron", "north", "bottom", open=False))
    for (dx, dz) in ((-2, 0), (-2, 1), (-2, 2), (-3, 1), (-1, -1), (-1, 3), (5, 0), (5, 1)):   # snow plowed up: piles
        s.set(11 + dx, Y, 5 + dz, st.snow_layer(rng.randint(5, 7)))
    for (dx, dz) in ((-3, 0), (-3, 2), (-4, 1), (-2, -1), (-2, 3), (6, 0), (6, 1), (-1, 4), (0, 3), (1, 3)):
        if s.is_air(11 + dx, Y, 5 + dz):
            s.set(11 + dx, Y, 5 + dz, st.snow_layer(rng.randint(2, 3)))
    # ---- small cyan + small white stacked and skewed 90 degrees (south)
    P7 = container(s, 8, Y, 26, 5, 3, 3, "x", "cyan", doors="closed")
    P8 = container(s, 9, Y + 3, 25, 5, 3, 3, "z", "white", doors="closed")
    s.set(*P8(2, 1, 1), BARREL_UP)
    roof_detail(s, P8, 5, 3, 3, seed=5, rib=True, hatch=False)
    s.set(*P7(1, 0, 2), LGP)

    # ---- debris and weathering
    pallets = [(19, 11, st.slab("spruce")), (7, 20, st.trapdoor("iron", "north", "bottom", open=False)),
               (17, 21, st.slab("spruce")), (13, 24, st.slab("polished_deepslate")), (25, 12, st.slab("spruce"))]
    for x, z, b in pallets:
        if s.is_air(x, Y, z):
            s.set(x, Y, z, b)
    _drift(s, 26, Y, 6, 1, 0, 3, seed=3); _drift(s, 16, Y, 6, 1, 0, 3, seed=2)      # leeward drifts (east side)
    _drift(s, 17, Y, 21, 1, 0, 3, seed=4); _drift(s, 13, Y, 27, 1, 0, 2, seed=5)
    _drift(s, 6, Y, 17, 1, 0, 2, seed=6)
    sh.snow_cover(s, y_min=Y, prob=0.22, seed=5, layers=(1, 2),
                  skip=["wool", "carpet", "glass", "iron", "purple", "lantern", "barrel", "shulker", "planks", "table",
                        "bed", "log", "white_concrete", "sea_lantern", "powder", "concrete", "polished_deepslate"])
    # a 2-block snow margin all round so nothing sits on the schematic border
    out = Schematic(W + 4, H, L + 4, ground=G)
    sh.ground_slab(out, G, SNOW, depth=3)
    out.paste(s, 2, 0, 2, skip_air=False)
    sh.snow_cover(out, y_min=G, prob=0.12, seed=15, layers=(1, 2), skip=["wool", "carpet", "glass", "iron", "purple",
                  "lantern", "barrel", "shulker", "planks", "table", "bed", "log", "sea_lantern", "concrete", "packed_ice"])
    return out.cropped(pad=1)


# ------------------------------------------------------------------------------------------ orbital debris
def _panel(s, x, y, z, dir, mat="smooth_quartz", core="minecraft:white_concrete"):
    """A small hull panel resting at an angle: slab -> stairs -> raised block -> top stair, on a dark anchor
    (polished deepslate under the lifted end, a basalt scorch mark beside it)."""
    dx, dz = _DV[dir]
    back = _OPP[dir]
    s.set(x, y, z, st.slab(mat))
    s.set(x + dx, y, z + dz, st.stairs(mat, dir))
    s.set(x + 2 * dx, y, z + 2 * dz, core)
    s.set(x + 2 * dx, y + 1, z + 2 * dz, st.stairs(mat, back, "top"))
    s.set(x + 3 * dx, y + 1, z + 3 * dz, st.slab(mat))
    s.set(x + 3 * dx, y, z + 3 * dz, FRAME)
    s.set(x + dx - dz, y - 1, z + dz + dx, "minecraft:basalt")
    s.set(x + 2 * dx + dz, y, z + 2 * dz - dx, st.slab("polished_deepslate"))


def _sheet(s, x0, y, z0, dir, seed=0):
    """A big torn hull sheet, 5 long x 4 wide: a pale quartz plate lying on the snow (full blocks at the buried
    end, half-covered by snow layers) that lifts gently at the other end (top slab -> one block up), propped on
    polished-deepslate chunks, with one dark polished-deepslate rib edge and a torn-off corner."""
    rng = random.Random(seed)
    dx, dz = _DV[dir]
    wx, wz = (-dz, dx)                                        # width direction
    prof = [(0, "full"), (0, "full"), (0, "top"), (1, "bottom"), (1, "bottom")]
    for w in range(4):
        dark = (w == 3)
        mat = "polished_deepslate" if dark else ("quartz" if w % 2 == 0 else "smooth_quartz")
        for i, (dy, typ) in enumerate(prof):
            if i == 0 and w == 0:
                continue                                      # torn corner
            x, z = x0 + dx * i + wx * w, z0 + dz * i + wz * w
            if typ == "full":
                s.set(x, y + dy, z, FRAME if dark else ("minecraft:quartz_block" if w % 2 == 0 else "minecraft:smooth_quartz"))
                if rng.random() < 0.7:
                    s.set(x, y + dy + 1, z, st.snow_layer(rng.randint(1, 2)))     # half buried
            else:
                s.set(x, y + dy, z, st.slab(mat, typ))
    for w in (0, 3):                                          # props under the lifted end
        s.set(x0 + dx * 4 + wx * w, y, z0 + dz * 4 + wz * w, FRAME)
    s.set(x0 + dx * 3 + wx * 1, y, z0 + dz * 3 + wz * 1, "minecraft:cobbled_deepslate")
    s.set(x0 + dx * 3 + wx * 2, y, z0 + dz * 3 + wz * 2, st.slab("polished_deepslate"))
    s.set(x0 + dx * 1 + wx * 1, y + 1, z0 + dz * 1 + wz * 1, st.trapdoor("iron", _OPP[dir], "bottom", open=False))
    s.set(x0 + wx * 0, y, z0 + wz * 0, st.trapdoor("iron", dir, "bottom", open=True))       # torn flap
    for w in range(-1, 5):                                    # scorch under the buried edge
        s.set(x0 - dx + wx * w, y - 1, z0 - dz + wz * w, "minecraft:basalt" if w % 2 else "minecraft:tuff")


def _chunk(s, x, z, kind, seed=0):
    """2-4 block mini-cluster of wreckage on the snow, always with a dark anchor (deepslate / basalt scorch)."""
    y = _on(s, x, z, "air")
    s.set(x, y - 1, z, "minecraft:basalt")                    # scorch mark on the snow under every chunk
    if kind == 0:
        s.set(x, y, z, st.slab("polished_deepslate")); s.set(x + 1, y, z, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(x, y, z + 1, "minecraft:cobbled_deepslate")
    elif kind == 1:
        s.set(x, y, z, st.stairs("quartz", "east")); s.set(x + 1, y, z, "minecraft:white_concrete")
        s.set(x + 1, y, z + 1, st.slab("polished_deepslate")); s.set(x + 1, y + 1, z, st.slab("quartz"))
        s.set(x + 1, y - 1, z, "minecraft:blackstone")
    elif kind == 2:
        s.set(x, y, z, IRON); s.set(x - 1, y, z, st.slab("smooth_quartz"))
        s.set(x, y, z - 1, st.trapdoor("iron", "north", "bottom", open=False)); s.set(x, y + 1, z, st.snow_layer(2))
        s.set(x - 1, y - 1, z, "minecraft:tuff")
    else:
        s.set(x, y, z, "minecraft:cobbled_deepslate"); s.set(x + 1, y, z, st.stairs("polished_blackstone_brick", "west"))
        s.set(x, y, z - 1, st.slab("smooth_quartz")); s.set(x, y + 1, z, st.trapdoor("iron", "east", "bottom", open=True))


def _wing(s, x0, y0, z0, length, dir, bends=None, ribs=()):
    """Solar panel wing, 5 wide: a stripped-spruce spar down the middle, blue / light-blue glass cells either
    side, iron-bar rails on both edges, iron ribs across. `bends` = {index: +1 / -1} folds the wing up / down by
    one block at that index (the fold column is 2 blocks thick so the plate stays face-connected)."""
    bends = bends or {}
    dx, dz = _DV[dir]
    wx, wz = (-dz, dx)
    spar = st.log("minecraft:stripped_spruce_log", "x" if dx else "z")
    y = y0
    for i in range(length):
        x, z = x0 + dx * i, z0 + dz * i
        b = bends.get(i, 0)
        y += b
        rib = i in ribs or i == 0 or b != 0
        for w in range(-2, 3):
            px, pz = x + wx * w, z + wz * w
            if rib:
                blk = IRON
            elif abs(w) == 2:
                blk = "minecraft:iron_bars"
            elif w == 0:
                blk = spar
            else:
                blk = "minecraft:blue_stained_glass" if (i % 3) else "minecraft:light_blue_stained_glass"
            s.set(px, y, pz, blk)
            if b:
                s.set(px, y - b, pz, blk)
            for k in (1, 2):                                   # nothing piled on the wing
                if s.get(px, y + k, pz) == SNOW or "snow[" in s.get(px, y + k, pz):
                    s.set(px, y + k, pz, "air")
    return y


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
            elif d <= 1.4:
                rh = 2 if leeward else 1
                h = min(rh, int(round(rh * (1.4 - d) / 0.3 * (0.5 + 0.6 * n))))
                for y in range(G + 1, G + 1 + h):
                    s.set(x, y, z, SNOW)
                if s.is_air(x, G + 1 + h, z) and rng.random() < 0.7:
                    s.set(x, G + 1 + h, z, st.snow_layer(2 + int(n * 5)))
            elif d <= 1.9 and n > 0.62:
                s.set(x, G, z, rng.choice(["minecraft:tuff", "minecraft:basalt", "minecraft:polished_basalt[axis=y]", "minecraft:tuff"]))


def _heat_shield(s, hx, hz, r, y_base, Y):
    """Ablative heat-shield disc propped at ~27 degrees: the west edge lies in the crater, the plate (one block
    thick, stairs at each step so the top reads as a ramp) rises one block every two columns to the east and
    stands ~5 above the snow on polished-deepslate props. Gradient: black centre -> basalt -> pale ablated
    tuff / light gray ring, with a 1-wide dark polished-blackstone rim; the north-east quarter of the rim is gone."""
    rng = random.Random(7)
    x_lo = int(math.floor(hx - r))
    for x in range(int(hx - r) - 1, int(hx + r) + 2):
        for z in range(int(hz - r) - 1, int(hz + r) + 2):
            dd = math.hypot(x - hx, z - hz)
            if dd > r:
                continue
            rim = dd > r - 1.0
            if rim and (x - hx) > 0.25 * r and (hz - z) > 0.25 * r:
                continue                                      # broken north-east quarter of the rim
            if dd <= 1.8:
                mat, smat = rng.choice(["minecraft:coal_block", SHIP["scorch"], SHIP["scorch"]]), "blackstone"
            elif dd <= 3.2:
                mat, smat = rng.choice(["minecraft:basalt", "minecraft:polished_basalt[axis=y]", "minecraft:blackstone"]), "blackstone"
            elif not rim:
                mat, smat = rng.choice(["minecraft:tuff", LGC, "minecraft:tuff", "minecraft:polished_basalt[axis=y]"]), "polished_andesite"
            else:
                mat, smat = "minecraft:polished_blackstone", "polished_blackstone"
            k = x - x_lo
            h = y_base + k // 2
            if k % 2 == 0 and k > 0:                          # step column: a stair so the top reads as a ramp
                s.set(x, h, z, st.stairs(smat, "east", "bottom"))
            else:
                s.set(x, h, z, mat)
    top_x = int(hx + r)
    h_top = y_base + (top_x - x_lo) // 2
    for z in (int(hz) - 2, int(hz) + 2):                      # props under the raised edge
        for y in range(Y, h_top - 1):
            s.set(top_x - 1, y, z, FRAME)
    s.set(top_x - 3, Y, int(hz), "minecraft:cobbled_deepslate"); s.set(top_x - 3, Y + 1, int(hz), "minecraft:cobbled_deepslate")
    s.set(top_x - 1, Y, int(hz), st.campfire(soul=True))       # the hottest piece, still smoking under the plate
    # rim pieces knocked off, lying 3-4 blocks past the broken quarter
    for (px, pz, f) in ((int(hx + r) + 1, int(hz - r) + 2, "south"), (int(hx + r) - 1, int(hz - r) - 2, "west"),
                        (int(hx + r) + 2, int(hz - r), "east")):
        if s.inside(px, Y, pz):
            _on(s, px, pz, st.stairs("polished_blackstone", f))


def build_orbital():
    W, H, L, G = 46, 17, 44, 2
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=3)
    Y = G + 1
    scorch = SHIP["scorch"]
    rng = random.Random(21)

    # ---- craters: satellite (centre), fuel sphere (north-west), heat shield (south-east) + 3 small ones
    #      everything lies on ONE trail running north-west -> south-east, densest around the satellite
    _scorch_crater(s, 19, 20, 7.0, G, 2, seed=11)
    _scorch_crater(s, 9, 9, 4.5, G, 2, seed=12)
    _scorch_crater(s, 33, 34, 5.0, G, 2, seed=13)
    _scorch_crater(s, 27, 27, 2.5, G, 1, seed=14)
    _scorch_crater(s, 40, 21, 3.0, G, 1, seed=15)
    _scorch_crater(s, 23, 33, 2.5, G, 1, seed=16)

    # ---- satellite bus (hero): 7 x 5 x 5 white / quartz box, dark edge ribs + mid rib, sunk in its crater
    bx1, by1, bz1, bx2, by2, bz2 = 16, G - 1, 18, 22, G + 3, 22
    sh.box(s, bx1, 0, bz1, bx2, 0, bz2, scorch)                                          # impact fill under the body
    sh.hollow_box(s, bx1, by1, bz1, bx2, by2, bz2, SHIP["hull_light"], 1)
    for (x, z) in ((bx1, bz1), (bx1, bz2), (bx2, bz1), (bx2, bz2), (19, bz1), (19, bz2)):     # corner posts + mid rib
        sh.box(s, x, by1, z, x, by2, z, FRAME)
    for yy in (by1, by2):
        sh.box(s, bx1, yy, bz1, bx2, yy, bz1, FRAME); sh.box(s, bx1, yy, bz2, bx2, yy, bz2, FRAME)
        sh.box(s, bx1, yy, bz1, bx1, yy, bz2, FRAME); sh.box(s, bx2, yy, bz1, bx2, yy, bz2, FRAME)
    sh.box(s, bx1 + 1, by2, bz1 + 1, bx2 - 1, by2, bz2 - 1, LGC)                          # top plate
    sh.box(s, 19, by2, bz1, 19, by2, bz2, FRAME)
    # south face (camera side): window strips + iron service panel + the breach
    for x in (17, 18):
        s.set(x, by1 + 2, bz2, SHIP["glass"])
    s.set(17, by1 + 1, bz2, IRON); s.set(18, by1 + 1, bz2, st.trapdoor("iron", "north", "bottom", open=True))
    sh.box(s, 20, by1 + 1, bz2, 21, by1 + 2, bz2, "air")                                 # breach 2 x 2
    s.set(20, by1 + 3, bz2, st.stairs(FRAME_STAIR, "north", "top")); s.set(21, by1 + 3, bz2, st.stairs(FRAME_STAIR, "north", "top"))
    s.set(21, by1 + 1, bz2 + 1, st.trapdoor("iron", "south", "bottom", open=True))       # torn plate hanging out
    _on(s, 20, bz2 + 1, st.campfire(soul=True))                                         # smoke at the breach
    # north face: 3 blocks of gold MLI foil + quartz clamps + vents; east face vents; west end thruster nozzle
    for x in (17, 18, 19):
        s.set(x, by1 + 2, bz1, "minecraft:gold_block")
    s.set(17, by1 + 1, bz1, "minecraft:quartz_block"); s.set(21, by1 + 2, bz1, "minecraft:quartz_block")
    for x in (18, 20):
        s.set(x, by1 + 1, bz1 - 1, st.trapdoor("iron", "north", "bottom", open=True))
    for z in (19, 20, 21):
        s.set(bx2 + 1, by1 + 2, z, st.trapdoor("iron", "east", "bottom", open=True))
    for (yy, z) in ((by1 + 1, 20), (by1 + 3, 20), (by1 + 2, 19), (by1 + 2, 21), (by1 + 2, 20)):
        s.set(bx1 - 1, yy, z, "minecraft:polished_blackstone")
    s.set(bx1 - 2, by1 + 2, 20, "minecraft:coal_block")
    # interior: memory module bay, lit
    sh.box(s, bx1 + 1, by1 + 1, bz1 + 1, bx2 - 1, by2 - 1, bz2 - 1, "air")
    sh.box(s, bx1 + 1, by1, bz1 + 1, bx2 - 1, by1, bz2 - 1, SHIP["hull_dark"])
    s.set(17, by1 + 1, 19, "minecraft:daylight_detector"); s.set(17, by1 + 2, 19, st.redstone_lamp(True))
    s.set(17, by1 + 1, 21, "minecraft:observer[facing=east]"); s.set(17, by1 + 2, 21, "minecraft:observer[facing=east]")
    s.set(19, by1 + 1, 20, SHIP["engine_glow"]); s.set(19, by1 + 2, 20, SHIP["light"])
    s.set(19, by1, 19, SHIP["light"]); s.set(19, by1, 21, SHIP["light"])
    s.add_chest(21, by1 + 1, 19, "south", "minecraft:chests/end_city_treasure")
    s.set(21, by1 + 1, 21, "minecraft:blast_furnace[facing=west,lit=false]")
    s.add_sign(18, by1 + 2, 19, "minecraft:warped_wall_sign[facing=south]", ["SAT ORB-14", "module memoire", "rayonnement", "ne pas ouvrir"])

    # ---- dish antenna (r 4) on top of the bus: dark stair rim, quartz slab bowl, iron hub, feed horn
    dy = by2 + 1
    sh.ring_stairs(s, 19, dy, 20, 4.0, FRAME_STAIR, half="bottom", outward=True)
    for x in range(14, 25):
        for z in range(15, 26):
            d = math.hypot(x - 19, z - 20)
            if d < 3.5:
                s.set(x, dy, z, IRON if d <= 1.2 else st.slab("quartz" if int(d) % 2 else "smooth_quartz"))
    for (x, z) in ((22, 17), (23, 18), (21, 16)):                                        # torn rim (north-east)
        s.set(x, dy, z, "air")
    s.set(19, dy + 1, 20, "minecraft:iron_bars"); s.set(19, dy + 2, 20, "minecraft:iron_bars")
    s.set(19, dy + 3, 20, st.end_rod("up"))
    _on(s, 26, 15, st.stairs(FRAME_STAIR, "south")); _on(s, 28, 13, st.stairs(FRAME_STAIR, "west"))   # rim pieces

    # ---- solar wings: east one intact, sagging in 2 folds down to the snow; west one snapped at the root
    _wing(s, bx2 + 1, by2, 20, 12, "east", bends={6: -1, 9: -1}, ribs=(3,))
    _wing(s, bx1 - 1, by2, 20, 3, "west")
    for z in (18, 22):
        s.set(bx1 - 4, by2, z, "minecraft:iron_bars")                                    # torn rails
    s.set(bx1 - 4, by2, 20, st.chain("x")); s.set(bx1 - 4, by2 - 1, 20, st.chain("y")); s.set(bx1 - 4, by2 - 2, 20, st.chain("y"))
    # the snapped wing, tumbled 4-6 blocks south-west, lying along z and bent up in two steps
    _wing(s, 6, Y, 24, 9, "south", bends={5: 1, 7: 1}, ribs=(2,))
    for (x, z) in ((6, 32), (8, 32), (4, 32)):                                           # chunks it came to rest on
        s.set(x, Y, z, FRAME); s.set(x, Y + 1, z, FRAME)
    s.set(5, Y, 33, "minecraft:cobbled_deepslate")
    for (x, z, b) in ((10, 23, "minecraft:blue_stained_glass"), (11, 22, "minecraft:light_blue_stained_glass"),
                      (9, 23, "minecraft:iron_bars"), (10, 24, "minecraft:iron_bars"), (12, 23, st.slab("polished_deepslate"))):
        _on(s, x, z, b)                                                                  # shards along the tumble path

    # ---- fuel tank sphere (north-west), iron, sunk in its crater, a quarter wedge torn open toward the satellite
    tcx, tcy, tcz = 9, G + 1, 9
    sh.sphere(s, tcx, tcy, tcz, 3.0, IRON, hollow=True, thickness=1.2)
    sh.torus(s, tcx, tcy, tcz, 3.0, 0.5, FRAME, axis="y")                                 # equator band
    cut = set()
    for x in range(tcx + 1, tcx + 5):
        for y in range(tcy, tcy + 5):
            for z in range(tcz + 1, tcz + 5):
                if not s.is_air(x, y, z) and "snow" not in s.get(x, y, z):
                    cut.add((x, y, z)); s.set(x, y, z, "air")
    for (x, y, z) in sorted(cut):                                                          # torn metal along the crack
        for (nx, ny, nz, f) in ((x - 1, y, z, "east"), (x, y, z - 1, "south"), (x, y - 1, z, "up")):
            b = s.get(nx, ny, nz)
            if b == IRON and (nx, ny, nz) not in cut:
                r = rng.random()
                if r < 0.35:
                    s.set(nx, ny, nz, st.stairs(FRAME_STAIR, f if f != "up" else "east", "top" if f == "up" else "bottom"))
                elif r < 0.6 and f != "up":
                    s.set(nx, ny, nz, st.trapdoor("iron", f, "bottom", open=True))
    s.set(tcx, tcy - 2, tcz, st.campfire(soul=True))                                      # blue smoke inside
    s.set(tcx - 1, tcy - 2, tcz - 1, SHIP["light"]); s.set(tcx - 1, tcy - 1, tcz - 1, SHIP["engine_glow"])
    s.set(tcx, tcy + 4, tcz, "minecraft:iron_bars"); s.set(tcx, tcy + 5, tcz, "minecraft:iron_bars")   # valve
    s.set(tcx, tcy + 6, tcz, st.lightning_rod("up"))
    s.set(tcx - 3, tcy + 1, tcz - 1, st.trapdoor("iron", "east", "bottom", open=True))    # a torn hatch
    sh.texturize(s, IRON, [(IRON, 7), (LGC, 2), (FRAME, 1)], seed=8, region=(5, 0, 5, 13, 8, 13))
    _chunk(s, 13, 13, 0)

    # ---- heat shield disc (r 5.5) at the south-east end of the trail, propped up in its crater
    _heat_shield(s, 36, 34, 5.5, G, Y)

    # ---- tall bent antenna mast (north-east of the bus): dark base plate, iron-bar column, kinked, chain top
    ax, az = 29, 11
    sh.box(s, ax - 1, Y, az - 1, ax + 1, Y, az + 1, SHIP["hull_dark"])
    s.set(ax, Y, az, IRON)
    s.set(ax - 1, G, az + 1, SHIP["light"]); s.set(ax - 1, Y, az + 1, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(ax + 1, Y + 1, az - 1, "minecraft:observer[facing=up]")
    for y in range(Y + 1, Y + 6):
        s.set(ax, y, az, "minecraft:iron_bars")
    s.set(ax + 1, Y + 5, az, "minecraft:iron_bars"); s.set(ax + 2, Y + 5, az, "minecraft:iron_bars")    # the kink
    for y in range(Y + 6, Y + 10):
        s.set(ax + 2, y, az, st.chain("y"))
    s.set(ax + 2, Y + 10, az, st.lightning_rod("up"))
    s.set(ax + 1, Y + 9, az, st.lightning_rod("west")); s.set(ax + 3, Y + 9, az, st.lightning_rod("east"))
    s.set(ax + 3, Y + 5, az, st.lightning_rod("east"))

    # ---- hull sheets, small panels and wreckage chunks along the trail (dense near the bus, thinning south-east)
    _sheet(s, 24, Y, 29, "east")
    _sheet(s, 41, Y, 25, "south")
    _panel(s, 38, G, 21, "east"); s.set(40, G, 19, st.campfire(soul=True))
    _panel(s, 29, Y, 6, "north")
    for (x, z, k) in ((24, 25, 1), (26, 30, 3), (30, 27, 0), (33, 30, 2), (30, 38, 3), (39, 39, 1), (14, 30, 2)):
        _chunk(s, x, z, k)
    for _ in range(16):                                                                   # scorch spots on the axis
        t = rng.random() ** 1.6
        x, z = round(23 + t * 14 + rng.uniform(-2.5, 2.5)), round(23 + t * 12 + rng.uniform(-2.5, 2.5))
        if s.inside(x, G, z) and s.get(x, G, z) == SNOW and s.is_air(x, Y, z):
            s.set(x, G, z, rng.choice(["minecraft:basalt", "minecraft:tuff", "minecraft:blackstone"]))
    sh.texturize(s, scorch, MIX_SCORCH, seed=4)
    sh.texturize(s, SHIP["hull_light"], MIX_WHITE, seed=5)
    sh.snow_cover(s, y_min=Y, prob=0.3, seed=6, layers=(1, 2),
                  skip=["glass", "iron", "gold", "quartz", "lamp", "observer", "detector", "blackstone", "basalt", "coal",
                        "calcite", "log", "polished_deepslate", "light_gray_concrete"])
    return s.cropped(pad=1)


def build():
    return {"cargo_containers": build_cargo(), "orbital_debris": build_orbital()}

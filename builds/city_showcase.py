"""city_showcase: the whole villain tech city assembled from the finished modules.

Walled compound (7 wall segments per side, corner towers, twin-tower gate centred on the south side), the command
spire on a raised 50x50 plaza, factory + hangar + landing pad (gunship parked, nose toward the gate) in the east
district, three habitat towers in the west district, two watchtowers near the back corners.
Added by the assembly: polished-basalt roads with magenta centre lines (gate -> plaza -> every building), a plaza
ring road, sea-lantern street lights, purple banners along the main avenue, obsidian pylons on the plaza corners,
a caged crystal-extraction pen and a supply depot in the north yard, prisoner cages by the gate, crate props with
loot, sculk creeping around building bases, and snow drifts piling against the outside of the walls.

Modules are loaded from schematics/<name>.schem (tools.schem.Schematic.load drops BlockEntities, so signs/chests
are re-read from the NBT here and carried over with rotation + offset).
"""
import math
import random

import nbtlib
import numpy as np
from nbtlib import tag

from tools.schem import Schematic, AIR
from tools import shapes as sh, states as st
from tools.palette import VILLAIN as V, MIX_DARK

ROOT = "/home/user/milax1905/schematics/"

W, H, L, G = 149, 93, 149, 1
XW, XE, ZN, ZS = 4, 143, 4, 143            # outer faces of the wall lines
CX, CZ = 73.5, 73.5                         # compound centre

PBB = V["wall"]                             # polished blackstone bricks
PB = "minecraft:polished_blackstone"
PD = V["wall_smooth"]                       # polished deepslate
DT = V["wall_alt"]                          # deepslate tiles
ROAD = "minecraft:polished_basalt[axis=y]"
MAG = V["road_line"]                        # magenta concrete
LANT = V["floor_light"]                     # sea lantern
FROG = V["light"]
RAILW = V["railing"]                        # polished_blackstone_brick_wall
OBS = V["core"]
CRY = V["core_glow"]
GLASS = V["glass"]
NEON = V["neon"]
SNOW = "minecraft:snow_block"
SIGN = "minecraft:warped_wall_sign"
MIX_ROAD = [(ROAD, 8), ("minecraft:basalt[axis=y]", 1), ("minecraft:smooth_basalt", 1)]
MIX_PLAZA = [(DT, 7), (PD, 2), ("minecraft:cracked_deepslate_tiles", 1)]
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------------------------------ module loading
def _py(v):
    if isinstance(v, tag.Compound):
        return {str(k): _py(x) for k, x in v.items()}
    if isinstance(v, (tag.List, tag.IntArray, tag.ByteArray, tag.LongArray)):
        return [_py(x) for x in v]
    if isinstance(v, str):
        return str(v)
    if isinstance(v, float):
        return float(v)
    return int(v)


_CACHE = {}


def load_module(name):
    """(Schematic, [block entity dicts]) - re-reads BlockEntities that Schematic.load ignores."""
    if name in _CACHE:
        return _CACHE[name]
    path = ROOT + name + ".schem"
    s = Schematic.load(path)
    f = nbtlib.load(path, gzipped=True)
    root = f["Schematic"] if "Schematic" in f else f
    ents = [_py(e) for e in root.get("BlockEntities", [])]
    _CACHE[name] = (s, ents)
    return _CACHE[name]


def _rot_pos(x, z, w, l, k):
    for _ in range(k % 4):
        x, z = l - 1 - z, x
        w, l = l, w
    return x, z


def place(s, name, k, ox, oz, oy=None, clear=False):
    """Paste module `name` rotated k*90 cw so that its ground plane lands on y=G. Returns (x0,z0,x1,z1) footprint."""
    mod, ents = load_module(name)
    if oy is None:
        oy = G - mod.ground
    r = mod.rotated(k) if k % 4 else mod
    if clear:
        sh.box(s, ox, 0, oz, ox + r.w - 1, H - 1, oz + r.l - 1, AIR)
    s.paste(r, ox, oy, oz)
    for e in ents:
        x, y, z = e["Pos"]
        rx, rz = _rot_pos(x, z, mod.w, mod.l, k)
        s.block_entities.append(dict(e, Pos=[rx + ox, y + oy, rz + oz]))
    return ox, oz, ox + r.w - 1, oz + r.l - 1


# ------------------------------------------------------------------------------------------ street furniture
def road(s, x1, z1, x2, z2, line="none", kerb=True):
    """Flush road on the ground plane: basalt with deepslate-tile kerbs and a magenta centre line (2 wide on the
    6-wide avenues, 1 wide on streets). line = 'x' (runs along x), 'z' or 'none'."""
    sh.box(s, x1, G, z1, x2, G, z2, ROAD)
    if kerb:
        for x in range(x1, x2 + 1):
            s.set(x, G, z1, DT); s.set(x, G, z2, DT)
        for z in range(z1, z2 + 1):
            s.set(x1, G, z, DT); s.set(x2, G, z, DT)
    if line == "z":
        w = x2 - x1 + 1
        xs = [x1 + w // 2 - 1, x1 + w // 2] if w >= 6 else [x1 + w // 2]
        for x in xs:
            sh.box(s, x, G, z1 + 1, x, G, z2 - 1, MAG)
    elif line == "x":
        w = z2 - z1 + 1
        zs = [z1 + w // 2 - 1, z1 + w // 2] if w >= 6 else [z1 + w // 2]
        for z in zs:
            sh.box(s, x1 + 1, G, z, x2 - 1, G, z, MAG)


def street_light(s, x, z):
    if not s.is_air(x, G + 1, z):
        return
    for y in (G + 1, G + 2, G + 3):
        s.set(x, y, z, RAILW)
    s.set(x, G + 4, z, LANT)
    s.set(x, G + 5, z, st.slab("polished_blackstone", "bottom"))


def banner_pole(s, x, z, sides=("east", "west")):
    if not s.is_air(x, G + 1, z):
        return
    for y in (G + 1, G + 2, G + 3):
        s.set(x, y, z, RAILW)
    s.set(x, G + 4, z, PB)
    s.set(x, G + 5, z, PB)
    s.set(x, G + 6, z, st.end_rod("up"))
    for f in sides:
        dx, dz = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}[f]
        if s.is_air(x + dx, G + 5, z + dz):
            s.set(x + dx, G + 5, z + dz, st.wall_banner("purple", f))


def crate_stack(s, x, z, seed=0, loot=None, facing="north"):
    """Small pile of supply crates on the ground (2x2 footprint, some stacked)."""
    rng = random.Random(seed)
    crates = ["minecraft:barrel[facing=up,open=false]", "minecraft:barrel[facing=up,open=false]",
              "minecraft:purple_shulker_box[facing=up]", "minecraft:chiseled_polished_blackstone",
              "minecraft:iron_block", "minecraft:magenta_shulker_box[facing=up]"]
    cells = [(x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)]
    for i, (cx, cz) in enumerate(cells):
        if rng.random() < 0.8:
            s.set(cx, G + 1, cz, rng.choice(crates))
            if rng.random() < 0.35:
                s.set(cx, G + 2, cz, rng.choice(crates))
    if loot:
        s.add_chest(x, G + 1, z, facing, loot)


def sculk_ring(s, x1, z1, x2, z2, seed=0, width=2, prob=0.55):
    """Sculk creeping out of a building's base onto the surrounding ground (only replaces snow ground)."""
    rng = random.Random(seed)
    cells = []
    for x in range(x1 - width, x2 + width + 1):
        for z in range(z1 - width, z2 + width + 1):
            if x1 <= x <= x2 and z1 <= z <= z2:
                continue
            d = max(x1 - x, x - x2, z1 - z, z - z2)
            n = sh.value_noise2(x, z, seed, 4.0)
            if s.inside(x, G, z) and s.get(x, G, z) == SNOW and rng.random() < prob * n * 1.7 / d:
                s.set(x, G, z, "minecraft:sculk")
                cells.append((x, z))
    for (x, z) in cells:
        if rng.random() < 0.08 and s.is_air(x, G + 1, z):
            s.set(x, G, z, "minecraft:sculk_catalyst")
        elif rng.random() < 0.06 and s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, "minecraft:sculk_sensor")
        elif rng.random() < 0.3 and s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, "minecraft:sculk_vein[down=true]")


def pylon(s, x, z):
    """Obsidian pylon with a crying-obsidian core and a neon cap (plaza corners)."""
    sh.box(s, x - 1, G + 3, z - 1, x + 1, G + 3, z + 1, PB)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        s.set(x + dx, G + 3, z + dz, st.stairs("polished_blackstone_brick", "north" if dz < 0 else "south"))
    s.set(x, G + 3, z, OBS)
    for y in range(G + 4, G + 9):
        s.set(x, y, z, OBS if y % 2 else CRY)
    s.set(x, G + 9, z, NEON)
    s.set(x, G + 10, z, LANT)
    s.set(x, G + 11, z, st.end_rod("up"))
    for f, (dx, dz) in {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}.items():
        s.set(x + dx, G + 6, z + dz, st.trapdoor("iron", OPP[f], "top", open=True))
        s.set(x + dx, G + 9, z + dz, st.wall_banner("purple", f))


def crystal_pen(s, cx, cz):
    """A wild blue crystal spike the villains fenced in and are drilling: iron-bar pen, chains, a drill mast."""
    sh.box(s, cx - 3, G, cz - 3, cx + 3, G, cz + 3, "minecraft:packed_ice")
    sh.texturize(s, "minecraft:packed_ice", [("minecraft:packed_ice", 5), ("minecraft:blue_ice", 2)], seed=21,
                 region=(cx - 3, G, cz - 3, cx + 3, G, cz + 3))
    # the spike: leaning column of blue ice with amethyst tips
    for i in range(7):
        x, z = cx, cz
        r = 1.6 - i * 0.2
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx * dx + dz * dz <= r * r:
                    s.set(x + dx, G + 1 + i, z + dz, "minecraft:blue_ice" if (dx + dz + i) % 3 else "minecraft:amethyst_block")
    s.set(cx, G + 8, cz, "minecraft:amethyst_cluster[facing=up,waterlogged=false]")
    s.set(cx + 2, G + 3, cz, "minecraft:amethyst_cluster[facing=east,waterlogged=false]")
    s.set(cx, G + 4, cz + 1, "minecraft:amethyst_cluster[facing=south,waterlogged=false]")
    s.set(cx - 2, G + 2, cz, "minecraft:medium_amethyst_bud[facing=west,waterlogged=false]")
    s.set(cx - 1, G + 6, cz, "minecraft:amethyst_cluster[facing=west,waterlogged=false]")
    # pen: iron bars on a blackstone kerb, chains strapping the spike, corner posts with soul lanterns
    for x in range(cx - 4, cx + 5):
        for z in (cz - 4, cz + 4):
            s.set(x, G + 1, z, "minecraft:iron_bars"); s.set(x, G + 2, z, "minecraft:iron_bars")
    for z in range(cz - 4, cz + 5):
        for x in (cx - 4, cx + 4):
            s.set(x, G + 1, z, "minecraft:iron_bars"); s.set(x, G + 2, z, "minecraft:iron_bars")
    for x, z in ((cx - 4, cz - 4), (cx + 4, cz - 4), (cx - 4, cz + 4), (cx + 4, cz + 4)):
        for y in (G + 1, G + 2, G + 3):
            s.set(x, y, z, RAILW)
        s.set(x, G + 4, z, PB)
        s.set(x, G + 5, z, st.lantern(soul=True, hanging=False))
    for x in range(cx - 3, cx + 4):
        s.set(x, G + 3, cz + 1, st.chain("x"))
    for z in range(cz - 3, cz + 2):
        s.set(cx - 1, G + 5, z, st.chain("z"))
    # drill mast leaning over the spike
    sh.box(s, cx + 4, G + 1, cz + 4, cx + 4, G + 9, cz + 4, PB)
    sh.box(s, cx + 1, G + 10, cz + 4, cx + 4, G + 10, cz + 4, "minecraft:iron_block")     # boom west...
    sh.box(s, cx + 1, G + 10, cz + 1, cx + 1, G + 10, cz + 3, "minecraft:iron_block")     # ...then north over the spike
    s.set(cx + 1, G + 11, cz + 4, st.end_rod("up"))
    s.set(cx + 1, G + 9, cz + 1, st.chain("y"))
    s.set(cx + 1, G + 8, cz + 1, "minecraft:hopper[enabled=true,facing=down]")
    s.set(cx + 1, G + 7, cz + 1, st.pointed_dripstone("down", "frustum"))
    s.set(cx + 1, G + 6, cz + 1, st.pointed_dripstone("down", "tip"))
    s.set(cx + 4, G + 6, cz + 4, st.redstone_lamp(True))
    s.set(cx + 5, G + 1, cz + 4, "minecraft:blast_furnace[facing=east,lit=true]")
    s.set(cx + 5, G + 1, cz + 3, "minecraft:cauldron")
    s.set(cx + 5, G + 2, cz + 4, PB)
    s.add_sign(cx + 5, G + 2, cz + 5, SIGN + "[facing=south]", ["EXTRACTION 3", "cristal instable", "rendement 40%", "ne pas toucher"])


def prisoner_cage(s, x, z, facing="north"):
    """3x3 iron-bar cage on a deepslate plinth with a soul lantern - the villains keep captured explorers here."""
    sh.box(s, x - 1, G + 1, z - 1, x + 1, G + 1, z + 1, PD)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if abs(dx) == 1 or abs(dz) == 1:
                for y in (G + 2, G + 3, G + 4):
                    s.set(x + dx, y, z + dz, "minecraft:iron_bars")
    sh.box(s, x - 1, G + 5, z - 1, x + 1, G + 5, z + 1, st.slab("polished_deepslate", "bottom"))
    s.set(x, G + 5, z, PD)
    s.set(x, G + 4, z, st.lantern(soul=True, hanging=True))
    s.set(x, G + 2, z, st.stairs("polished_deepslate", facing))
    s.set(x, G + 6, z, st.chain("y")); s.set(x, G + 7, z, st.chain("y"))
    s.set(x, G + 8, z, st.end_rod("up"))


def antenna_array(s, cx, cz):
    """Comms yard: a tall lattice mast with guy chains and two shorter relay masts on a deepslate pad."""
    sh.box(s, cx - 7, G, cz - 5, cx + 7, G, cz + 5, DT)
    sh.texturize(s, DT, MIX_PLAZA, seed=61, region=(cx - 7, G, cz - 5, cx + 7, G, cz + 5))
    def mast(x, z, h, big):
        sh.box(s, x - 1, G + 1, z - 1, x + 1, G + 1, z + 1, PB)
        for y in range(G + 2, G + 2 + h):
            if big:
                for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    s.set(x + dx, y, z + dz, RAILW if y % 4 else "minecraft:iron_block")
                if y % 4 == 0:
                    for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        s.set(x + dx, y, z + dz, "minecraft:iron_block")
                    s.set(x, y, z, LANT)
            else:
                s.set(x, y, z, RAILW if y % 3 else "minecraft:iron_block")
        top = G + 2 + h
        if big:
            sh.box(s, x - 1, top, z - 1, x + 1, top, z + 1, PB)
            s.set(x, top + 1, z, "minecraft:iron_block")
            s.set(x, top + 2, z, LANT)
            for i in range(1, 4):
                s.set(x, top + 2 + i, z, st.lightning_rod("up"))
            for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                s.set(x + dx, top + 1, z + dz, st.end_rod({(-1, 0): "west", (1, 0): "east", (0, -1): "north", (0, 1): "south"}[(dx, dz)]))
            # dish: a shallow bowl of stairs on a bracket
            s.set(x + 2, top - 3, z, "minecraft:iron_block")
            s.set(x + 3, top - 3, z, PB)
            for dz in (-1, 0, 1):
                s.set(x + 4, top - 3, z + dz, st.stairs("polished_deepslate", "east", "bottom") if dz else PD)
                s.set(x + 3, top - 2, z + dz, st.stairs("polished_deepslate", "west", "top"))
            s.set(x + 3, top - 3, z - 1, st.stairs("polished_deepslate", "south", "bottom"))
            s.set(x + 3, top - 3, z + 1, st.stairs("polished_deepslate", "north", "bottom"))
            s.set(x + 4, top - 2, z, st.end_rod("east"))
        else:
            s.set(x, top, z, "minecraft:iron_block")
            s.set(x, top + 1, z, st.lightning_rod("up"))
            for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                s.set(x + dx, top, z + dz, st.trapdoor("iron", "north", "top", open=False))
    mast(cx, cz, 18, True)
    mast(cx - 5, cz + 3, 9, False)
    mast(cx + 5, cz - 3, 11, False)
    # anchor blocks + short chain stays hanging from the mast crossbars
    for (ax, az) in ((cx - 6, cz - 4), (cx + 6, cz + 4), (cx + 6, cz - 4)):
        s.set(ax, G + 1, az, "minecraft:iron_block")
        s.set(ax, G + 2, az, RAILW)
    for (px, pz) in ((cx - 1, cz - 1), (cx + 1, cz + 1)):
        for y in range(G + 14, G + 18):
            s.set(px, y, pz, st.chain("y")) if s.is_air(px, y, pz) else None
    s.set(cx - 6, G + 1, cz + 4, "minecraft:observer[facing=up,powered=false]")
    s.set(cx - 5, G + 1, cz + 5, "minecraft:daylight_detector[inverted=false,power=0]")
    s.add_sign(cx + 6, G + 2, cz + 5, SIGN + "[facing=south]", ["RELAIS COMM 2", "liaison orbite", "brouillage actif", "ne pas couper"])


def tank_farm(s, cx, cz):
    """Three banded fuel tanks on a deepslate pad with a pipe rack running toward the factory."""
    sh.box(s, cx - 9, G, cz - 6, cx + 9, G, cz + 6, DT)
    sh.texturize(s, DT, MIX_PLAZA, seed=62, region=(cx - 9, G, cz - 6, cx + 9, G, cz + 6))
    for i, (tx, tz) in enumerate(((cx - 6, cz), (cx, cz), (cx + 6, cz))):
        sh.cylinder(s, tx, G + 1, tz, 2.6, 0, PD, axis="y")
        sh.cylinder(s, tx, G + 2, tz, 2.6, 5, V["pipe"], axis="y")                 # oxidized copper drum
        sh.cylinder(s, tx, G + 4, tz, 2.7, 0, "minecraft:iron_block", axis="y", hollow=True, thickness=1.0)
        sh.cylinder(s, tx, G + 8, tz, 2.2, 0, PD, axis="y")
        sh.ring_stairs(s, tx, G + 8, tz, 2.7, "polished_deepslate", half="bottom")
        s.set(tx, G + 9, tz, "minecraft:iron_block")
        s.set(tx, G + 10, tz, st.lantern(soul=True))
        s.set(tx + 2, G + 6, tz, MAG); s.set(tx - 2, G + 6, tz, MAG)                 # hazard markings
        s.set(tx, G + 3, tz - 3, st.trapdoor("iron", "north", "top", open=True))
    # pipe rack along the north edge, dropping into each tank
    sh.box(s, cx - 8, G + 3, cz - 5, cx + 8, G + 3, cz - 5, V["pipe_cut"])
    for x in (cx - 8, cx - 3, cx + 3, cx + 8):
        s.set(x, G + 1, cz - 5, RAILW); s.set(x, G + 2, cz - 5, RAILW)
    for tx in (cx - 6, cx, cx + 6):
        s.set(tx, G + 3, cz - 4, V["pipe_cut"])
    s.set(cx + 8, G + 4, cz - 5, "minecraft:oxidized_copper")
    s.set(cx + 8, G + 5, cz - 5, st.campfire(soul=True))                              # vent flare
    s.set(cx - 8, G + 1, cz + 4, "minecraft:cauldron"); s.set(cx - 7, G + 1, cz + 4, "minecraft:cauldron")
    s.set(cx + 7, G + 1, cz + 4, "minecraft:barrel[facing=up,open=false]"); s.set(cx + 8, G + 1, cz + 4, "minecraft:barrel[facing=up,open=false]")
    s.set(cx - 9, G + 1, cz + 5, RAILW); s.set(cx - 9, G + 2, cz + 5, PB)
    s.add_sign(cx - 9, G + 2, cz + 6, SIGN + "[facing=south]", ["CARBURANT", "reserve 3 jours", "fuite cuve 2", "interdit de fumer"])


def sculk_garden(s, cx, cz):
    """The villains farm sculk: a fenced bed of sculk with catalysts, shriekers and sensors under lantern posts."""
    sh.box(s, cx - 8, G, cz - 6, cx + 8, G, cz + 6, DT)
    sh.box(s, cx - 7, G, cz - 5, cx + 7, G, cz + 5, "minecraft:sculk")
    rng = random.Random(77)
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 5, cz + 6):
            r = rng.random()
            if r < 0.05:
                s.set(x, G, z, "minecraft:sculk_catalyst")
            elif r < 0.08:
                s.set(x, G + 1, z, "minecraft:sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]")
            elif r < 0.13:
                s.set(x, G + 1, z, "minecraft:sculk_sensor")
            elif r < 0.35:
                s.set(x, G + 1, z, "minecraft:sculk_vein[down=true]")
    sh.box(s, cx - 1, G, cz - 5, cx + 1, G, cz + 5, DT)                                  # walkway through the bed
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 5, cz + 6):
            if not s.is_air(x, G + 1, z):
                s.set(x, G + 1, z, AIR)
    for x in range(cx - 8, cx + 9):
        for z in (cz - 6, cz + 6):
            if (x, z) not in ((cx, cz + 6),):
                s.set(x, G + 1, z, "minecraft:iron_bars")
    for z in range(cz - 6, cz + 7):
        for x in (cx - 8, cx + 8):
            s.set(x, G + 1, z, "minecraft:iron_bars")
    for x, z in ((cx - 8, cz - 6), (cx + 8, cz - 6), (cx - 8, cz + 6), (cx + 8, cz + 6)):
        s.set(x, G + 1, z, RAILW); s.set(x, G + 2, z, RAILW); s.set(x, G + 3, z, LANT)
    s.set(cx, G + 1, cz + 6, AIR)
    for x in (cx - 4, cx + 4):
        s.set(x, G + 1, cz, "minecraft:obsidian"); s.set(x, G + 2, cz, CRY); s.set(x, G + 3, cz, GLASS)
        s.set(x, G + 4, cz, st.end_rod("up"))
    s.set(cx + 2, G + 1, cz + 6, RAILW); s.set(cx + 2, G + 2, cz + 6, RAILW)
    s.add_sign(cx + 2, G + 2, cz + 7, SIGN + "[facing=south]", ["CULTURE SCULK", "lot 4", "ne pas marcher", "ca ecoute"])


def hover_sled(s, x, z, facing="north", seed=0):
    """Small parked 1-seat hover sled (5 long x 3 wide): black hull, purple canopy, skids, tail lights."""
    along_x = facing in ("east", "west")
    def P(u, v):                        # (u along the sled, v across) -> world
        if facing == "north": return x + v, z + u
        if facing == "south": return x - v, z - u
        if facing == "east": return x - u, z - v
        return x + u, z + v
    for u in range(-2, 3):
        for v in (-1, 0, 1):
            wx, wz = P(u, v)
            s.set(wx, G + 2, wz, PB if v == 0 or abs(u) < 2 else st.slab("polished_blackstone", "bottom"))
    for v in (-1, 1):                   # skids
        for u in (-1, 1):
            wx, wz = P(u, v); s.set(wx, G + 1, wz, st.slab("polished_deepslate", "top"))
    wx, wz = P(-2, 0); s.set(wx, G + 2, wz, st.stairs("polished_blackstone_brick", facing, "bottom"))
    wx, wz = P(2, 0); s.set(wx, G + 2, wz, st.stairs("polished_blackstone_brick", OPP[facing], "bottom"))
    wx, wz = P(0, 0); s.set(wx, G + 3, wz, st.stairs("polished_blackstone_brick", OPP[facing], "bottom"))  # seat back
    wx, wz = P(-1, 0); s.set(wx, G + 3, wz, GLASS)                                                            # canopy
    wx, wz = P(2, 0); s.set(wx, G + 3, wz, st.end_rod("up") if seed % 2 else st.trapdoor("iron", facing, "bottom", open=False))
    for v in (-1, 1):
        wx, wz = P(2, v); s.set(wx, G + 2, wz, NEON)                                                          # tail lights
    wx, wz = P(-2, 0); s.set(wx, G + 1, wz, st.trapdoor("iron", facing, "top", open=True))


def motor_pool(s, cx, cz):
    """Vehicle yard: a striped apron with parked hover sleds, a charging post and crates."""
    sh.box(s, cx - 10, G, cz - 8, cx + 10, G, cz + 8, ROAD)
    sh.box(s, cx - 10, G, cz - 8, cx + 10, G, cz - 8, DT); sh.box(s, cx - 10, G, cz + 8, cx + 10, G, cz + 8, DT)
    for i, x in enumerate(range(cx - 8, cx + 9, 4)):
        sh.box(s, x, G, cz - 7, x, G, cz + 7, MAG)                                     # bay lines
    for i, x in enumerate(range(cx - 6, cx + 8, 4)):
        if i != 2:
            hover_sled(s, x, cz - 3, "north", seed=i)
    hover_sled(s, cx + 6, cz + 4, "south", seed=1)
    # charging post + cable
    s.set(cx - 9, G + 1, cz + 6, PB); s.set(cx - 9, G + 2, cz + 6, PB); s.set(cx - 9, G + 3, cz + 6, st.redstone_lamp(True))
    s.set(cx - 9, G + 4, cz + 6, st.slab("polished_deepslate", "bottom"))
    for x in range(cx - 8, cx - 5):
        s.set(x, G + 1, cz + 6, st.chain("x"))
    crate_stack(s, cx - 3, cz + 5, seed=71, loot="minecraft:chests/pillager_outpost")
    crate_stack(s, cx + 1, cz + 6, seed=72)
    s.add_sign(cx - 9, G + 3, cz + 7, SIGN + "[facing=south]", ["PARC MOTEURS", "sled 3 en panne", "recharge 2h", "casque oblig."])


def snow_drifts(s, seed=5):
    """Snow piling against the OUTSIDE faces of the walls (2-3 blocks out, wavy), nothing inside the compound."""
    for x in range(W):
        for z in range(L):
            # distance to the nearest wall face, only outside the compound
            dx = XW - x if x < XW else (x - XE if x > XE else -1)
            dz = ZN - z if z < ZN else (z - ZS if z > ZS else -1)
            if dx < 0 and dz < 0:
                continue
            d = min(v for v in (dx, dz) if v >= 0)
            if d < 1:
                continue
            n = sh.value_noise2(x, z, seed, 9.0) * 0.7 + 0.3 * sh.value_noise2(x + 50, z + 50, seed + 3, 3.5)
            h = (3.1 - d) * (0.15 + 1.25 * n)         # in blocks: wavy, sometimes 2 blocks, sometimes nothing
            if h <= 0.12:
                continue
            # only pile on snow ground that has air above (never on the wall / towers / road)
            if s.get(x, G, z) != SNOW or not s.is_air(x, G + 1, z):
                continue
            y = G + 1
            while h >= 1.0 and y < G + 3:
                s.set(x, y, z, SNOW)
                y += 1
                h -= 1.0
            layers = int(round(h * 8))
            if layers >= 1:
                s.set(x, y, z, st.snow_layer(min(8, layers)))


# ------------------------------------------------------------------------------------------ the assembly
def build():
    s = Schematic(W, H, L, ground=G)
    sh.box(s, 0, G, 0, W - 1, G, L - 1, SNOW)                     # flat snow ground the compound sits in

    # ---- walls: 7 segments per side, corners, gate centred on the south side
    for i in range(7):
        o = 18 + 16 * i
        place(s, "city_wall_segment", 0, o, ZN)                     # north (outer face z=4)
        place(s, "city_wall_segment", 2, o, ZS - 4)                 # south (outer face z=143)
        place(s, "city_wall_segment", 3, XW, o)                     # west
        place(s, "city_wall_segment", 1, XE - 4, o)                 # east
    place(s, "city_wall_corner", 0, 2, 2)                           # NW
    place(s, "city_wall_corner", 1, 130, 2)                         # NE
    place(s, "city_wall_corner", 2, 130, 130)                       # SE
    place(s, "city_wall_corner", 3, 2, 130)                         # SW
    place(s, "city_gate", 2, 62, 134, clear=True)                   # gate towers replace the seam piers (4 blocks each side)

    # ---- roads (flush with the ground) - laid before buildings so building bases win
    road(s, 71, 99, 76, 133, "z")                                   # main avenue: plaza -> gate
    road(s, 71, 146, 76, 148, "z", kerb=False)                      # ...continues out of the gate
    road(s, 71, 24, 76, 48, "z")                                    # north avenue
    road(s, 45, 45, 48, 102, "z"); road(s, 99, 45, 102, 102, "z")   # plaza ring road
    road(s, 45, 45, 102, 48, "x"); road(s, 45, 99, 102, 102, "x")
    road(s, 45, 20, 48, 44, "z"); road(s, 99, 20, 102, 44, "z")     # NW / NE streets up to the service road
    road(s, 20, 20, 127, 23, "x")                                   # north service road (watchtower to watchtower)
    road(s, 103, 31, 106, 34, "x", kerb=False)                      # factory dock spur
    road(s, 103, 95, 126, 97, "x")                                  # hangar -> landing pad spur
    road(s, 20, 48, 44, 51, "x")                                    # hab 1 street
    road(s, 38, 71, 44, 76, "x")                                    # west avenue (hab 2 door)
    road(s, 20, 122, 70, 125, "x")                                  # hab 3 street -> main avenue
    # junction patches (remove kerb lines where roads cross)
    for (x1, z1, x2, z2) in ((71, 45, 76, 48), (71, 99, 76, 102), (45, 71, 48, 76), (99, 71, 102, 76),
                             (45, 20, 48, 23), (99, 20, 102, 23), (71, 20, 76, 23), (45, 48, 48, 51),
                             (99, 95, 102, 97), (71, 122, 76, 125), (99, 31, 102, 34), (71, 133, 76, 133),
                             (45, 122, 48, 125) if False else (72, 133, 75, 133)):
        sh.box(s, x1, G, z1, x2, G, z2, ROAD)
    sh.box(s, 73, G, 20, 74, G, 133, MAG)                           # unbroken magenta axis gate -> plaza -> north
    sh.box(s, 73, G, 146, 74, G, 148, MAG)
    sh.box(s, 46, G, 73, 102, G, 74, MAG)                           # unbroken east-west axis (under the plaza too)

    # ---- central raised plaza (2 high) with the spire on top
    px1, pz1, px2, pz2 = 49, 49, 98, 98
    sh.box(s, px1, G + 1, pz1, px2, G + 1, pz2, PBB)
    sh.box(s, px1, G + 2, pz1, px2, G + 2, pz2, DT)
    sh.box_edge_stairs(s, px1, G + 1, pz1, px2, pz2, "polished_blackstone_brick", half="bottom")   # bevelled foot
    # 4 stairways (6 wide) in the middle of each side
    for x in range(71, 77):
        s.set(x, G + 1, pz1 - 1, st.stairs("polished_blackstone_brick", "south"))
        s.set(x, G + 2, pz1, st.stairs("deepslate_tile", "south"))
        s.set(x, G + 1, pz2 + 1, st.stairs("polished_blackstone_brick", "north"))
        s.set(x, G + 2, pz2, st.stairs("deepslate_tile", "north"))
    for z in range(71, 77):
        s.set(px1 - 1, G + 1, z, st.stairs("polished_blackstone_brick", "east"))
        s.set(px1, G + 2, z, st.stairs("deepslate_tile", "east"))
        s.set(px2 + 1, G + 1, z, st.stairs("polished_blackstone_brick", "west"))
        s.set(px2, G + 2, z, st.stairs("deepslate_tile", "west"))
    sh.texturize(s, DT, MIX_PLAZA, seed=7, region=(px1, G + 2, pz1, px2, G + 2, pz2))
    # magenta pattern: inner ring + axes + diagonals to the corners; sea lanterns along the rim
    for x in range(px1 + 3, px2 - 2):
        s.set(x, G + 2, pz1 + 3, MAG); s.set(x, G + 2, pz2 - 3, MAG)
    for z in range(pz1 + 3, pz2 - 2):
        s.set(px1 + 3, G + 2, z, MAG); s.set(px2 - 3, G + 2, z, MAG)
    sh.box(s, 73, G + 2, pz1 + 1, 74, G + 2, pz2 - 1, MAG)
    sh.box(s, px1 + 1, G + 2, 73, px2 - 1, G + 2, 74, MAG)
    for i in range(4, 22):
        for sx, sz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            s.set(73 + i if sx > 0 else 74 - i, G + 2, 73 + i if sz > 0 else 74 - i, MAG)
    for i in range(px1 + 4, px2 - 3, 6):
        s.set(i, G + 2, pz1 + 1, LANT); s.set(i, G + 2, pz2 - 1, LANT)
        s.set(px1 + 1, G + 2, i, LANT); s.set(px2 - 1, G + 2, i, LANT)
    # neon strip lit from inside the plinth (magenta glass in the side face, lanterns behind)
    for x in range(px1 + 2, px2 - 1, 3):
        for zz, inner in ((pz1, pz1 + 1), (pz2, pz2 - 1)):
            s.set(x, G + 1, zz, NEON); s.set(x, G + 1, inner, LANT)
    for z in range(pz1 + 2, pz2 - 1, 3):
        for xx, inner in ((px1, px1 + 1), (px2, px2 - 1)):
            s.set(xx, G + 1, z, NEON); s.set(inner, G + 1, z, LANT)
    place(s, "city_spire", 0, 57, 57, oy=G + 2 - 2)                # its own plaza (local y=2) lands on the platform top
    for x, z in ((px1 + 2, pz1 + 2), (px2 - 2, pz1 + 2), (px1 + 2, pz2 - 2), (px2 - 2, pz2 - 2)):
        pylon(s, x, z)

    # ---- east district: factory (dock west), hangar (door west onto the ring road), landing pad + gunship
    fx = place(s, "city_factory", 1, 107, 22)
    hx = place(s, "city_hangar", 0, 103, 65)
    padf = place(s, "city_landing_pad", 2, 102, 97)
    place(s, "villain_ship", 2, 102 + 7, 97 + 4, oy=3)             # gear on the pad floor (y=4), nose to the gate
    # ---- west district: three habitat towers
    h1 = place(s, "city_hab_block", 0, 14, 22)
    h2 = place(s, "city_hab_block", 3, 12, 65)
    h3 = place(s, "city_hab_block", 0, 14, 96)
    # ---- watchtowers near the back corners
    t1 = place(s, "city_watchtower", 0, 10, 10)
    t2 = place(s, "city_watchtower", 1, 128, 10)

    # ---- sculk creeping out of the building bases
    for i, fp in enumerate((fx, hx, h1, h2, h3, t1, t2)):
        sculk_ring(s, fp[0], fp[1], fp[2], fp[3], seed=30 + i)
    sculk_ring(s, px1 - 1, pz1 - 1, px2 + 1, pz2 + 1, seed=40, width=3, prob=0.35)

    # ---- street lights and banners
    for z in range(104, 133, 8):
        street_light(s, 70, z); street_light(s, 77, z)
    for z in range(108, 133, 8):
        banner_pole(s, 70, z); banner_pole(s, 77, z)
    for z in range(26, 45, 9):
        street_light(s, 70, z); street_light(s, 77, z)
    for x in range(44, 104, 12):                                    # ring road corners / sides
        street_light(s, x, 44); street_light(s, x, 103)
    for z in range(56, 92, 12):
        street_light(s, 44, z)
    for x in range(24, 128, 13):
        street_light(s, x, 19)
    for x in (24, 36):
        street_light(s, x, 52); street_light(s, x, 121)
    street_light(s, 112, 98); street_light(s, 124, 98)
    street_light(s, 40, 70); street_light(s, 40, 77)

    # ---- north yard: crystal extraction pen (west) + supply depot (east)
    crystal_pen(s, 60, 13)
    for i, (x, z) in enumerate(((84, 10), (88, 10), (84, 14), (89, 15), (92, 12))):
        crate_stack(s, x, z, seed=50 + i, loot="minecraft:chests/bastion_other" if i == 2 else None)
    for y in (G + 1, G + 2, G + 3):
        s.set(82, y, 17, RAILW)
    s.set(82, G + 4, 17, PB)
    s.add_sign(82, G + 3, 18, SIGN + "[facing=south]", ["DEPOT NORD", "inventaire j.12", "3 caisses", "manquent"])
    # ---- props: crates at the factory dock, the hangar apron and by the pad stairs; prisoner cages by the gate
    crate_stack(s, 104, 27, seed=60); crate_stack(s, 104, 36, seed=61, loot="minecraft:chests/abandoned_mineshaft")
    crate_stack(s, 100, 66, seed=62); crate_stack(s, 100, 88, seed=63)
    crate_stack(s, 128, 94, seed=64, loot="minecraft:chests/end_city_treasure")
    prisoner_cage(s, 66, 129, "east"); prisoner_cage(s, 81, 129, "west")
    s.add_sign(68, G + 3, 129, SIGN + "[facing=east]", ["CELLULE 2", "exploratrice", "capturee jour 9", "interrogatoire"])
    # welcome / warning sign posts inside the gate and at the plaza foot
    for y in (G + 1, G + 2):
        s.set(79, y, 132, RAILW); s.set(68, y, 132, RAILW)
    s.set(79, G + 3, 132, PB); s.set(68, G + 3, 132, PB)
    s.add_sign(78, G + 3, 132, SIGN + "[facing=west]", ["SECTEUR 7", "VOLKOV CORP", "badge obligatoire", "tir a vue"])
    s.add_sign(69, G + 3, 132, SIGN + "[facing=east]", ["PISTE 1 -> est", "usine -> nord-est", "quartiers -> ouest", "spire -> nord"])
    for y in (G + 1, G + 2):
        s.set(69, y, 101, RAILW)
    s.set(69, G + 3, 101, PB)
    s.add_sign(69, G + 3, 102, SIGN + "[facing=south]", ["PLACE DU", "COMMANDANT", "silence", "obligatoire"])

    # ---- the four empty lots around the plaza
    antenna_array(s, 60, 34)
    tank_farm(s, 88, 34)
    sculk_garden(s, 60, 112)
    motor_pool(s, 88, 112)

    # ---- weathering: snow drifts outside the walls, a little snow inside the compound corners
    snow_drifts(s)
    sh.texturize(s, ROAD, MIX_ROAD, seed=9)
    snow_skip = ["glass", "froglight", "sea_lantern", "sculk", "ladder", "copper", "iron", "hopper", "observer", "furnace",
                 "barrel", "chest", "obsidian", "lamp", "amethyst", "magenta", "purple", "ice", "cauldron", "shulker",
                 "daylight", "campfire", "detector", "blackstone_bricks", "deepslate_bricks"]
    for (x1, z1, x2, z2) in ((49, 49, 98, 98), (50, 26, 70, 44), (77, 26, 98, 44), (50, 104, 70, 121), (77, 104, 98, 121)):
        sh.snow_cover(s, x1, z1, x2, z2, y_min=G + 2, prob=0.07, seed=12, layers=(1, 2), skip=snow_skip)   # light dusting
    # drop block entities whose block was overwritten (cleared seam piers etc.)
    keep = []
    for e in s.block_entities:
        x, y, z = e["Pos"]
        b = s.get(x, y, z) if s.inside(x, y, z) else AIR
        if any(k in b for k in ("sign", "chest", "barrel")):
            keep.append(e)
    s.block_entities = keep
    return {"city_showcase": s.cropped(pad=1)}

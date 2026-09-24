"""Villain city landing pad + parked gunship.

city_landing_pad : octagonal raised pad (dark drum, neon underglow strip, overhanging floor with icicles) with
                   polished deepslate floor, magenta H + ring markings, sea-lantern runway lights, purple glass strips
                   lit from below, two stairways, fuel depot (oxidized-copper banded tank, pumps, hoses), glass control
                   booth (furnished), four floodlight masts and a lattice-boom crane setting a crate down. Snow
                   drifts on the skirt, rim, stairs and roofs. Sits flush in the snow on a deepslate skirt.
villain_ship     : sleek black gunship, gear down: lofted flattened hull, glowing purple belt line + vents, high
                   forward-swept wings with ribs / flaps / hard-points, big twin engine pods (4x4 rounded section,
                   magenta 2x2 nozzle core over sea lanterns, blue idle smoke) protruding past the tail, tinted +
                   purple cockpit canopy with a magenta eyebrow, chin turret, wing-tip cannons, starboard boarding
                   ramp, lit walkable interior (cockpit + cargo bay).
Both ground=1; the ship is meant to be pasted on top of the pad (centre of the H, ground plane on the floor)."""
import math

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import VILLAIN as V, MIX_BLACK, MIX_DARK

PBB = V["wall"]                 # polished blackstone bricks
DT = V["wall_alt"]              # deepslate tiles
PD = V["wall_smooth"]           # polished deepslate
PB = "minecraft:polished_blackstone"
LANT = V["floor_light"]         # sea lantern
GLASS = V["glass"]              # purple stained glass
NEON = V["neon"]                # magenta stained glass
TINT = V["glass_dark"]          # tinted glass
MAG = V["accent_alt"]           # magenta concrete
NETH = V["metal_dark"]
IRON = V["metal_light"]
OBS = V["core"]
CRY = V["core_glow"]
OXC = V["pipe"]                 # oxidized copper (teal - matches the blue crystals)
OXCUT = V["pipe_cut"]           # oxidized cut copper
WALL = "polished_blackstone_brick"      # wall / stairs material
WALLB = f"minecraft:{WALL}_wall"
SIGN = "minecraft:warped_wall_sign"
BARS = "minecraft:iron_bars"
MIX_TILES = [(DT, 7), (PD, 2), ("minecraft:cracked_deepslate_tiles", 1)]
MIX_HULL = [(PB, 6), (PBB, 2), (PD, 1), (DT, 1)]


# =================================================================================================================
#  LANDING PAD
# =================================================================================================================
def build_pad():
    W, H, L, G = 40, 17, 40, 1
    s = Schematic(W, H, L, ground=G)
    C = 19.5
    CH = 1.35
    xs = np.arange(W)[:, None].astype(float)
    zs = np.arange(L)[None, :].astype(float)
    DX, DZ = np.abs(xs - C), np.abs(zs - C)
    R = np.hypot(xs - C, zs - C)

    def octa(hw):
        return (DX <= hw) & (DZ <= hw) & (DX + DZ <= hw * CH)

    def oring(a, b):
        return octa(b) & ~octa(a)

    def fill2d(mask, y, block):
        for x, z in zip(*np.nonzero(mask)):
            s.set(int(x), y, int(z), block)

    def by_angle(mask):
        return sorted(zip(*np.nonzero(mask)), key=lambda p: math.atan2(p[1] - C, p[0] - C))

    FLOOR = G + 3                                    # y=4 : pad floor, players walk at y=5
    # ---------------------------------------------------------------- foundation + skirt (flush with the snow)
    fill2d(octa(14.5), 0, DT)
    fill2d(octa(17.5), G, DT)
    # sculk creeping on the skirt (villain signature), a couple of crystals
    rng = np.random.default_rng(3)
    for x, z in zip(*np.nonzero(oring(14.5, 17.5))):
        r = rng.random()
        if r < 0.10:
            s.set(int(x), G, int(z), V["sculk"])
        elif r < 0.115:
            s.set(int(x), G, int(z), V["sculk_glow"])
    for (x, z) in ((2, 17), (37, 22), (2, 23)):                      # on the skirt, outside the floor lip
        s.set(x, G + 1, z, st.facing_block("minecraft:amethyst_cluster", "up"))
    # ---------------------------------------------------------------- drum, neon strip, overhanging floor
    fill2d(octa(14.5), G + 1, PBB)                                   # y=2 recessed drum
    fill2d(octa(13.5), G + 2, PD)                                    # y=3 core
    fill2d(oring(13.5, 14.5), G + 2, LANT)                           # y=3 lantern ring (lights strip + glass above)
    fill2d(oring(14.5, 15.5), G + 2, NEON)                           # y=3 magenta neon strip (visible under the lip)
    fill2d(octa(16.5), FLOOR, PD)                                    # y=4 floor
    fill2d(oring(13.5, 14.5), FLOOR, GLASS)                          # purple glass ring lit from below
    rim = oring(15.5, 16.5)
    fill2d(rim, FLOOR, DT)
    # runway lights: every 3rd rim cell (sorted by angle)
    for i, (x, z) in enumerate(by_angle(rim)):
        if i % 3 == 0:
            s.set(int(x), FLOOR, int(z), LANT)
    # 8 support pylons at the octagon vertices (so the lip does not look like it hovers)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        x, z = round(C + 15.3 * math.cos(a)), round(C + 15.3 * math.sin(a))
        for y in (G + 1, G + 2):
            s.set(x, y, z, OBS if y == G + 1 else CRY)
    # icicles hanging under the lip (every ~4 cells of the overhang ring)
    for i, (x, z) in enumerate(by_angle(oring(15.5, 16.5))):
        if i % 4 == 1 and s.is_air(int(x), G + 2, int(z)):
            s.set(int(x), G + 2, int(z), st.pointed_dripstone("down", "tip"))
    # ---------------------------------------------------------------- markings
    fill2d((R >= 9.6) & (R <= 10.6), FLOOR, MAG)                     # ring
    for x in (16, 17, 22, 23):                                       # H uprights
        sh.box(s, x, FLOOR, 15, x, FLOOR, 24, MAG)
    sh.box(s, 18, FLOOR, 19, 21, FLOOR, 20, MAG)                     # H bar
    for (x1, z1, x2, z2) in ((19, 5, 20, 8), (19, 31, 20, 34), (5, 19, 8, 20), (31, 19, 34, 20)):
        sh.box(s, x1, FLOOR, z1, x2, FLOOR, z2, GLASS)               # radial purple strips ...
        sh.box(s, x1, FLOOR - 1, z1, x2, FLOOR - 1, z2, LANT)        # ... lit from below
    # ---------------------------------------------------------------- stairways (south main, north wide)
    def stairway(x1, x2, south: bool):
        for i, y in enumerate((FLOOR - 1, FLOOR - 2)):               # two steps down to the snow
            z = (36 + 1 + i) if south else (3 - 1 - i)
            for x in range(x1, x2 + 1):
                s.set(x, y, z, st.stairs(WALL, "north" if south else "south"))
                sh.box(s, x, G, z, x, y - 1, z, PBB)
        # rails: wall posts + end-rod tips
        for x in (x1 - 1, x2 + 1):
            for i, y in enumerate((FLOOR, FLOOR - 1)):
                z = (36 + 1 + i) if south else (3 - 1 - i)
                sh.box(s, x, G, z, x, y - 1, z, PBB)
                s.set(x, y, z, WALLB)
            z0 = 37 if south else 2
            s.set(x, FLOOR + 1, z0, st.end_rod("up"))
        # magenta edge line on the top step
        z = 36 if south else 3
        for x in range(x1, x2 + 1):
            s.set(x, FLOOR, z, MAG if x % 2 == 0 else DT)
    stairway(17, 22, True)
    stairway(16, 23, False)
    # ---------------------------------------------------------------- floodlight masts (west / east edges, clear of the ship)
    for (mx, mz) in ((5, 12), (5, 27), (34, 12), (34, 27)):
        sx = 1 if mx < C else -1                                     # toward the centre
        s.set(mx, FLOOR + 1, mz, NETH)                               # 2-block base
        s.set(mx, FLOOR + 2, mz, PBB)
        s.set(mx + sx, FLOOR + 1, mz, PBB)
        s.set(mx + sx, FLOOR + 2, mz, st.slab("polished_deepslate"))
        for dz in (-1, 1):
            s.set(mx, FLOOR + 1, mz + dz, st.slab("polished_deepslate"))
        for y in range(FLOOR + 3, FLOOR + 8):                        # doubled post: wall + hanging chain
            s.set(mx, y, mz, WALLB)
            s.set(mx + sx, y, mz, st.chain("y"))
        # 3-block head: lantern flanked by end rods + trapdoor shrouds, purple glass on top, tile slab cap
        s.set(mx, FLOOR + 8, mz, LANT)
        s.set(mx + sx, FLOOR + 8, mz, PBB)                           # bracket holding the chain
        s.set(mx + sx, FLOOR + 9, mz, st.slab("deepslate_tile"))
        for dz, f in ((-1, "north"), (1, "south")):
            s.set(mx, FLOOR + 8, mz + dz, st.end_rod(f))
            s.set(mx, FLOOR + 9, mz + dz, st.trapdoor("iron", f, "top", open=True))
        s.set(mx - sx, FLOOR + 8, mz, st.trapdoor("iron", "west" if sx > 0 else "east", "top", open=True))
        s.set(mx - sx, FLOOR + 9, mz, st.end_rod("west" if sx > 0 else "east"))
        s.set(mx, FLOOR + 9, mz, GLASS)
        s.set(mx, FLOOR + 10, mz, st.slab("deepslate_tile"))
        s.set(mx, FLOOR + 11, mz, st.lightning_rod("up"))
    # ---------------------------------------------------------------- control booth (west)
    bx1, bx2, bz1, bz2 = 5, 11, 16, 23
    by = FLOOR + 1
    sh.box(s, bx1, by, bz1, bx2, by, bz2, PBB)                       # knee wall band (solid, will be hollowed)
    sh.box(s, bx1, by + 1, bz1, bx2, by + 2, bz2, GLASS)             # glass walls
    sh.box(s, bx1 + 1, by, bz1 + 1, bx2 - 1, by + 2, bz2 - 1, "air")
    for (x, z) in ((bx1, bz1), (bx2, bz1), (bx1, bz2), (bx2, bz2)):
        sh.box(s, x, by, z, x, by + 3, z, PBB)                       # corner posts
    sh.box(s, bx1, by + 3, bz1, bx2, by + 3, bz2, DT)                # roof
    sh.box_edge_stairs(s, bx1, by + 3, bz1, bx2, bz2, WALL, half="top")   # bevelled eave
    for (x, z) in ((bx1 - 1, bz1 - 1), (bx2 + 1, bz1 - 1), (bx1 - 1, bz2 + 1), (bx2 + 1, bz2 + 1)):
        s.set(x, by + 3, z, st.slab("polished_deepslate", "top"))
    for z in (19, 20):
        s.set(8, by + 3, z, LANT)                                    # ceiling lights
    for z in (17, 22):                                               # vents in the knee wall (east face)
        s.set(bx2, by, z, st.trapdoor("iron", "east", "bottom", open=True))
    # airlock doorway on the east face (open, 1 wide x 2 tall, framed) - iron_door[half=lower] is rejected by the validator
    sh.box(s, bx2, by, 20, bx2, by + 1, 20, "air")
    for z in (19, 21):
        sh.box(s, bx2, by, z, bx2, by + 2, z, PBB)
    s.set(bx2, by + 2, 20, PBB)
    s.set(bx2 + 1, by + 1, 19, st.trapdoor("iron", "east", "top", open=True))   # slid-open door panel
    # interior: console row on the west wall, seats, loot, lectern, sign
    for i, z in enumerate(range(bz1 + 1, bz2)):
        s.set(bx1 + 1, by, z, "minecraft:daylight_detector" if i % 2 == 0 else st.redstone_lamp(True))
    s.set(bx1 + 1, by, bz1 + 1, st.facing_block("minecraft:observer", "up"))
    s.set(bx1 + 1, by, bz2 - 1, st.facing_block("minecraft:observer", "up"))
    for z in (18, 21):
        s.set(bx1 + 2, by, z, st.stairs("polished_deepslate", "east"))
    s.add_chest(bx2 - 1, by, bz1 + 1, "west", "minecraft:chests/bastion_other")
    s.set(bx2 - 1, by, bz2 - 1, st.facing_block("minecraft:lectern", "west"))
    s.add_sign(bx1 + 2, by + 2, bz1 + 1, SIGN + "[facing=east]", ["TOUR PISTE 01", "vaisseau 1: OK", "alerte niv 2", "intrus: aucun"])
    s.set(bx2 + 1, by + 1, bz2, st.wall_banner("purple", "east"))
    # roof gear
    s.set(6, by + 4, 17, st.lightning_rod("up")); s.set(6, by + 5, 17, st.lightning_rod("up"))
    s.set(10, by + 4, 22, st.end_rod("up"))
    for z in (19, 20):
        s.set(6, by + 4, z, "minecraft:daylight_detector")
    s.set(9, by + 4, 17, st.trapdoor("iron", "east", "top", open=True))     # small dish panel
    # ---------------------------------------------------------------- fuel depot (east, north half: keeps the ship's starboard ramp clear)
    tx, ty = 31, FLOOR + 2
    sh.cylinder(s, tx, ty, 10, 1.0, 9, st.log("minecraft:polished_basalt", "z"), axis="z")  # tank z=10..19, plus-shaped section
    for z in (11, 14, 18):
        sh.cylinder(s, tx, ty, z, 1.0, 0, OXCUT, axis="z")                               # oxidized copper bands (teal)
    for z in (9, 20):
        s.set(tx, ty, z, OXC)                                                            # oxidized end caps
    for z in range(10, 20):                                          # cradle
        s.set(tx - 1, ty - 1, z, st.stairs("polished_deepslate", "east"))
        s.set(tx + 1, ty - 1, z, st.stairs("polished_deepslate", "west"))
    s.set(tx, ty + 2, 14, st.trapdoor("iron", "north", "bottom"))    # hatch on top
    s.set(tx, ty + 2, 18, st.lightning_rod("up"))                    # vent
    s.add_sign(tx, ty, 21, SIGN + "[facing=south]", ["CARBURANT", "NE PAS FUMER", "DANGER", ""])
    for z in (10, 14):                                               # pumps + hoses + nozzles (raw copper bodies)
        s.set(26, FLOOR + 1, z, "minecraft:cut_copper")
        s.set(26, FLOOR + 2, z, "minecraft:barrel[facing=up,open=false]")
        s.set(26, FLOOR + 3, z, st.trapdoor("iron", "north", "bottom"))
        s.set(26, FLOOR + 2, z - 1, "minecraft:lever[face=wall,facing=north,powered=false]")
        for x in range(27, 30):
            s.set(x, FLOOR + 2, z, st.chain("x"))
        s.set(25, FLOOR + 2, z, st.lightning_rod("west"))
    # crates + a loot barrel
    for (x, z) in ((28, 18), (29, 18), (28, 19), (29, 19)):
        s.set(x, FLOOR + 1, z, "minecraft:barrel[facing=up,open=false]")
    s.set(28, FLOOR + 2, 18, "minecraft:purple_shulker_box[facing=up]")
    s.add_chest(29, FLOOR + 2, 19, "west", "minecraft:chests/ancient_city", kind="barrel")
    s.set(27, FLOOR + 1, 20, "minecraft:magenta_shulker_box[facing=up]")
    # ground power unit near the H, cable on the floor to the ship position
    s.set(24, FLOOR + 1, 27, st.facing_block("minecraft:blast_furnace", "north"))
    s.set(25, FLOOR + 1, 27, PBB)
    s.set(25, FLOOR + 2, 27, st.trapdoor("iron", "north", "bottom"))
    s.set(24, FLOOR + 2, 27, st.lightning_rod("up"))
    for x in range(21, 24):
        s.set(x, FLOOR + 1, 27, st.chain("x"))
    s.set(26, FLOOR + 1, 27, "minecraft:lever[face=wall,facing=east,powered=true]")
    # banners behind the booth
    s.set(4, FLOOR + 2, 19, st.wall_banner("purple", "west"))
    s.set(4, FLOOR + 2, 20, st.wall_banner("purple", "west"))
    # cargo stack in the south-east quadrant (crates under a chain net) + a beacon post
    for (x, z) in ((28, 29), (29, 29), (28, 30), (29, 30)):
        s.set(x, FLOOR + 1, z, "minecraft:barrel[facing=up,open=false]")
    s.set(28, FLOOR + 2, 29, "minecraft:purple_shulker_box[facing=up]")
    s.set(29, FLOOR + 2, 30, NETH)
    s.set(29, FLOOR + 2, 29, st.chain("x")); s.set(28, FLOOR + 2, 30, st.chain("z"))
    s.set(30, FLOOR + 1, 28, st.chain("y")); s.set(30, FLOOR + 2, 28, st.chain("y"))
    s.set(30, FLOOR + 3, 28, st.lantern(soul=True, hanging=True))
    s.set(24, FLOOR + 1, 32, WALLB); s.set(24, FLOOR + 2, 32, WALLB)
    s.set(24, FLOOR + 3, 32, NEON); s.set(24, FLOOR + 4, 32, st.end_rod("up"))
    s.add_sign(15, FLOOR - 1, 37, SIGN + "[facing=west]", ["ZONE", "INTERDITE", "personnel", "autorise"])
    for (x, z) in ((3, 24), (36, 15)):                                # on the skirt under the lip
        s.set(x, G + 1, z, "minecraft:sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
        s.set(x, G, z, V["sculk"])
    # ---------------------------------------------------------------- crane (north-east)
    cx1, cz1 = 26, 5
    sh.box(s, cx1, FLOOR + 1, cz1, cx1 + 1, FLOOR + 1, cz1 + 1, NETH)
    sh.box(s, cx1, FLOOR + 2, cz1, cx1 + 1, FLOOR + 9, cz1 + 1, PBB)
    sh.box(s, cx1, FLOOR + 5, cz1, cx1 + 1, FLOOR + 5, cz1 + 1, CRY)
    for y in range(FLOOR + 2, FLOOR + 10, 2):                         # rungs / vents on the tower faces
        s.set(cx1 - 1, y, cz1, st.trapdoor("iron", "west", "top", open=True))
        s.set(cx1 + 2, y, cz1 + 1, st.trapdoor("iron", "east", "top", open=True))
    boom_y = FLOOR + 10
    for x in (cx1, cx1 + 1):                                          # lattice boom: wall chord + bars / slab top
        for z in range(3, 20):
            s.set(x, boom_y, z, WALLB)
            s.set(x, boom_y + 1, z, BARS if (z // 2) % 2 == 0 else st.slab("deepslate_tile"))
    sh.box(s, cx1, boom_y - 1, 3, cx1 + 1, boom_y - 1, 4, NETH)       # counterweight
    sh.box(s, cx1, boom_y + 1, 3, cx1 + 1, boom_y + 1, 4, NETH)
    for x in (cx1, cx1 + 1):                                          # boom tip lights
        s.set(x, boom_y, 20, NEON)
        s.set(x, boom_y + 1, 20, st.slab("deepslate_tile"))
    # operator cab (east side of the tower)
    sh.box(s, cx1 + 2, FLOOR + 6, cz1, cx1 + 2, FLOOR + 6, cz1 + 1, PD)
    sh.box(s, cx1 + 2, FLOOR + 7, cz1, cx1 + 2, FLOOR + 7, cz1 + 1, GLASS)
    sh.box(s, cx1 + 2, FLOOR + 8, cz1, cx1 + 2, FLOOR + 8, cz1 + 1, st.slab("deepslate_tile"))
    # trolley on the underside of the boom, hook chain down to a crate being set on the floor
    hz = 8
    for z in range(hz - 1, hz + 3):
        s.set(cx1, boom_y - 1, z, st.chain("z"))
    s.set(cx1, boom_y - 1, hz, NETH)                                  # trolley block
    for y in range(FLOOR + 3, boom_y - 1):
        s.set(cx1, y, hz, st.chain("y"))
    s.set(cx1, FLOOR + 2, hz, "minecraft:hopper[enabled=true,facing=down]")
    s.set(cx1, FLOOR + 1, hz, "minecraft:purple_shulker_box[facing=up]")
    s.add_sign(cx1 - 1, FLOOR + 3, cz1 + 1, SIGN + "[facing=west]", ["GRUE 2", "charge max 4t", "ne pas passer", "dessous"])
    # ---------------------------------------------------------------- textures
    sh.texturize(s, PD, MIX_DARK, seed=5, region=(0, FLOOR, 0, W - 1, FLOOR, L - 1))
    sh.texturize(s, DT, MIX_TILES, seed=6, region=(0, 0, 0, W - 1, G, L - 1))
    sh.texturize(s, PBB, MIX_BLACK, seed=7)
    # ---------------------------------------------------------------- weathering: snow drifts (skirt, rim, stair tops, roofs)

    def snow_on(cells, y, prob, layers=(1, 2), lean=0.0):
        """Snow layers as contiguous drifts (value noise), optionally piled toward the east (lean > 0)."""
        for x, z in cells:
            x, z = int(x), int(z)
            b = s.get(x, y, z)
            if not s.inside(x, y + 1, z) or not s.is_air(x, y + 1, z) or b == "minecraft:air" or "[" in b:
                continue
            if any(k in b for k in ("glass", "lantern", "sensor", "cluster", "sculk_catalyst")):
                continue
            n = sh.value_noise2(x, z, 21, 5.0) + lean * (x - C) / 17.0
            if n > 1.0 - prob:
                depth = layers[0] + int((layers[1] - layers[0] + 0.999) * min(1.0, (n - (1.0 - prob)) / max(prob, 0.01)))
                s.set(x, y + 1, z, st.snow_layer(max(1, min(8, depth))))
    snow_on(zip(*np.nonzero(oring(14.5, 17.5))), G, 0.42, (1, 4), lean=0.25)           # skirt drifts (leeward east)
    snow_on(zip(*np.nonzero(oring(14.5, 16.5))), FLOOR, 0.22, (1, 2), lean=0.2)        # floor rim
    snow_on([(x, z) for x in range(16, 24) for z in (3, 36)], FLOOR, 0.45)             # stair top steps
    snow_on([(x, z) for x in range(bx1, bx2 + 1) for z in range(bz1, bz2 + 1)], by + 3, 0.4, (1, 3))   # booth roof
    snow_on([(x, z) for x in (cx1, cx1 + 1) for z in (3, 4)], boom_y + 1, 0.8)          # counterweight
    snow_on([(x, z) for x in (cx1, cx1 + 1) for z in (cz1, cz1 + 1)], FLOOR + 9, 0.8)   # crane tower top
    return s.cropped(pad=1)


# =================================================================================================================
#  GUNSHIP
# =================================================================================================================
def build_ship():
    W, H, L, G = 24, 15, 34, 1
    s = Schematic(W, H, L, ground=G)
    CX = 11.5
    secs = [(1, CX, 6.5, 0.6, 0.5), (4, CX, 6.6, 2.0, 1.3), (9, CX, 6.9, 3.4, 2.4),
            (15, CX, 7.0, 4.2, 3.0), (22, CX, 7.0, 4.0, 2.9), (28, CX, 7.0, 3.0, 2.3)]
    hull = sh.loft(s, secs, PB, axis="z")
    inner = sh.loft_mask(s, secs, "z", shrink=1.0)
    zi = np.arange(L)[None, None, :]
    inner &= (zi >= 5) & (zi <= 26)
    yi = np.arange(H)[None, :, None]
    sh.fill_mask(s, inner & (yi >= 7), "air")                        # interior air y=7..9
    sh.fill_mask(s, inner & (yi <= 6), PD)                           # flat floor at y=6

    def shell(x, y, z):
        return s.inside(x, y, z) and hull[x, y, z] and not inner[x, y, z]

    # ---- cockpit: canopy on the upper nose framed by a polished deepslate line, magenta eyebrow behind it
    for z in range(3, 10):
        for x in range(9, 15):
            col = [y for y in range(7, 11) if shell(x, y, z)]
            for y in col:
                s.set(x, y, z, PD)
            if 4 <= z <= 8 and 10 <= x <= 13:
                for y in col:
                    s.set(x, y, z, TINT if x in (11, 12) and y < max(col) else GLASS)
            if z == 9 and 10 <= x <= 13 and col:
                s.set(x, max(col), z, NEON)                          # eyebrow strip over the canopy
    for z in (2, 3):                                                 # nose tip dark cone
        for x in (11, 12):
            for y in range(5, 9):
                if shell(x, y, z):
                    s.set(x, y, z, NETH)
    # ---- dorsal spine + glowing belt line + vents + cheek underglow
    for z in range(10, 27):
        col = [(x, y) for x in range(W) for y in range(H) if shell(x, y, z)]
        top = {}
        for x, y in col:
            top[x] = max(top.get(x, -1), y)
        for x, y in top.items():
            if abs(x - CX) <= 0.5 and 12 <= z <= 24:
                s.set(x, y, z, GLASS)                                # neon dorsal spine (lit by the bay end rods)
            elif abs(x - CX) <= 1.5:
                s.set(x, y, z, PD)
        xs_at7 = [x for x, y in col if y == 7]
        if xs_at7:
            for x in (min(xs_at7), max(xs_at7)):
                s.set(x, 7, z, GLASS)                                # continuous purple belt line
                ix = x + (1 if x < CX else -1)
                if s.inside(ix, 7, z):
                    s.set(ix, 7, z, LANT)                            # lantern behind the glass (ledge inside the bay)
        xs_at6 = [x for x, y in col if y == 6]
        if xs_at6:
            for x in (min(xs_at6), max(xs_at6)):
                s.set(x, 6, z, GLASS)
                ix = x + (1 if x < CX else -1)
                if s.inside(ix, 6, z) and inner[ix, 6, z]:
                    s.set(ix, 6, z, LANT)                            # floor-edge light strip inside
        if z % 3 == 0:
            xs_at8 = [x for x, y in col if y == 8]
            for x in (min(xs_at8), max(xs_at8)):
                ox = x + (-1 if x < CX else 1)
                if s.inside(ox, 8, z) and s.is_air(ox, 8, z):
                    s.set(ox, 8, z, st.trapdoor("iron", "west" if x < CX else "east", "top", open=True))  # vent panel
    # ---- keel underglow: purple glass along the bottom centreline, lanterns above (starts behind the nose gear)
    for z in range(10, 27):
        for x in (11, 12):
            ys = [y for y in range(3, 8) if shell(x, y, z)]
            if ys:
                s.set(x, ys[0], z, GLASS)
                if s.inside(x, ys[0] + 1, z) and not inner[x, ys[0] + 1, z] or (s.inside(x, ys[0] + 1, z) and inner[x, ys[0] + 1, z] and ys[0] + 1 <= 6):
                    s.set(x, ys[0] + 1, z, LANT)
    # ---- wings (high shoulder mount, forward swept) at y=9, slab bevel around, tip pods, cannons
    WY = 9
    def wing(sign):
        def X(dx):                                                   # mirror helper around CX
            return CX + sign * dx
        root_x, tip_x = X(3.5), X(11.0)
        pts = [(root_x, 27.5), (root_x, 17.0), (tip_x, 9.0), (tip_x, 13.0)]
        big = [(root_x, 28.3), (root_x, 16.0), (tip_x + sign * 0.9, 8.0), (tip_x + sign * 0.9, 14.0)]
        before = s.data.copy()
        sh.polygon_prism(s, big, WY, WY, st.slab("deepslate_tile"))
        sh.polygon_prism(s, pts, WY, WY, PD)
        # keep hull cells intact under the polygon
        m = hull[:, WY, :]
        s.data[:, WY, :][m] = before[:, WY, :][m]
        # thick root fairing (y=8) close to the hull
        fair = [(root_x, 26.0), (root_x, 18.0), (X(5.5), 16.0), (X(5.5), 22.0)]
        sh.polygon_prism(s, fair, WY - 1, WY - 1, st.slab("polished_deepslate", "top"))
        # leading-edge rib under the wing (1-wide strip along the leading edge)
        rib = [(root_x, 17.0), (tip_x, 9.0), (tip_x, 10.2), (root_x, 18.2)]
        sh.polygon_prism(s, rib, WY - 1, WY - 1, st.slab("polished_deepslate", "top"))
        s.data[:, WY - 1, :][hull[:, WY - 1, :]] = before[:, WY - 1, :][hull[:, WY - 1, :]]
        # energy conduit: purple glass line from the root to the tip
        for i in range(10):
            f = i / 9.0
            cx_ = root_x + (tip_x - root_x) * f - (0.5 if sign > 0 else -0.5)
            cz_ = 22.5 - 11.0 * f
            x, z = int(round(cx_)), int(round(cz_))
            if s.get(x, WY, z) == PD:
                s.set(x, WY, z, GLASS)
        # crying obsidian wing-root blocks (power couplings)
        rx_ = int(round(root_x - (0.5 if sign > 0 else -0.5)))
        for z in (18, 25):
            s.set(rx_, WY, z, CRY)
        # tip: find wing cells at the tip column
        tx = int(round(tip_x - (0.5 if sign > 0 else -0.5)))
        tx = min(max(tx, 0), W - 1)
        zs_tip = [z for z in range(L) if s.get(tx, WY, z) != "minecraft:air"]
        if zs_tip:
            z0, z1 = min(zs_tip), max(zs_tip)
            for z in range(z0, z1 + 1):
                s.set(tx, WY, z, NETH)
            s.set(tx, WY, z0, NEON)                                  # position light
            s.set(tx, WY, z1 + 1, st.slab("deepslate_tile"))
        # cannons: two lightning rods forward of the leading edge, on 2 columns
        for gx in (tx, tx - sign):
            zs_g = [z for z in range(L) if s.get(gx, WY, z) not in ("minecraft:air",) and "slab" not in s.get(gx, WY, z)]
            if zs_g:
                zl = min(zs_g)
                s.set(gx, WY, zl - 1, st.lightning_rod("north"))
                s.set(gx, WY, zl - 2, st.lightning_rod("north"))
        # trailing-edge flaps (iron trapdoors hinged on the wing edge)
        for fx in (tx - sign, tx - 2 * sign):
            zs_w = [z for z in range(L) if s.get(fx, WY, z) != "minecraft:air" and "slab" not in s.get(fx, WY, z)]
            if zs_w:
                zt = max(zs_w) + 1
                if s.inside(fx, WY, zt) and s.is_air(fx, WY, zt):
                    s.set(fx, WY, zt, st.trapdoor("iron", "south", "top", open=True))
        # hard-point pods under the wing (missile pods), two per wing, outboard of the engine
        for dx, plen in ((9.5, 3), (8.5, 4)):
            px = int(round(X(dx) - (0.5 if sign > 0 else -0.5)))
            zs_p = [z for z in range(L) if s.get(px, WY, z) != "minecraft:air"]
            if zs_p:
                zl = min(zs_p) + 1
                for z in range(zl, zl + plen):
                    s.set(px, WY - 1, z, st.log("minecraft:polished_basalt", "z"))
                s.set(px, WY - 1, zl - 1, st.lightning_rod("north"))
                s.set(px, WY - 1, zl + plen, NEON)
    wing(1)
    wing(-1)
    # ---- engine pods: 4x4 rounded section on the wing roots, z=17..31 (2 past the tail), 2x2 magenta core
    for ex in (5.5, 17.5):
        ey = 8.5
        xa, xb = int(ex - 1.5), int(ex + 1.5)                        # 4..7 / 16..19
        xi0, xi1 = int(ex - 0.5), int(ex + 0.5)                      # 5,6 / 17,18
        sh.elliptic_cylinder(s, ex, ey, 18, 1.5, 1.5, 12, PB, axis="z")   # body z=18..30
        for z in range(18, 31):
            for x in (xi0, xi1):
                s.set(x, 10, z, DT if (z + x) % 2 else PD)                     # top spine panels
            # bevel the 4 cut corners with stairs so the pod reads round
            s.set(xa, 10, z, st.stairs("polished_blackstone", "east", "bottom"))
            s.set(xb, 10, z, st.stairs("polished_blackstone", "west", "bottom"))
            s.set(xa, 7, z, st.stairs("polished_blackstone", "east", "top"))
            s.set(xb, 7, z, st.stairs("polished_blackstone", "west", "top"))
        for z in (21, 25):                                           # panel lines / vents on the flanks
            s.set(xa, 9, z, DT); s.set(xb, 9, z, DT)
        # intake face (z=17): netherite lip + 2x2 tinted glass
        for x in range(xa, xb + 1):
            for y in (8, 9):
                s.set(x, 8 if y == 8 else 9, 17, NETH)
        for x in (xi0, xi1):
            s.set(x, 10, 17, st.slab("polished_blackstone", "top"))
            s.set(x, 7, 17, st.slab("polished_blackstone"))
            for y in (8, 9):
                s.set(x, y, 17, TINT)
        # core: sea lanterns, hidden soul campfire, magenta 2x2 nozzle glow
        for x in (xi0, xi1):
            for y in (8, 9):
                s.set(x, y, 28, LANT)
                s.set(x, y, 29, LANT)
                s.set(x, y, 30, NEON)
        s.set(xi0, 8, 29, st.campfire(soul=True, facing="south"))    # idle blue smoke
        # nozzle lip (z=31): tapered ring of stairs/slabs, open centre
        s.set(xa, 8, 31, st.stairs("polished_blackstone", "east", "top"))
        s.set(xa, 9, 31, st.stairs("polished_blackstone", "east", "bottom"))
        s.set(xb, 8, 31, st.stairs("polished_blackstone", "west", "top"))
        s.set(xb, 9, 31, st.stairs("polished_blackstone", "west", "bottom"))
        for x in (xi0, xi1):
            s.set(x, 10, 31, st.slab("polished_blackstone", "top"))
            s.set(x, 7, 31, st.slab("polished_blackstone"))
        # pylon fill between pod and hull (make sure it is attached at y=8 too)
        px = 8 if ex < CX else 15
        for z in range(19, 26):
            if s.is_air(px, 8, z):
                s.set(px, 8, z, PD)
    # ---- twin canted fins (netherite leading-edge caps)
    for fx in (9, 14):
        s.set(fx, 10, 23, st.stairs("polished_blackstone", "south"))
        s.set(fx, 10, 24, NETH)
        sh.box(s, fx, 10, 25, fx, 10, 27, PB)
        s.set(fx, 11, 25, st.stairs("polished_blackstone", "south"))
        s.set(fx, 11, 26, NETH)
        s.set(fx, 11, 27, PB)
        s.set(fx, 12, 26, st.stairs("polished_blackstone", "south"))
        s.set(fx, 12, 27, NETH)
        s.set(fx, 13, 27, st.slab("polished_blackstone"))
        s.set(fx, 11, 28, NEON)
        s.set(fx, 12, 28, st.slab("deepslate_tile", "top"))
    # tail: magenta strip between the fins + antenna
    for x in range(10, 14):
        s.set(x, 10, 27, NEON if x in (11, 12) else DT)
    s.set(11, 11, 24, st.lightning_rod("up")); s.set(11, 12, 24, st.lightning_rod("up"))
    # ---- smooth the hull shoulders and belly with slabs (step bevels on the loft)
    tops, bots = {}, {}
    for x in range(W):
        for z in range(L):
            ys = [y for y in range(H) if hull[x, y, z]]
            if ys:
                tops[(x, z)] = max(ys); bots[(x, z)] = min(ys)
    for (x, z), yt in tops.items():
        inward = x + (1 if x < CX else -1)
        if tops.get((inward, z), -9) >= yt + 1 and s.is_air(x, yt + 1, z) and not s.is_air(x, yt, z):
            s.set(x, yt + 1, z, st.slab("polished_blackstone"))
    for (x, z), yb in bots.items():
        inward = x + (1 if x < CX else -1)
        if bots.get((inward, z), 99) <= yb - 1 and s.is_air(x, yb - 1, z) and yb - 1 >= 3:
            s.set(x, yb - 1, z, st.slab("polished_blackstone", "top"))
    # nose probe
    s.set(11, 6, 0, st.lightning_rod("north")); s.set(12, 6, 0, st.lightning_rod("north"))
    # ---- chin turret under the nose: netherite block, bevelled, twin rods
    for x in (11, 12):
        s.set(x, 4, 5, NETH)
        s.set(x, 4, 6, st.slab("polished_blackstone", "top"))
        for z in (3, 4):
            s.set(x, 4, z, st.lightning_rod("north"))
    # ---- landing gear (feet at y=2, struts up to the hull)
    for (gx, gz) in ((11, 9), (12, 9), (8, 21), (15, 21)):
        y0 = 3
        while y0 < H and s.is_air(gx, y0, gz):
            y0 += 1
        for y in range(3, y0):
            s.set(gx, y, gz, WALLB)
        s.set(gx, 2, gz, st.slab("polished_deepslate"))
    # ---- boarding hatch (starboard / east side, just behind the cockpit bulkhead) + ramp down to the pad
    HZ = (13, 14)
    HX = 15                                                          # shell column at z=13..14
    for z in HZ:
        for y in (7, 8):
            s.set(HX, y, z, "air")
        s.set(HX, 6, z, DT)                                          # threshold
        s.set(HX, 9, z, st.trapdoor("iron", "east", "top", open=True))   # raised hatch cover
        for i, x in enumerate(range(HX + 1, HX + 6)):                # stairs x=16..20, y=6..2
            y = 6 - i
            s.set(x, y, z, st.stairs(WALL, "west"))
            if y - 1 >= 2:
                s.set(x, y - 1, z, st.stairs(WALL, "east", "top"))
    for z in (HZ[0] - 1, HZ[1] + 1):                                 # ramp rails
        for i, x in enumerate(range(HX + 1, HX + 5)):
            s.set(x, 6 - i, z, WALLB)
    # ---- interior: cockpit
    for x in (11, 12):
        s.set(x, 7, 8, st.stairs("polished_deepslate", "north"))     # pilot seats
        s.set(x, 7, 6, "minecraft:daylight_detector")
    s.set(10, 7, 6, st.redstone_lamp(True)); s.set(13, 7, 6, st.redstone_lamp(True))
    s.set(10, 7, 7, st.facing_block("minecraft:observer", "up")); s.set(13, 7, 7, st.facing_block("minecraft:observer", "up"))
    # bulkhead between cockpit and bay with a 2-wide door opening
    for x in range(8, 16):
        for y in (7, 8, 9):
            if s.inside(x, y, 11) and inner[x, y, 11] and x not in (11, 12):
                s.set(x, y, 11, PBB)
    for x in (11, 12):
        s.set(x, 9, 11, PBB)
    # cargo bay furniture
    s.add_chest(9, 7, 24, "east", "minecraft:chests/bastion_other")
    s.add_chest(14, 7, 24, "west", "minecraft:chests/end_city_treasure")
    for (x, z) in ((9, 22), (14, 22), (14, 21)):
        s.set(x, 7, z, "minecraft:barrel[facing=up,open=false]")
    s.set(9, 7, 21, "minecraft:purple_shulker_box[facing=up]")
    s.set(14, 8, 22, "minecraft:magenta_shulker_box[facing=up]")
    for z in (16, 18):                                               # weapon rack on the port wall
        s.set(9, 8, z, st.lightning_rod("east"))
    s.set(13, 7, 17, "minecraft:anvil[facing=north]")
    s.set(9, 7, 14, st.facing_block("minecraft:blast_furnace", "east"))
    # ceiling lights
    for z in range(7, 27, 4):
        for x in (11, 12):
            if s.inside(x, 10, z) and not s.is_air(x, 10, z) and s.is_air(x, 9, z):
                s.set(x, 9, z, st.end_rod("down"))
    s.add_sign(14, 8, 16, SIGN + "[facing=west]", ["CORBEAU-7", "acces reserve", "equipage", "seulement"])
    s.set(14, 8, 20, st.wall_banner("purple", "west"))
    # ---- texture the hull
    sh.texturize(s, PB, MIX_HULL, seed=9)
    return s.cropped(pad=1)


def with_ground(s, g):
    """Return a copy whose ground index is g (adds empty layers under the build; nothing sits below the surface)."""
    lift = g - s.ground
    if lift <= 0:
        return s
    out = Schematic(s.w, s.h + lift, s.l, ground=g)
    out.paste(s, 0, lift, 0)
    out.block_entities = [dict(e, Pos=[e["Pos"][0], e["Pos"][1] + lift, e["Pos"][2]]) for e in s.block_entities]
    return out


def build():
    return {"city_landing_pad": build_pad(), "villain_ship": with_ground(build_ship(), 1)}

"""
Villain tech-city buildings (three schematics, ground = 1), same language as city_walls / city_spire:
polished deepslate plinth (y0..2) + basalt band (y3), blackstone-brick bodies textured with MIX_BLACK, purple /
magenta glass lit from behind, froglight / sea lantern lights, crying obsidian accents, sculk at the base.

  city_factory    40 x 30 x 30   processing plant: sawtooth hall, 3 chimneys (blue smoke), tanks, pipes, dock
  city_hab_block  26 x 36 x 26   Nakagin-style stack of habitat capsules around a split-level core + lift cage
  city_hangar     36 x 18 x 30   arched vehicle hangar with a parked ship and a mining crawler
"""
from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import VILLAIN, MIX_BLACK

G = 1
BASE = "minecraft:polished_deepslate"
TRIM = "minecraft:polished_basalt[axis=y]"
BODY = VILLAIN["wall"]                      # polished_blackstone_bricks, textured at the end
BODY_SMOOTH = "minecraft:polished_blackstone"
TILE = "minecraft:deepslate_tiles"
CHISEL = "minecraft:chiseled_polished_blackstone"
CRY = "minecraft:crying_obsidian"
GLASS = VILLAIN["glass"]                    # purple
GLASS2 = VILLAIN["glass_alt"]               # magenta
TINT = "minecraft:tinted_glass"
FROG = VILLAIN["light"]
LANT = "minecraft:sea_lantern"
RAIL = VILLAIN["railing"]
IRON = "minecraft:iron_block"
BARS = "minecraft:iron_bars"
PIPE = VILLAIN["pipe"]
PIPE_CUT = VILLAIN["pipe_cut"]
MAG = VILLAIN["road_line"]                  # magenta concrete
SIGN = "minecraft:warped_wall_sign"
ST_T = "deepslate_tile"
ST_B = "polished_blackstone_brick"
ST_D = "polished_deepslate"
OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}


# ------------------------------------------------------------------------------------------------ shared helpers
def vent(s, x, y, z, face):
    """Iron trapdoor lying flat against the wall behind it. `face` = direction the panel looks toward."""
    s.set(x, y, z, st.trapdoor("iron", face, "top", open=True))


def lamp_post(s, x, y, z):
    s.set(x, y, z, FROG)
    s.set(x, y + 1, z, st.trapdoor("iron", "north", "top", open=False))


def frame_light(s, x, y, z):
    s.set(x, y, z, LANT)
    s.set(x, y, z - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(x, y, z + 1, st.trapdoor("iron", "south", "bottom", open=True))
    s.set(x - 1, y, z, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(x + 1, y, z, st.trapdoor("iron", "east", "bottom", open=True))
    s.set(x, y + 1, z, st.trapdoor("iron", "north", "bottom", open=False))


def spike(s, x, y, z, n=2):
    parts = {3: ("base", "frustum", "tip"), 2: ("frustum", "tip"), 1: ("tip",)}[max(1, min(3, n))]
    for i, t in enumerate(parts):
        s.set(x, y + i, z, st.pointed_dripstone("up", t))


def sculk_patch(s, cells, seed=0):
    import random
    rng = random.Random(seed)
    for (x, y, z) in cells:
        s.set(x, y, z, "minecraft:sculk")
    x, y, z = cells[len(cells) // 2]
    s.set(x, y, z, "minecraft:sculk_catalyst")
    for (x, y, z) in cells:
        if s.is_air(x, y + 1, z) and rng.random() < 0.5:
            s.set(x, y + 1, z, "minecraft:sculk_vein[down=true]")
    x, y, z = cells[0]
    if s.is_air(x, y + 1, z) or "vein" in s.get(x, y + 1, z):
        s.set(x, y + 1, z, "minecraft:sculk_sensor")


def hang_lantern(s, x, y, z, n=2):
    """n chains hanging from the block above (x, y+1, z) with a soul lantern at the end."""
    for i in range(n):
        s.set(x, y - i, z, st.chain("y"))
    s.set(x, y - n, z, st.lantern(soul=True, hanging=True))


def bed(s, x, y, z, facing, color="purple"):
    """Two-block bed whose head is toward `facing`."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[facing]
    s.set(x, y, z, st.bed(color, facing, "foot"))
    s.set(x + dx, y, z + dz, st.bed(color, facing, "head"))


def finish(s, seed):
    sh.texturize(s, BODY, MIX_BLACK, seed=seed)
    sh.snow_cover(s, y_min=G + 4, prob=0.045, seed=seed, layers=(1, 1),
                  skip=["glass", "froglight", "sea_lantern", "sculk", "ladder", "basalt", "copper", "iron", "hopper",
                        "piston", "observer", "dispenser", "furnace", "bed", "barrel", "chest", "obsidian", "lamp"])
    return s


# ================================================================================================ 1. FACTORY
def build_factory():
    W, H, L = 40, 30, 30
    s = Schematic(W, H, L, ground=G)
    HX0, HX1, HZ0, HZ1 = 1, 28, 6, 25           # hall pier plane
    FLOOR, WALLTOP, ROOF = 2, 14, 15            # interior floor y2 (walk y3), roof slab y15
    PIERS_X = (1, 8, 15, 22, 28)
    PIERS_Z = (6, 12, 19, 25)

    # ---- foundation + plinth + basalt band (whole hall footprint, slightly wider)
    sh.box(s, HX0 - 1, 0, HZ0 - 1, HX1 + 1, 2, HZ1 + 1, BASE)
    sh.box(s, HX0 - 1, 3, HZ0 - 1, HX1 + 1, 3, HZ1 + 1, TRIM)
    sh.box(s, HX0, 3, HZ0, HX1, 3, HZ1, BASE)
    # ---- body: full box, then recess the panels between the piers by 1
    sh.box(s, HX0, 4, HZ0, HX1, WALLTOP, HZ1, BODY)
    for x in range(HX0 + 1, HX1):
        if x in PIERS_X:
            continue
        for z in (HZ0, HZ1):
            sh.box(s, x, 4, z, x, WALLTOP - 1, z, "air")
            s.set(x, 4, z, st.stairs(ST_T, OPP["north"] if z == HZ0 else OPP["south"]))
            s.set(x, WALLTOP, z, st.stairs(ST_T, OPP["north"] if z == HZ0 else OPP["south"], "top"))
    for z in range(HZ0 + 1, HZ1):
        if z in PIERS_Z:
            continue
        for x in (HX0, HX1):
            sh.box(s, x, 4, z, x, WALLTOP - 1, z, "air")
            s.set(x, 4, z, st.stairs(ST_T, OPP["west"] if x == HX0 else OPP["east"]))
            s.set(x, WALLTOP, z, st.stairs(ST_T, OPP["west"] if x == HX0 else OPP["east"], "top"))
    # interior void + floor
    sh.box(s, HX0 + 2, FLOOR + 1, HZ0 + 2, HX1 - 2, WALLTOP, HZ1 - 2, "air")
    sh.box(s, HX0 + 2, FLOOR, HZ0 + 2, HX1 - 2, FLOOR, HZ1 - 2, BASE)
    # neon line at y12 on every recessed panel (glass / lantern alternating), windows y8..9, vents, rivets
    for x in range(HX0 + 1, HX1):
        if x in PIERS_X:
            continue
        for zp in (HZ0 + 1, HZ1 - 1):
            s.set(x, 12, zp, LANT if x % 3 == 0 else GLASS)
            if (x - HX0) % 7 in (3, 4, 5):
                s.set(x, 8, zp, GLASS); s.set(x, 9, zp, GLASS)
    for z in range(HZ0 + 1, HZ1):
        if z in PIERS_Z:
            continue
        for xp in (HX0 + 1, HX1 - 1):
            s.set(xp, 12, z, LANT if z % 3 == 0 else GLASS)
    for (za, zb) in ((7, 11), (13, 18), (20, 24)):
        c = (za + zb) // 2
        for xp, face in ((HX0 + 1, "west"), (HX1 - 1, "east")):
            for z in range(c - 1, c + 2):
                s.set(xp, 8, z, GLASS); s.set(xp, 9, z, GLASS)
            vent(s, HX0 if face == "west" else HX1, 6, za, face)
            vent(s, HX0 if face == "west" else HX1, 6, zb, face)
            s.set(HX0 if face == "west" else HX1, 10, c, st.wall_banner("purple", face))
    for x in PIERS_X:
        for z in (HZ0, HZ1):
            s.set(x, 4, z, CRY)
            s.set(x, 7, z, CHISEL)
            s.set(x, 11, z, CHISEL)
        for zp, face in ((HZ0, "north"), (HZ1, "south")):
            zz = zp - 1 if face == "north" else zp + 1
            for dx in (-2, 2):
                if HX0 < x + dx < HX1 and x + dx not in PIERS_X:
                    vent(s, x + dx, 6, zp, face)
                    vent(s, x + dx, 5, zp, face)
    for z in PIERS_Z:
        for x in (HX0, HX1):
            s.set(x, 4, z, CRY)
            s.set(x, 7, z, CHISEL)
    # ---- sawtooth roof: 4 teeth of 7 along x (glass face looks west), basalt rim on the z edges
    sh.box(s, HX0 - 1, ROOF, HZ0 - 1, HX1 + 1, ROOF, HZ1 + 1, BASE)
    sh.box_edge_stairs(s, HX0 - 1, ROOF, HZ0 - 1, HX1 + 1, HZ1 + 1, ST_T, half="top")
    profile = [None, (18, "full"), (18, "slab"), (17, "full"), (17, "slab"), (16, "full"), (16, "slab")]
    for x in range(HX0, HX1 + 1):
        i = (x - HX0) % 7
        for z in range(HZ0 - 1, HZ1 + 2):
            edge = z in (HZ0 - 1, HZ1 + 1)
            mat = TRIM if edge else BODY
            if i == 0:
                if edge:
                    sh.box(s, x, ROOF + 1, z, x, 18, z, TRIM)
                else:
                    for y in (16, 17, 18):
                        s.set(x, y, z, GLASS)
                continue
            top, kind = profile[i]
            sh.box(s, x, ROOF + 1, z, x, top - 1, z, mat)
            if kind == "full":
                s.set(x, top, z, mat)
            else:
                s.set(x, top, z, st.slab("polished_blackstone" if edge else ST_D))
            if i == 1 and not edge:
                s.set(x, 16, z, LANT if z % 2 == 0 else BODY)       # lights behind the glass face
                s.set(x, 17, z, LANT if z % 2 == 1 else BODY)
    for x in (HX0 + 1, HX0 + 8, HX0 + 15, HX0 + 22):
        for z in (HZ0 - 1, HZ1 + 1):
            s.set(x, 19, z, st.end_rod("up"))
    # roof gear: radio mast + searchlight on the east tooth, vents
    frame_light(s, 26, 17, 8)
    for y in range(17, 24):
        s.set(26, y, 23, BARS)
    s.set(26, 24, 23, st.lightning_rod("up"))
    for z in (21, 25):
        s.set(26, 19, z, st.end_rod("up"))
    for x in (10, 17, 24):
        s.set(x, 17, 15, st.trapdoor("iron", "north", "bottom", open=False))

    # ---- chimneys (3) on the north side, each with a manifold pipe and blue smoke
    for cx in (5, 14, 23):
        cz = 3
        sh.cylinder(s, cx, 0, cz, 3.2, 2, BASE, axis="y")
        sh.cylinder(s, cx, 3, cz, 3.0, 0, TRIM, axis="y")
        sh.cylinder(s, cx, 4, cz, 2.8, 2, BODY, axis="y", r2=2.1)
        sh.cylinder(s, cx, 6, cz, 2.0, 19, BODY, axis="y")                 # y6..25
        for y in (9, 17, 24):
            sh.ring(s, cx, y, cz, 2.5, TRIM)
        sh.ring(s, cx, 26, cz, 2.5, TRIM)
        sh.cylinder(s, cx, 26, cz, 1.6, 0, TILE, axis="y")
        s.set(cx, 26, cz, st.campfire(soul=True))
        sh.ring(s, cx, 27, cz, 2.1, RAIL)
        for y in (12, 20):
            sh.ring_stairs(s, cx, y, cz, 2.6, ST_T, half="top", outward=True)
        # rivet / access hatch, ladder up the west side
        vent(s, cx - 3, 7, cz, "west")
        for y in range(8, 24, 4):                                          # rung hatches up the east side
            vent(s, cx + 3, y, cz, "east")
    sh.box(s, 3, 13, 5, 25, 13, 5, PIPE)                     # manifold along the hall north face
    for cx in (5, 14, 23):
        s.set(cx, 13, 5, PIPE_CUT)
        s.set(cx, 12, 5, PIPE_CUT)
        s.set(cx, 14, 5, PIPE_CUT)
    for x in (9, 19):
        s.set(x, 13, 5, PIPE_CUT)
        hang_lantern(s, x, 12, 5, 2)

    # ---- storage tanks (2) on the east side, purple glass band, pipes into the hall, hanging cables
    for cz in (10, 21):
        cx = 35
        sh.cylinder(s, cx, 0, cz, 3.6, 2, BASE, axis="y")
        sh.cylinder(s, cx, 3, cz, 3.3, 0, TRIM, axis="y")
        sh.cylinder(s, cx, 4, cz, 3.0, 10, "minecraft:polished_basalt[axis=y]", axis="y")    # y4..14
        sh.cylinder(s, cx, 6, cz, 3.0, 0, IRON, axis="y", hollow=True, thickness=1.0)
        sh.cylinder(s, cx, 13, cz, 3.0, 0, IRON, axis="y", hollow=True, thickness=1.0)
        sh.cylinder(s, cx, 9, cz, 3.0, 1, GLASS, axis="y", hollow=True, thickness=1.0)
        sh.cylinder(s, cx, 9, cz, 2.0, 1, LANT, axis="y")
        sh.ring_stairs(s, cx, 15, cz, 3.3, ST_T, half="bottom")
        sh.cylinder(s, cx, 15, cz, 2.2, 0, BODY, axis="y")
        s.set(cx, 16, cz, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(cx + 2, 16, cz, st.lightning_rod("up"))
        s.set(cx - 2, 16, cz, st.end_rod("up"))
        for y in range(5, 14, 2):
            vent(s, cx, y, cz + 4, "south")
        # feed pipe to the hall at y11 with a valve wheel, hanging chains from the roof lip
        sh.box(s, 29, 11, cz, 31, 11, cz, PIPE)
        s.set(32, 11, cz, PIPE_CUT)
        s.set(29, 11, cz, PIPE_CUT)
        s.set(30, 12, cz, st.button("polished_blackstone", "floor", "north"))
        for x in (30, 31):
            for y in (12, 13, 14):
                if s.is_air(x, y, cz + 1):
                    s.set(x, y, cz + 1, st.chain("y"))
        sh.box(s, 30, 11, cz + 1, 31, 11, cz + 1, PIPE)
    sh.box(s, 38, 6, 12, 38, 6, 19, PIPE)                    # cross pipe between the tanks
    s.set(38, 6, 12, PIPE_CUT); s.set(38, 6, 19, PIPE_CUT)
    s.set(38, 5, 15, "minecraft:cauldron"); s.set(38, 5, 16, "minecraft:cauldron")

    # ---- loading dock on the south: raised platform, half-lowered roll door, canopy, crates, conveyor
    sh.box(s, 3, 0, 26, 24, 2, 29, BASE)
    for x in range(3, 25):
        s.set(x, 2, 29, st.stairs(ST_T, "north"))
    sh.box(s, 8, 3, 24, 13, 7, 25, "air")                                  # dock door 6 wide, 5 high
    sh.box(s, 7, 3, 25, 7, 8, 25, BODY); sh.box(s, 14, 3, 25, 14, 8, 25, BODY)
    sh.box(s, 8, 8, 25, 13, 8, 25, TRIM)
    for x in range(8, 14):
        vent(s, x, 7, 26, "south")
        vent(s, x, 6, 26, "south")
    for x in (8, 13):
        s.set(x, 9, 25, FROG)
    sh.box(s, 5, 9, 26, 16, 9, 28, st.slab(ST_T, "top"))                    # canopy
    sh.box(s, 5, 9, 26, 16, 9, 26, TILE)
    for x in (7, 10, 13):
        s.set(x, 9, 27, FROG)
    for x in (5, 16):
        sh.box(s, x, 3, 28, x, 8, 28, RAIL)
        s.set(x, 9, 28, TILE)
    sh.box(s, 9, 2, 26, 12, 2, 29, MAG)                                    # dock markings
    for (x, z) in ((17, 27), (18, 27), (17, 28), (4, 27), (5, 27)):
        s.set(x, 3, z, "minecraft:barrel[facing=up,open=false]")
    s.set(18, 4, 27, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(4, 3, 28, "north", "minecraft:chests/bastion_other")
    s.set(19, 3, 28, "minecraft:purple_shulker_box[facing=up]")
    for (x, z) in ((6, 27), (7, 27), (6, 28)):
        s.set(x, 3, z, "minecraft:amethyst_block")
    s.set(6, 4, 27, "minecraft:amethyst_cluster[facing=up]")
    s.set(7, 4, 27, "minecraft:medium_amethyst_bud[facing=up]")
    s.set(21, 4, 27, "minecraft:amethyst_block")
    # conveyor: hopper line running from the dock through a hatch into the hall
    sh.box(s, 21, 3, 24, 21, 4, 25, "air")
    for z in range(20, 29):
        s.set(21, 3, z, st.facing_block("minecraft:hopper", "north"))
    for z in range(20, 29, 2):
        s.set(21, 4, z, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(20, 5, 25, FROG)
    s.add_sign(15, 5, 26, SIGN + "[facing=south]", ["QUAI B", "livraisons", "cristal brut", "uniquement"])
    # personnel door on the west side + step + sign
    sh.box(s, 1, 3, 15, 2, 5, 16, "air")
    s.set(0, 2, 15, st.stairs(ST_T, "east")); s.set(0, 2, 16, st.stairs(ST_T, "east"))
    s.set(1, 6, 15, FROG); s.set(1, 6, 16, FROG)
    s.add_sign(1, 5, 14, SIGN + "[facing=west]", ["USINE 3", "traitement", "acces", "personnel"])

    # ---- INTERIOR (x3..26, z8..23, floor y2, air y3..14)
    IX0, IX1, IZ0, IZ1 = 3, 26, 8, 23
    for x in range(IX0, IX1 + 1, 4):
        for z in (IZ0 + 1, IZ1 - 1):
            s.set(x, FLOOR, z, LANT)
    sh.box(s, IX0, FLOOR, 13, IX1, FLOOR, 13, MAG)                         # walkway lines
    sh.box(s, IX0, FLOOR, 18, IX1, FLOOR, 18, MAG)
    # furnace bank along the west wall with copper flues
    for z in range(IZ0 + 2, IZ1 - 1):
        s.set(IX0, 3, z, st.facing_block("minecraft:blast_furnace", "east") if z % 2 else "minecraft:smoker[facing=east,lit=true]")
        s.set(IX0, 4, z, IRON if z % 2 else TILE)
        if z % 3 == 0:
            for y in range(5, WALLTOP + 1):
                s.set(IX0, y, z, PIPE)
            s.set(IX0, 5, z, PIPE_CUT)
    # processing line: beam frame + pistons over a hopper belt
    for x in (7, 13, 19, 24):
        for z in (14, 17):
            sh.box(s, x, 3, z, x, 6, z, IRON)
    sh.box(s, 7, 7, 14, 24, 7, 17, TILE)
    for z in (14, 17):
        sh.box(s, 7, 7, z, 24, 7, z, st.log("minecraft:polished_basalt", "x"))
    for x in range(7, 25):
        s.set(x, 3, 15, st.facing_block("minecraft:hopper", "east"))
        s.set(x, 3, 16, st.facing_block("minecraft:dispenser", "up") if x % 2 else st.facing_block("minecraft:observer", "up"))
        if x % 2 == 0:
            s.set(x, 6, 15, "minecraft:piston[facing=down,extended=false]")
            s.set(x, 6, 16, st.facing_block("minecraft:observer", "down"))
        else:
            s.set(x, 6, 16, "minecraft:sticky_piston[facing=down,extended=false]")
            s.set(x, 6, 15, st.facing_block("minecraft:observer", "down"))
    for x in (10, 16, 22):
        s.set(x, 6, 14, GLASS2); s.set(x, 6, 17, GLASS2)
        s.set(x, 4, 14, st.redstone_lamp(True))
    s.set(8, 3, 18, "minecraft:cauldron"); s.set(9, 3, 18, "minecraft:cauldron")
    for x in (11, 12):
        s.set(x, 3, 19, "minecraft:amethyst_block")
    s.set(11, 4, 19, "minecraft:amethyst_cluster[facing=up]")
    # catwalk along the north interior wall (y9), ramp up from the floor, railings, froglight posts
    sh.box(s, IX0, 9, IZ0, IX1, 9, IZ0 + 1, BASE)
    for x in range(IX0, IX1 + 1):
        s.set(x, 9, IZ0 + 1, st.slab(ST_D, "top") if x % 2 else BASE)
        if x >= 12:
            s.set(x, 10, IZ0 + 1, RAIL)
    for x in range(IX0, IX1 + 1, 4):
        s.set(x, 10, IZ0, RAIL)
        s.set(x, 11, IZ0, FROG)
    for i in range(6):                                                     # ramp x4..9, y3..8 at z=10
        s.set(4 + i, 3 + i, IZ0 + 2, st.stairs(ST_D, "east"))
        if i % 2 == 1:
            sh.box(s, 4 + i, 3, IZ0 + 2, 4 + i, 2 + i, IZ0 + 2, RAIL)
    s.set(10, 9, IZ0 + 2, BASE); s.set(11, 9, IZ0 + 2, BASE)
    s.set(10, 10, IZ0 + 3, RAIL); s.set(11, 10, IZ0 + 3, RAIL)
    for i in range(6):
        s.set(4 + i, 4 + i, IZ0 + 3, RAIL)
    # control room corner (east), storage stacks, lights in the ceiling
    for z in (11, 12, 13):
        s.set(IX1, 3, z, st.facing_block("minecraft:observer", "west"))
        s.set(IX1, 4, z, "minecraft:daylight_detector")
    s.set(IX1, 5, 12, st.redstone_lamp(True))
    s.set(IX1 - 1, 3, 10, st.facing_block("minecraft:lectern", "west"))
    s.add_sign(IX1, 5, 11, SIGN + "[facing=west]", ["JOURNAL 31", "four 2 en panne", "rendement", "-40 pct"])
    s.add_sign(IX1, 5, 13, SIGN + "[facing=west]", ["ATTENTION", "poussiere de", "cristal", "masque oblig."])
    for (x, z) in ((25, 21), (26, 21), (26, 22), (25, 22), (24, 22)):
        s.set(x, 3, z, "minecraft:barrel[facing=up,open=false]")
    s.set(26, 4, 22, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(26, 3, 20, "west", "minecraft:chests/ancient_city")
    for x in range(5, 26, 5):
        for z in (11, 20):
            s.set(x, WALLTOP, z, LANT)
    for x in (4, 25):
        s.set(x, 5, IZ1, st.wall_banner("purple", "north"))
    # ---- ground integration: sculk creeping on the plinth, crying-obsidian bleed, a scatter of crates outside
    sculk_patch(s, [(0, 2, 8), (0, 2, 9), (0, 2, 10), (0, 3, 9), (1, 2, 5), (2, 2, 5), (3, 2, 5)], seed=1)
    sculk_patch(s, [(29, 2, 24), (29, 2, 25), (29, 2, 26), (30, 2, 25), (31, 2, 25)], seed=2)
    s.set(38, 2, 8, "minecraft:sculk"); s.set(38, 2, 7, "minecraft:sculk")
    lamp_post(s, 0, 4, 26); lamp_post(s, 29, 4, 26)
    return finish(s, 21)


# ================================================================================================ 2. HAB BLOCK
def capsule(s, level_y, face, c, glass_end=True, beds=True, seed=0):
    """Habitat capsule: 5x5 chamfered section, 8 long, attached to the core on `face`.
    level_y = y of the capsule's centre row; c = centre coordinate across the face (z for W/E, x for N/S)."""
    y = level_y
    # cells along the capsule: a = distance from the outer end (0 = end cap, 7 = at the core plane)
    if face == "west":
        cell = lambda a, u, v: (a, y + v, c + u)
        inward = "east"
    elif face == "east":
        cell = lambda a, u, v: (25 - a, y + v, c + u)
        inward = "west"
    elif face == "north":
        cell = lambda a, u, v: (c + u, y + v, a)
        inward = "south"
    else:
        cell = lambda a, u, v: (c + u, y + v, 25 - a)
        inward = "north"
    left, right = ("north", "south") if face in ("west", "east") else ("west", "east")
    for a in range(0, 10):                                       # a=8,9 pierce the core wall
        for u in range(-2, 3):
            for v in range(-2, 3):
                if abs(u) == 2 and abs(v) == 2:
                    continue
                x, yy, z = cell(a, u, v)
                if a >= 8:
                    if abs(u) <= 1 and abs(v) <= 1:
                        s.set(x, yy, z, "air")
                    continue
                if a == 0:
                    if abs(u) <= 1 and abs(v) <= 1:
                        s.set(x, yy, z, GLASS if glass_end else BODY)
                    elif abs(v) == 2:
                        s.set(x, yy, z, st.stairs(ST_T, inward, "top" if v == 2 else "bottom"))
                    else:
                        s.set(x, yy, z, st.stairs(ST_T, left if u == -2 else right, "bottom"))
                    continue
                if abs(u) <= 1 and abs(v) <= 1:
                    s.set(x, yy, z, "air")
                    continue
                if abs(v) == 2:
                    s.set(x, yy, z, BODY if abs(u) <= 1 else BODY)
                elif abs(u) == 2 and abs(v) == 1:
                    s.set(x, yy, z, st.stairs(ST_T, right if u == -2 else left, "top" if v == -1 else "bottom"))
                elif abs(u) == 2 and v == 0:
                    s.set(x, yy, z, GLASS if 1 <= a <= 6 and a % 3 != 0 else BODY_SMOOTH)   # neon window strip
                else:
                    s.set(x, yy, z, BODY)
    # bevelled end: replace the four edge cells of the end face by stairs
    for a in (1, 2):
        x, yy, z = cell(a, 0, 2)
        s.set(x, yy, z, st.slab(ST_D, "bottom") if a == 1 else BODY)
    # floor lights, ceiling light, furniture
    x, yy, z = cell(4, 0, 2)
    s.set(x, yy, z, FROG)
    x, yy, z = cell(2, 0, 2)
    s.set(x, yy, z, LANT)
    x, yy, z = cell(1, 0, -2)
    s.set(x, yy, z, LANT)
    if beds:
        for u in (-1, 1):
            x, yy, z = cell(2, u, -1)
            bed(s, x, yy, z, OPP[inward])
        for u in (-1, 1):
            x, yy, z = cell(6, u, -1)
            s.set(x, yy, z, "minecraft:barrel[facing=up,open=false]")
        x, yy, z = cell(5, 0, -1)
        s.set(x, yy, z, st.trapdoor("iron", inward, "bottom", open=False))
    # support beam stub under the capsule at the core side + bevel under the end
    for a in (5, 6, 7):
        x, yy, z = cell(a, 0, -3)
        s.set(x, yy, z, TILE)
    x, yy, z = cell(4, 0, -3)
    s.set(x, yy, z, st.stairs(ST_T, inward, "top"))
    if level_y == 5:                                              # ground level: feet down to the snow
        for a in (1, 6):
            for u in (-1, 0, 1):
                x, yy, z = cell(a, u, -3)
                s.set(x, yy, z, TILE)
    if not beds:                                                  # common room: table, lectern, loot
        x, yy, z = cell(3, 0, -1)
        s.set(x, yy, z, st.facing_block("minecraft:lectern", inward))
        x, yy, z = cell(5, -1, -1)
        s.add_chest(x, yy, z, left, "minecraft:chests/bastion_other")
        x, yy, z = cell(5, 1, -1)
        s.set(x, yy, z, st.stairs(ST_D, left))
    # rivets on the top ridge, a vent on the side
    for a in (2, 5):
        x, yy, z = cell(a, 0, 3)
        s.set(x, yy, z, st.trapdoor("iron", "north", "bottom", open=False))


def build_hab():
    W, H, L = 26, 36, 26
    s = Schematic(W, H, L, ground=G)
    CX0, CX1, CZ0, CZ1 = 8, 17, 8, 17           # core pier plane (10x10)
    TOP = 32                                     # roof deck y
    # foundation + plinth ring + basalt band
    sh.box(s, CX0 - 1, 0, CZ0 - 1, CX1 + 1, 2, CZ1 + 1, BASE)
    sh.box(s, CX0 - 1, 3, CZ0 - 1, CX1 + 1, 3, CZ1 + 1, TRIM)
    sh.box(s, CX0, 3, CZ0, CX1, 3, CZ1, BASE)
    sh.box(s, CX0, 4, CZ0, CX1, TOP, CZ1, BODY)
    # recess the 6 mid cells of every face by 1 (2x2 corner piers stay proud)
    for face in ("north", "south", "east", "west"):
        for a in range(2, 8):
            if face in ("north", "south"):
                zp = CZ0 if face == "north" else CZ1
                sh.box(s, CX0 + a, 4, zp, CX0 + a, TOP - 1, zp, "air")
                s.set(CX0 + a, 4, zp, st.stairs(ST_T, OPP[face]))
                s.set(CX0 + a, TOP, zp, st.stairs(ST_T, OPP[face], "top"))
            else:
                xp = CX0 if face == "west" else CX1
                sh.box(s, xp, 4, CZ0 + a, xp, TOP - 1, CZ0 + a, "air")
                s.set(xp, 4, CZ0 + a, st.stairs(ST_T, OPP[face]))
                s.set(xp, TOP, CZ0 + a, st.stairs(ST_T, OPP[face], "top"))
    # interior void x10..15, z10..15 from y3 (floor y2? no: floor y3 = plinth top) -> floor y3, air y4..31
    sh.box(s, 10, 4, 10, 15, TOP - 1, 15, "air")
    sh.box(s, 10, 3, 10, 15, 3, 15, BASE)
    # vertical neon strips in the free middle columns (z=12..13 / x=12..13) of every face
    for y in range(5, TOP - 1):
        for a in (12, 13):
            g = LANT if y % 4 == 0 else GLASS
            s.set(a, y, CZ0 + 1, g); s.set(a, y, CZ1 - 1, g)
            s.set(CX0 + 1, y, a, g); s.set(CX1 - 1, y, a, g)
    # crying obsidian + chisel bands on the piers
    for (x, z) in ((CX0, CZ0), (CX1, CZ0), (CX0, CZ1), (CX1, CZ1)):
        s.set(x, 4, z, CRY)
        for y in (9, 17, 25):
            s.set(x, y, z, CHISEL)
    # ---- capsules (Nakagin stagger). W/E levels centre y = 5,13,21,29 ; N/S levels 9,17,25
    W_LV = {5: (10, 15), 13: (10,), 21: (10, 15), 29: (15,)}
    E_LV = {5: (10, 15), 13: (15,), 21: (10, 15), 29: (10,)}
    N_LV = {9: (10, 15), 17: (15,), 25: (10, 15)}
    S_LV = {9: (10,), 17: (10,), 25: (10,)}
    k = 0
    for lv, cs in W_LV.items():
        for c in cs:
            capsule(s, lv, "west", c, beds=True, seed=k); k += 1
    for lv, cs in E_LV.items():
        for c in cs:
            capsule(s, lv, "east", c, beds=True, seed=k); k += 1
    for lv, cs in N_LV.items():
        for c in cs:
            capsule(s, lv, "north", c, beds=True, seed=k); k += 1
    for lv, cs in S_LV.items():
        for c in cs:
            capsule(s, lv, "south", c, beds=(lv != 9), seed=k); k += 1
    # ---- core interior: split-level floors every 4 blocks, one 4-step flight per level spiralling
    # N wall -> E wall -> S wall -> W wall (even flights sit on N/S walls, odd on E/W: they never cross a doorway)
    floors = list(range(3, TOP - 4, 4))          # 3,7,...,27
    for fy in floors:
        if fy > 3:
            sh.box(s, 10, fy, 10, 15, fy, 15, BASE)
        s.set(12, fy, 12, LANT); s.set(13, fy, 13, LANT)
    for n, fy in enumerate(floors[:-1]):
        k = n % 4
        if k == 0:
            cells = [(10 + i, 10) for i in range(4)]; facing = "east"; rail = [(10 + i, 11) for i in range(3)]
        elif k == 1:
            cells = [(15, 10 + i) for i in range(4)]; facing = "south"; rail = [(14, 10 + i) for i in range(3)]
        elif k == 2:
            cells = [(15 - i, 15) for i in range(4)]; facing = "west"; rail = [(15 - i, 14) for i in range(3)]
        else:
            cells = [(10, 15 - i) for i in range(4)]; facing = "north"; rail = [(11, 15 - i) for i in range(3)]
        for i, (x, z) in enumerate(cells):
            s.set(x, fy + 1 + i, z, st.stairs(ST_D, facing))
            if i < 3:
                s.set(x, fy + 4, z, "air")                              # hole in the floor above the flight
        for (x, z) in rail:
            s.set(x, fy + 5, z, RAIL)
    for y in range(28, TOP + 1):                                          # ladder + roof hatch from the top level
        s.set(15, y, 14, st.facing_block("minecraft:ladder", "west") if y < TOP else st.trapdoor("iron", "north", "top", open=True))
    # mess hall at the bottom level (floor y3): tables, benches, kitchen, lockers
    for x in (11, 13):
        s.set(x, 4, 12, st.slab(ST_D, "top")); s.set(x + 1, 4, 12, st.slab(ST_D, "top"))
    for x in (11, 12, 13, 14):
        s.set(x, 4, 11, st.stairs(ST_D, "south")); s.set(x, 4, 13, st.stairs(ST_D, "north"))
    s.set(14, 4, 15, st.facing_block("minecraft:blast_furnace", "north"))
    s.set(13, 4, 15, "minecraft:smoker[facing=north,lit=true]")
    s.set(12, 4, 15, "minecraft:cauldron")
    s.set(11, 4, 15, "minecraft:barrel[facing=up,open=false]")
    s.set(11, 5, 15, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(15, 4, 10, "west", "minecraft:chests/pillager_outpost")
    s.add_sign(15, 6, 12, SIGN + "[facing=west]", ["BLOC H-4", "repas 6h 12h 20h", "silence apres", "22h"])
    # ---- entrance on the south face under the lowest S capsule: opening, steps, canopy, path
    sh.box(s, 12, 4, CZ1 - 1, 13, 6, CZ1, "air")
    s.set(12, 3, CZ1, BASE); s.set(13, 3, CZ1, BASE)
    for x in (12, 13):
        s.set(x, 2, CZ1 + 1, st.stairs(ST_T, "north"))
        s.set(x, 7, CZ1, FROG)
    for x in (11, 14):
        s.set(x, 5, CZ1 + 1, st.trapdoor("iron", "west" if x == 11 else "east", "bottom", open=True))
    sh.box(s, 10, 6, CZ1 + 1, 15, 6, CZ1 + 3, st.slab(ST_T, "top"))         # canopy
    sh.box(s, 10, 6, CZ1 + 3, 15, 6, CZ1 + 3, TILE)
    s.set(12, 6, CZ1 + 2, FROG); s.set(13, 6, CZ1 + 2, FROG)
    for x in (10, 15):
        sh.box(s, x, 2, CZ1 + 3, x, 5, CZ1 + 3, RAIL)
    sh.box(s, 12, 1, CZ1 + 2, 13, 1, 25, MAG)
    sh.box(s, 11, 1, CZ1 + 2, 11, 1, 25, BASE); sh.box(s, 14, 1, CZ1 + 2, 14, 1, 25, BASE)
    s.add_sign(14, 5, CZ1, SIGN + "[facing=south]", ["BLOC H-4", "quartier", "troupes", "badge requis"])
    # ---- lift cage on the south-east: iron bars column with chains, motor housing, door slots at every level
    LX0, LX1, LZ0, LZ1 = 15, 17, CZ1 + 1, CZ1 + 3
    sh.box(s, LX0, 0, LZ0, LX1, 2, LZ1, BASE)
    sh.box(s, LX0, 3, LZ0, LX1, TOP - 1, LZ1, BARS)
    sh.box(s, LX0 + 1, 3, LZ0 + 1, LX1 - 1, TOP - 1, LZ1 - 1, "air")
    sh.box(s, LX0 + 1, 3, LZ0, LX1 - 1, TOP - 1, LZ0, "air")               # open toward the core wall
    for y in range(4, TOP - 1):
        s.set(LX0 + 1, y, LZ0 + 1, st.chain("y"))
    s.set(LX0 + 1, 3, LZ0 + 1, st.trapdoor("iron", "north", "bottom", open=False))   # cabin floor
    sh.box(s, LX0, TOP, LZ0, LX1, TOP + 1, LZ1, BODY)                       # motor housing
    s.set(LX0 + 1, TOP + 2, LZ0 + 1, TRIM)
    s.set(LX0 + 1, TOP + 3, LZ0 + 1, st.lightning_rod("up"))
    for y in (3, 7, 11, 15, 19, 23, 27):
        for (x, z) in ((16, CZ1), (16, CZ1 - 1), (15, CZ1 - 1)):
            s.set(x, y + 1, z, "air"); s.set(x, y + 2, z, "air")
        s.set(16, y + 3, CZ1, GLASS2)
        s.set(16, y, CZ1 - 1, BASE)
    for y in (3, 11, 19, 27):
        for x in (LX0, LX1):
            s.set(x, y, LZ1, TRIM)
    # ---- roof: deck, parapet, corner spikes, antennas, vents, beacon box
    sh.box(s, CX0, TOP, CZ0, CX1, TOP, CZ1, BASE)
    for x in range(CX0, CX1 + 1):
        s.set(x, TOP + 1, CZ0, RAIL); s.set(x, TOP + 1, CZ1, RAIL)
    for z in range(CZ0, CZ1 + 1):
        s.set(CX0, TOP + 1, z, RAIL); s.set(CX1, TOP + 1, z, RAIL)
    for (x, z) in ((CX0, CZ0), (CX1, CZ0), (CX0, CZ1), (CX1, CZ1)):
        s.set(x, TOP + 1, z, BODY)
        spike(s, x, TOP + 2, z, 2)
    sh.box(s, 12, TOP + 1, 12, 13, TOP + 2, 13, GLASS)
    sh.box(s, 12, TOP + 1, 12, 13, TOP + 1, 13, LANT)
    s.set(12, TOP + 3, 12, TRIM)
    s.set(12, TOP + 4, 12, st.lightning_rod("up"))
    for y in (TOP + 1, TOP + 2):
        s.set(10, y, 10, BARS)
    s.set(10, TOP + 3, 10, st.lightning_rod("up"))
    for (x, z) in ((15, 10), (10, 15)):
        s.set(x, TOP + 1, z, st.end_rod("up"))
    for (x, z) in ((14, 14), (15, 15)):
        s.set(x, TOP + 1, z, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(14, TOP + 1, 11, st.log("minecraft:polished_basalt", "y"))
    s.set(14, TOP + 2, 11, "minecraft:cauldron")
    for (x, z, f) in ((12, CZ0, "north"), (13, CZ0, "north"), (CX0, 12, "west"), (CX0, 13, "west")):
        s.set(x, 31, z, st.wall_banner("purple", f)) if s.is_air(x, 31, z) else None
    s.set(LX0 + 1, TOP + 1, LZ1 + 1, st.wall_banner("purple", "south"))
    # ---- ground: sculk at the plinth, lamp posts, crystal shards
    sculk_patch(s, [(7, 2, 10), (7, 2, 11), (7, 2, 12), (7, 3, 11), (8, 2, 7), (9, 2, 7)], seed=3)
    sculk_patch(s, [(18, 2, 14), (18, 2, 15), (18, 2, 16), (17, 2, 18)], seed=4)
    lamp_post(s, 9, 2, 21); lamp_post(s, 17, 2, 25)
    return finish(s, 22)


# ================================================================================================ 3. HANGAR
def build_hangar():
    W, H, L = 36, 18, 30
    s = Schematic(W, H, L, ground=G)
    CY, CZ, RY, RZ = 4, 14.5, 11, 14.5
    import numpy as np
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]

    def ell(ry, rz):
        m = (((ys - CY) / (ry + 0.5)) ** 2 + ((zs - CZ) / (rz + 0.5)) ** 2 <= 1.0) & (ys >= CY)
        return np.broadcast_to(m, (s.w, s.h, s.l)).copy()

    outer = ell(RY, RZ)
    inner = ell(RY - 2, RZ - 2)
    # foundation + floor
    sh.box(s, 0, 0, 0, W - 1, 1, L - 1, BASE)
    # walls below the spring line (y2..4) 2 thick, arch shell above
    sh.box(s, 0, 2, 0, W - 1, CY, 1, BODY); sh.box(s, 0, 2, L - 2, W - 1, CY, L - 1, BODY)
    sh.box(s, 0, 2, 0, W - 1, 2, 0, BASE); sh.box(s, 0, 2, L - 1, W - 1, 2, L - 1, BASE)
    sh.box(s, 0, 3, 0, W - 1, 3, 0, TRIM); sh.box(s, 0, 3, L - 1, W - 1, 3, L - 1, TRIM)
    shell = outer & ~inner
    s.data[shell] = s.pid(BODY)
    # end caps (2 thick) + interior void
    for x in (0, 1, W - 2, W - 1):
        col = outer[0, :, :]
        for y in range(2, s.h):
            for z in range(s.l):
                if col[y, z]:
                    s.set(x, y, z, BODY)
    void = inner.copy()
    void[:2, :, :] = False; void[W - 2:, :, :] = False
    s.data[void] = 0
    sh.box(s, 2, 2, 2, W - 3, CY, L - 3, "air")
    # ribs: proud ring every 6 blocks, dark tile rib inside, basalt outside; crying obsidian at the feet
    rib = ell(RY + 1, RZ + 1) & ~outer
    for x in (3, 9, 15, 21, 27, 33):
        s.data[x, :, :][rib[0]] = s.pid(TRIM)
        for z in (0, L - 1):
            s.set(x, 2, z, BASE); s.set(x, 3, z, TRIM); s.set(x, 4, z, CRY)
            s.set(x, 2, z - 1 if z else 1, TRIM)
        sh.box(s, x, 5, 0, x, 5, 0, TILE); sh.box(s, x, 5, L - 1, x, 5, L - 1, TILE)
    # ridge line + skylight strips between the ribs (glass on top, lanterns underneath)
    for x in range(2, W - 2):
        if x in (3, 9, 15, 21, 27, 33):
            sh.box(s, x, 16, 13, x, 16, 16, TRIM)
            continue
        for z in (13, 14, 15, 16):
            s.set(x, 15, z, GLASS)
            s.set(x, 14, z, LANT if (x + z) % 2 == 0 else BODY)
        s.set(x, 15, 12, st.slab(ST_D, "bottom")); s.set(x, 15, 17, st.slab(ST_D, "bottom"))
    for x in (9, 21):
        s.set(x, 17, 14, st.end_rod("up")); s.set(x, 17, 15, st.end_rod("up"))
    s.set(30, 16, 14, BARS); s.set(30, 17, 14, st.lightning_rod("up"))
    s.set(30, 16, 15, BARS); s.set(30, 16, 16, st.end_rod("east"))
    for x in (6, 12, 18, 24, 30):                                          # access panels on the low walls
        vent(s, x, 4, 0, "north"); vent(s, x + 1, 4, 0, "north")
        vent(s, x, 4, L - 1, "south"); vent(s, x + 1, 4, L - 1, "south")
    # neon line + vents along the low walls, outside
    for x in range(2, W - 2):
        if x in (3, 9, 15, 21, 27, 33):
            continue
        for z in (0, L - 1):
            s.set(x, 6, z, "air")
            s.set(x, 6, z + 1 if z == 0 else z - 1, LANT if x % 3 == 0 else GLASS)
            s.set(x, 5, z, st.stairs(ST_T, "south" if z == 0 else "north", "top"))
    # ---- west end: big door (z 8..21, y2..9), frame, half-lowered roll door, bars, lights
    sh.box(s, 0, 2, 8, 1, 9, 21, "air")
    for z in range(7, 23):
        s.set(0, 10, z, TRIM)
    for y in range(2, 11):
        s.set(0, y, 7, TRIM); s.set(0, y, 22, TRIM)
    for z in range(8, 22):
        s.set(1, 9, z, BARS)
        s.set(1, 8, z, st.trapdoor("iron", "east", "bottom", open=True))
        s.set(1, 7, z, st.trapdoor("iron", "east", "bottom", open=True))
        if z % 3 == 1:
            s.set(2, 1, z, LANT)
    s.set(0, 10, 8, FROG); s.set(0, 10, 21, FROG); s.set(0, 10, 14, FROG); s.set(0, 10, 15, FROG)
    s.set(0, 5, 7, CRY); s.set(0, 5, 22, CRY)
    s.add_sign(0, 6, 6, SIGN + "[facing=west]", ["HANGAR 2", "vehicules", "porte 3", "pas de feu"])
    lamp_post(s, 0, 2, 4); lamp_post(s, 0, 2, 25)
    # ---- east end: purple window band, vents, hatch
    for z in range(10, 20):
        for y in (6, 7, 8):
            s.set(W - 1, y, z, GLASS if z % 4 != 1 else LANT)
    for z in (4, 6, 23, 25):
        s.set(W - 1, 5, z, "air"); s.set(W - 2, 5, z, TINT)
        s.set(W - 1, 5, z, BARS)
    sh.box(s, W - 2, 2, 13, W - 1, 4, 16, "air")                            # rear personnel door
    s.set(W - 1, 5, 14, FROG); s.set(W - 1, 5, 15, FROG)
    # ---- floor markings: bays, centre line, threshold
    sh.box(s, 2, 1, 14, W - 3, 1, 15, TILE)
    for x in range(3, W - 3, 2):
        s.set(x, 1, 14, MAG); s.set(x, 1, 15, MAG)
    for (z0, z1) in ((3, 11), (18, 26)):
        sh.outline_top(s, 4, 1, z0, 22, z1, MAG)
    # ---- crane rail along the ridge with a trolley lifting a crate + overhead froglights
    sh.box(s, 3, 13, 14, W - 4, 13, 15, st.log("minecraft:polished_basalt", "x"))
    for x in range(6, W - 4, 6):
        s.set(x, 13, 14, FROG); s.set(x, 13, 15, FROG)
    s.set(17, 12, 14, IRON); s.set(17, 12, 15, IRON)
    for y in (11, 10, 9):
        s.set(17, y, 14, st.chain("y"))
    s.set(17, 8, 14, "minecraft:barrel[facing=up,open=false]")
    # ---- parked ship (bay north): lofted dark hull, magenta cockpit, fins, twin engines, skids
    secs = [(5, 4, 7, 0.6, 1.0), (8, 4, 7, 1.4, 2.4), (12, 4, 7, 1.9, 3.3), (16, 4, 7, 1.8, 3.1), (19, 4, 7, 1.2, 2.2)]
    sh.loft(s, secs, BODY_SMOOTH, axis="x")
    sh.box(s, 8, 5, 6, 10, 6, 8, GLASS2)
    sh.box(s, 8, 5, 7, 10, 5, 7, LANT)
    for x in (11, 12):
        s.set(x, 6, 7, TILE)
    for x in range(13, 18):
        s.set(x, 4, 11, st.slab(ST_D, "top")); s.set(x, 4, 3, st.slab(ST_D, "top"))
    for x in range(14, 17):
        s.set(x, 4, 12, st.slab(ST_D, "bottom")); s.set(x, 4, 2, st.slab(ST_D, "bottom"))
    s.set(19, 6, 7, st.stairs(ST_T, "east")); s.set(19, 7, 7, st.stairs(ST_T, "east"))
    for ez in (4, 10):
        sh.cylinder(s, 15, 4, ez, 1.0, 5, TILE, axis="x")
        sh.ring(s, 21, 4, ez, 1.0, IRON, axis="x")
        s.set(21, 4, ez, "minecraft:cyan_stained_glass")
        s.set(20, 4, ez, LANT)
    for z in (4, 10):
        sh.box(s, 9, 2, z, 15, 2, z, st.log("minecraft:polished_basalt", "x"))
        s.set(8, 2, z, st.stairs(ST_T, "west")); s.set(16, 2, z, st.stairs(ST_T, "east"))
    for x in (7, 11, 15):
        s.set(x, 6 if x > 7 else 5, 7, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(9, 3, 7, IRON)   # lowered ramp under the cockpit
    # ---- mining crawler (bay south): tracks, body, cab, drill head, exhaust
    sh.box(s, 8, 2, 19, 15, 2, 19, st.log("minecraft:polished_basalt", "x"))
    sh.box(s, 8, 2, 25, 15, 2, 25, st.log("minecraft:polished_basalt", "x"))
    for z in (19, 25):
        sh.box(s, 8, 3, z, 15, 3, z, TILE)
        s.set(7, 2, z, st.stairs(ST_T, "west")); s.set(16, 2, z, st.stairs(ST_T, "east"))
        s.set(7, 3, z, st.stairs(ST_T, "west", "top")); s.set(16, 3, z, st.stairs(ST_T, "east", "top"))
    sh.box(s, 8, 3, 20, 15, 4, 24, BODY)
    sh.box(s, 9, 5, 21, 14, 5, 23, BODY)
    sh.box(s, 9, 6, 21, 10, 6, 23, GLASS2)
    sh.box(s, 8, 5, 21, 8, 6, 23, GLASS2)
    s.set(9, 5, 22, LANT)
    for x in (12, 14):
        s.set(x, 6, 22, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(15, 5, 21, PIPE); s.set(15, 6, 21, PIPE_CUT)
    s.set(15, 5, 23, PIPE); s.set(15, 6, 23, PIPE_CUT)
    sh.cylinder(s, 7, 4, 22, 1.4, -3, IRON, axis="x", r2=0.3)              # drill x7..4
    s.set(4, 4, 22, IRON); s.set(3, 4, 22, "minecraft:lightning_rod[facing=west]")
    for z in (20, 24):
        s.set(11, 5, z, "minecraft:amethyst_block")
    s.set(13, 5, 20, "minecraft:barrel[facing=up,open=false]")
    # ---- workshop along the north wall, fuel tanks east, lockers south-east
    bench = [("minecraft:smithing_table", None), ("minecraft:anvil[facing=east]", None), ("minecraft:grindstone[face=floor,facing=north]", None),
             ("minecraft:stonecutter[facing=south]", None), ("minecraft:cauldron", None), ("minecraft:barrel[facing=up,open=false]", None),
             ("minecraft:crafting_table", None), ("minecraft:blast_furnace[facing=south,lit=true]", None)]
    for i, (b, _) in enumerate(bench):
        s.set(22 + i, 2, 3, b)
    sh.box(s, 22, 1, 3, 29, 1, 3, BASE)
    for x in (23, 26, 29):
        s.set(x, 4, 2, st.chain("y")); s.set(x, 3, 2, st.lantern(soul=True, hanging=True))
    for cz in (5, 24):                                                      # fuel tanks (2 drums)
        cx = 31
        sh.cylinder(s, cx, 2, cz, 1.5, 4, "minecraft:polished_basalt[axis=y]", axis="y")
        sh.ring(s, cx, 4, cz, 1.5, GLASS)
        s.set(cx, 4, cz, LANT)
        sh.ring(s, cx, 6, cz, 1.5, IRON)
        s.set(cx, 7, cz, PIPE_CUT)
        s.set(cx + 2, 2, cz, PIPE_CUT)
        sh.box(s, cx + 2, 3, cz, cx + 2, 5, cz, PIPE)
        s.set(cx + 2, 6, cz, PIPE_CUT)
        s.set(cx, 3, cz - 2 if cz < 10 else cz + 2, st.button("polished_blackstone", "wall", "north" if cz < 10 else "south"))
    for (x, z) in ((25, 26), (26, 26), (27, 26), (26, 27)):
        s.set(x, 2, z, "minecraft:barrel[facing=up,open=false]")
    s.set(26, 3, 26, "minecraft:barrel[facing=up,open=false]")
    s.add_chest(28, 2, 27, "north", "minecraft:chests/bastion_other")
    s.set(24, 2, 27, "minecraft:purple_shulker_box[facing=up]")
    s.add_sign(30, 4, 28, SIGN + "[facing=north]", ["JOURNAL 8", "vaisseau 2", "moteur bab.", "a changer"])
    s.set(20, 5, 1, st.wall_banner("purple", "south")); s.set(30, 5, 1, st.wall_banner("purple", "south"))
    # ---- outside: sculk, scattered crates by the door, lamp posts
    sculk_patch(s, [(1, 2, 1), (2, 2, 1), (3, 2, 1), (2, 3, 1)], seed=5)
    sculk_patch(s, [(33, 2, 28), (34, 2, 28), (33, 3, 28)], seed=6)
    return finish(s, 23)


def build():
    return {
        "city_factory": build_factory().cropped(pad=1),
        "city_hab_block": build_hab().cropped(pad=1),
        "city_hangar": build_hangar().cropped(pad=1),
    }
